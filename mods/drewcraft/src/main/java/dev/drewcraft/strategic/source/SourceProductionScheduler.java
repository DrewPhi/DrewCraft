package dev.drewcraft.strategic.source;

import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.model.StrategicGroup;
import java.util.List;
import java.util.UUID;
import net.minecraft.server.MinecraftServer;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/** Bounded source scheduler. It iterates persistent records only and never scans distant chunks. */
public final class SourceProductionScheduler {
    private static long nextDueGameTime = Long.MIN_VALUE;
    private static long lastObservedGameTime = Long.MIN_VALUE;
    private static int sourceCursor;
    private static volatile CycleStats lastStats = CycleStats.empty();

    private SourceProductionScheduler() {
    }

    public static void onServerTick(ServerTickEvent.Post event) {
        if (!DrewCraftConfig.STRATEGIC_KERNEL.get()) return;
        MinecraftServer server = event.getServer();
        long now = server.overworld().getGameTime();
        if (lastObservedGameTime != Long.MIN_VALUE && now < lastObservedGameTime) {
            nextDueGameTime = Long.MIN_VALUE;
            sourceCursor = 0;
        }
        lastObservedGameTime = now;
        if (nextDueGameTime != Long.MIN_VALUE && now < nextDueGameTime) return;
        nextDueGameTime = now + DrewCraftConfig.STRATEGIC_SOURCE_INTERVAL_TICKS.get();

        DrewCraftSavedData data = DrewCraftSavedData.get(server);
        lastStats = runCycleFromIndex(
                data,
                now,
                DrewCraftConfig.STRATEGIC_MAX_SOURCES_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_MAX_LAUNCHES_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_SOURCE_ROUTE_RETRY_TICKS.get(),
                sourceCursor,
                (source, gameTime) -> SourceLaunchPlanner.plan(data, source, gameTime)
        );
        sourceCursor = lastStats.nextCursor();
    }

    /** Deterministic zero-cursor harness used by focused tests/admin tooling. */
    public static CycleStats runCycle(DrewCraftSavedData data, long gameTime,
                                      int maxSources, int maxLaunches, long retryTicks,
                                      Planner planner) {
        return runCycleFromIndex(data, gameTime, maxSources, maxLaunches, retryTicks, 0, planner);
    }

    public static CycleStats runCycleFromIndex(DrewCraftSavedData data, long gameTime,
                                               int maxSources, int maxLaunches, long retryTicks,
                                               int startIndex, Planner planner) {
        long started = System.nanoTime();
        List<SourceRecord> sources = data.sourceRecords();
        int total = sources.size();
        int seen = 0;
        int due = 0;
        int launched = 0;
        int routeFailures = 0;
        int rejectedCommits = 0;
        int normalizedStart = total == 0 ? 0 : Math.floorMod(startIndex, total);

        while (seen < Math.min(maxSources, total) && launched < maxLaunches) {
            SourceRecord source = sources.get((normalizedStart + seen) % total);
            seen++;
            if (!source.canLaunch(gameTime)) continue;
            due++;
            long expectedGeneration = source.generation();
            SourceLaunchPlanner.PlanResult planned = planner.plan(source, gameTime);
            if (!planned.success()) {
                data.postponeSourceLaunch(source.sourceId(), expectedGeneration, gameTime, retryTicks);
                routeFailures++;
                continue;
            }
            if (commitPlannedLaunch(data, source.sourceId(), expectedGeneration, planned.group(), gameTime)) {
                launched++;
            } else {
                rejectedCommits++;
            }
        }

        int nextCursor = total == 0 ? 0 : (normalizedStart + Math.max(1, seen)) % total;
        return new CycleStats(
                total, seen, due, launched, routeFailures, rejectedCommits, nextCursor,
                (System.nanoTime() - started) / 1_000_000.0
        );
    }

    /**
     * BP5 variable-strength launch commit. Synchronizing on SavedData preserves BP4's clear-vs-launch
     * transaction boundary while charging the exact represented population instead of base strength.
     */
    public static boolean commitPlannedLaunch(DrewCraftSavedData data, UUID sourceId,
                                              long expectedGeneration, StrategicGroup group,
                                              long gameTime) {
        synchronized (data) {
            SourceRecord source = data.sourceRecord(sourceId)
                    .orElseThrow(() -> new IllegalArgumentException("unknown strategic source: " + sourceId));
            UUID groupSource = group.sourceId()
                    .orElseThrow(() -> new IllegalArgumentException("source launch group is missing sourceId"));
            if (!sourceId.equals(groupSource)) throw new IllegalArgumentException("group/source id mismatch");
            if (!source.factionId().equals(group.factionId())) throw new IllegalArgumentException("group/source faction mismatch");
            if (!source.dimension().equals(group.position().dimension())) throw new IllegalArgumentException("group/source dimension mismatch");
            if (data.strategicGroup(group.groupId()).isPresent()) {
                throw new IllegalStateException("duplicate strategic group id: " + group.groupId());
            }
            if (!source.commitLaunch(expectedGeneration, gameTime, group.totalStrength())) return false;
            data.upsertStrategicGroup(group);
            return true;
        }
    }

    public static CycleStats lastStats() { return lastStats; }

    @FunctionalInterface
    public interface Planner {
        SourceLaunchPlanner.PlanResult plan(SourceRecord source, long gameTime);
    }

    public record CycleStats(int totalSources, int sourcesSeen, int sourcesDue, int groupsLaunched,
                             int routeFailures, int rejectedCommits, int nextCursor, double elapsedMillis) {
        static CycleStats empty() { return new CycleStats(0, 0, 0, 0, 0, 0, 0, 0.0); }
    }
}
