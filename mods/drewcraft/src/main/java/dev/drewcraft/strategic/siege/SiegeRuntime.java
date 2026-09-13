package dev.drewcraft.strategic.siege;

import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.encounter.StrategicEncounter;
import dev.drewcraft.strategic.encounter.StrategicEncounterState;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicPosition;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.pathfinder.Path;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * BP6 tactical siege runtime. It only inspects already-materialized encounters in loaded chunks.
 * Vanilla navigation is always attempted first. The local breach planner is invoked only after
 * repeated path failures and its result is cached by encounter + local-grid fingerprint.
 */
public final class SiegeRuntime {
    private static final Map<UUID, EncounterState> STATES = new HashMap<>();
    private static long nextDueGameTime = Long.MIN_VALUE;
    private static long lastObservedGameTime = Long.MIN_VALUE;
    private static volatile CycleStats lastStats = CycleStats.empty();

    private SiegeRuntime() { }

    public static void onServerTick(ServerTickEvent.Post event) {
        if (!DrewCraftConfig.STRATEGIC_KERNEL.get() || !DrewCraftConfig.STRATEGIC_SIEGE.get()) return;
        MinecraftServer server = event.getServer();
        long now = server.overworld().getGameTime();
        if (lastObservedGameTime != Long.MIN_VALUE && now < lastObservedGameTime) {
            nextDueGameTime = Long.MIN_VALUE;
            STATES.clear();
        }
        lastObservedGameTime = now;
        if (nextDueGameTime != Long.MIN_VALUE && now < nextDueGameTime) return;
        nextDueGameTime = now + DrewCraftConfig.STRATEGIC_SIEGE_INTERVAL_TICKS.get();
        lastStats = runCycle(server, DrewCraftSavedData.get(server), now);
    }

    static CycleStats runCycle(MinecraftServer server, DrewCraftSavedData data, long gameTime) {
        long started = System.nanoTime();
        int maxEncounters = DrewCraftConfig.STRATEGIC_SIEGE_MAX_ENCOUNTERS_PER_CYCLE.get();
        int processed = 0;
        int eligible = 0;
        int normalPathSuccess = 0;
        int blocked = 0;
        int plans = 0;
        int cacheHits = 0;
        int breaches = 0;
        Set<UUID> live = new HashSet<>();

        for (StrategicEncounter encounter : data.strategicEncounters()) {
            if (processed >= maxEncounters) break;
            if (encounter.state() != StrategicEncounterState.MATERIALIZED) continue;
            live.add(encounter.encounterId());
            StrategicGroup group = data.strategicGroup(encounter.groupId()).orElse(null);
            if (group == null || !SiegeRolePolicy.groupMaySiege(group.groupType())) continue;
            ServerLevel level = levelFor(server, group.position().dimension());
            if (level == null) continue;
            Breaker breaker = chooseBreaker(level, encounter);
            if (breaker == null) continue;
            processed++;
            eligible++;

            BlockPos center = breaker.mob().blockPosition();
            if (!level.hasChunkAt(center)) continue;
            BlockPos localGoal = projectLocalGoal(center, group.mission().target(), DrewCraftConfig.STRATEGIC_SIEGE_RADIUS_BLOCKS.get());
            if (!level.hasChunkAt(localGoal)) continue;

            EncounterState state = STATES.computeIfAbsent(encounter.encounterId(), ignored -> new EncounterState());
            Path normalPath = breaker.mob().getNavigation().createPath(localGoal, 1);
            if (normalPath != null) {
                normalPathSuccess++;
                state.resetBlocked();
                breaker.mob().getNavigation().moveTo(normalPath, 1.0);
                continue;
            }

            blocked++;
            state.blockedChecks++;
            if (state.blockedChecks < DrewCraftConfig.STRATEGIC_SIEGE_BLOCKED_CHECKS.get()) continue;

            SiegeWorldSnapshot snapshot = SiegeWorldSnapshot.capture(
                    level, center, localGoal, DrewCraftConfig.STRATEGIC_SIEGE_RADIUS_BLOCKS.get()
            );
            long fingerprint = snapshot.grid().fingerprint();
            SiegePlan plan;
            if (state.cachedPlan != null && state.cachedFingerprint == fingerprint) {
                plan = state.cachedPlan;
                cacheHits++;
            } else {
                plan = BoundedSiegePlanner.plan(
                        snapshot.grid(),
                        DrewCraftConfig.STRATEGIC_SIEGE_MAX_EXPANDED_NODES.get(),
                        DrewCraftConfig.STRATEGIC_SIEGE_MAX_BREACH_BLOCKS.get()
                );
                plans++;
                state.cachedPlan = plan;
                state.cachedFingerprint = fingerprint;
                state.nextBreachIndex = 0;
            }

            if (plan.status() == SiegePlan.Status.OPEN_ROUTE) {
                // Conservative false-negative handling: if the local geometry is open, never break.
                state.resetBlocked();
                BlockPos goal = snapshot.worldPoint(snapshot.grid().goalX(), snapshot.grid().goalZ());
                breaker.mob().getNavigation().moveTo(goal.getX() + 0.5, goal.getY(), goal.getZ() + 0.5, 1.0);
                continue;
            }
            if (!plan.requiresBreaching() || state.nextBreachIndex >= plan.breaches().size()) continue;

            SiegePlan.BreachStep step = plan.breaches().get(state.nextBreachIndex);
            BlockPos breachPos = snapshot.blockerFor(step.x(), step.z());
            if (breachPos == null) {
                state.nextBreachIndex++;
                continue;
            }
            SiegeCell current = SiegeWorldSnapshot.classifyBlock(level, breachPos);
            if (current.kind() == SiegeCellKind.OPEN) {
                state.nextBreachIndex++;
                continue;
            }
            if (!current.kind().breachable()) {
                state.invalidatePlan();
                continue;
            }

            BlockPos approach = precedingWorldPoint(plan, snapshot, step);
            breaker.mob().getNavigation().moveTo(
                    approach.getX() + 0.5, approach.getY(), approach.getZ() + 0.5, 1.0
            );
            if (gameTime < state.nextBreakGameTime) continue;
            if (breaker.mob().distanceToSqr(
                    breachPos.getX() + 0.5, breachPos.getY() + 0.5, breachPos.getZ() + 0.5
            ) > 20.25) continue;

            // Re-check the exact block immediately before destruction; tags/block entities may have changed.
            current = SiegeWorldSnapshot.classifyBlock(level, breachPos);
            if (!current.kind().breachable()) {
                state.invalidatePlan();
                continue;
            }
            if (level.destroyBlock(breachPos, false)) {
                breaches++;
                state.nextBreakGameTime = gameTime + DrewCraftConfig.STRATEGIC_SIEGE_BREAK_COOLDOWN_TICKS.get();
                state.invalidatePlan(); // world changed; next cycle must re-snapshot rather than chain-grief.
            }
        }

        STATES.keySet().removeIf(id -> !live.contains(id));
        return new CycleStats(processed, eligible, normalPathSuccess, blocked, plans, cacheHits, breaches,
                (System.nanoTime() - started) / 1_000_000.0);
    }

    private static Breaker chooseBreaker(ServerLevel level, StrategicEncounter encounter) {
        for (Map.Entry<UUID, String> entry : encounter.activeEntityTypes().entrySet()) {
            if (!SiegeRolePolicy.entityMayBreach(entry.getValue())) continue;
            Entity entity = level.getEntity(entry.getKey());
            if (entity instanceof Mob mob && mob.isAlive()) return new Breaker(mob, entry.getValue());
        }
        return null;
    }

    private static BlockPos projectLocalGoal(BlockPos start, StrategicPosition target, int radius) {
        double dx = target.x() - (start.getX() + 0.5);
        double dz = target.z() - (start.getZ() + 0.5);
        double length = Math.hypot(dx, dz);
        if (length < 1.0e-6) return start;
        double distance = Math.min(radius - 1.0, length);
        int x = start.getX() + (int) Math.round(dx / length * distance);
        int z = start.getZ() + (int) Math.round(dz / length * distance);
        return new BlockPos(x, start.getY(), z);
    }

    private static BlockPos precedingWorldPoint(SiegePlan plan, SiegeWorldSnapshot snapshot,
                                                SiegePlan.BreachStep breach) {
        SiegePlan.Point previous = new SiegePlan.Point(snapshot.grid().startX(), snapshot.grid().startZ());
        for (SiegePlan.Point point : plan.path()) {
            if (point.x() == breach.x() && point.z() == breach.z()) return snapshot.worldPoint(previous.x(), previous.z());
            previous = point;
        }
        return snapshot.worldPoint(snapshot.grid().startX(), snapshot.grid().startZ());
    }

    private static ServerLevel levelFor(MinecraftServer server, String dimensionId) {
        for (ServerLevel level : server.getAllLevels()) {
            if (level.dimension().location().toString().equals(dimensionId)) return level;
        }
        return null;
    }

    public static CycleStats lastStats() { return lastStats; }

    private record Breaker(Mob mob, String typeId) { }

    private static final class EncounterState {
        private int blockedChecks;
        private long cachedFingerprint = Long.MIN_VALUE;
        private SiegePlan cachedPlan;
        private int nextBreachIndex;
        private long nextBreakGameTime;

        private void resetBlocked() {
            blockedChecks = 0;
            invalidatePlan();
        }

        private void invalidatePlan() {
            cachedFingerprint = Long.MIN_VALUE;
            cachedPlan = null;
            nextBreachIndex = 0;
        }
    }

    public record CycleStats(int encountersProcessed, int siegeEligible, int normalPathSuccesses,
                             int blockedChecks, int plansComputed, int planCacheHits,
                             int blocksBreached, double elapsedMillis) {
        static CycleStats empty() { return new CycleStats(0, 0, 0, 0, 0, 0, 0, 0.0); }
    }
}
