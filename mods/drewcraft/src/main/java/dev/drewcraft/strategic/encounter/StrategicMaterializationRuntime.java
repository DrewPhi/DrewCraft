package dev.drewcraft.strategic.encounter;

import dev.drewcraft.DrewCraft;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicPosition;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * Converts strategic records into a bounded tactical population only near players. All expensive
 * work is local to already-loaded chunks. This class never requests/forces a chunk load.
 */
public final class StrategicMaterializationRuntime {
    private static long nextDueGameTime = Long.MIN_VALUE;
    private static long lastObservedGameTime = Long.MIN_VALUE;

    private StrategicMaterializationRuntime() {
    }

    public static void onServerTick(ServerTickEvent.Post event) {
        if (!DrewCraftConfig.STRATEGIC_KERNEL.get()) return;
        MinecraftServer server = event.getServer();
        long now = server.overworld().getGameTime();
        int interval = DrewCraftConfig.STRATEGIC_MATERIALIZATION_INTERVAL_TICKS.get();

        if (lastObservedGameTime != Long.MIN_VALUE && now < lastObservedGameTime) {
            nextDueGameTime = Long.MIN_VALUE;
        }
        lastObservedGameTime = now;
        if (nextDueGameTime != Long.MIN_VALUE && now < nextDueGameTime) return;
        nextDueGameTime = now + interval;

        DrewCraftSavedData data = DrewCraftSavedData.get(server);
        int encounterBudget = DrewCraftConfig.STRATEGIC_MAX_ENCOUNTERS_PROCESSED_PER_CYCLE.get();
        StrategicSpawnBudget spawnBudget = new StrategicSpawnBudget(
                DrewCraftConfig.STRATEGIC_MAX_NEW_ENTITIES_PER_CYCLE.get()
        );
        int processed = processExistingEncounters(server, data, now, encounterBudget, spawnBudget);
        if (processed < encounterBudget && !spawnBudget.exhausted()) {
            createNearbyEncounters(server, data, now, encounterBudget - processed, spawnBudget);
        }
    }

    /** Death callbacks are idempotent because the durable encounter owns the active UUID set. */
    public static void onLivingDeath(LivingDeathEvent event) {
        if (!(event.getEntity().level() instanceof ServerLevel level)) return;
        Optional<StrategicEntityTags.TaggedEntity> tagged = StrategicEntityTags.read(event.getEntity());
        if (tagged.isEmpty()) return;

        StrategicEntityTags.TaggedEntity tag = tagged.get();
        DrewCraftSavedData data = DrewCraftSavedData.get(level.getServer());
        StrategicEncounter encounter = data.strategicEncounter(tag.encounterId()).orElse(null);
        if (encounter == null || !encounter.groupId().equals(tag.groupId())) return;
        data.recordStrategicCasualty(tag.encounterId(), event.getEntity().getUUID());
    }

    /**
     * Reject stale tactical entities whose durable encounter has already been reconciled. This is
     * deliberately validation-only: EntityJoinLevelEvent can fire while a chunk is still loading.
     */
    public static void onEntityJoinLevel(EntityJoinLevelEvent event) {
        if (!(event.getLevel() instanceof ServerLevel level)) return;
        Optional<StrategicEntityTags.TaggedEntity> tagged = StrategicEntityTags.read(event.getEntity());
        if (tagged.isEmpty()) return;

        StrategicEntityTags.TaggedEntity tag = tagged.get();
        DrewCraftSavedData data = DrewCraftSavedData.get(level.getServer());
        StrategicEncounter encounter = data.strategicEncounter(tag.encounterId()).orElse(null);
        boolean valid = encounter != null
                && encounter.groupId().equals(tag.groupId())
                && encounter.expectsEntity(event.getEntity().getUUID());
        if (!valid) {
            event.setCanceled(true);
            DrewCraft.LOGGER.debug(
                    "Rejected stale strategic entity {} for encounter {}",
                    event.getEntity().getUUID(), tag.encounterId()
            );
        }
    }

    private static int processExistingEncounters(MinecraftServer server, DrewCraftSavedData data,
                                                 long now, int budget,
                                                 StrategicSpawnBudget spawnBudget) {
        int processed = 0;
        for (StrategicEncounter encounter : data.strategicEncounters()) {
            if (processed >= budget) break;
            processed++;
            StrategicGroup group = data.strategicGroup(encounter.groupId()).orElse(null);
            if (group == null) continue;
            ServerLevel level = levelFor(server, group.position().dimension());

            if (encounter.state() == StrategicEncounterState.PREPARING
                    || encounter.state() == StrategicEncounterState.RECONCILING) {
                // PREPARING/RECONCILING surviving a restart means the transaction was interrupted.
                // Remove any loaded partial tactical objects, then safely return to strategic state.
                discardLoadedEntities(level, encounter);
                data.recoverInterruptedStrategicEncounter(encounter.encounterId());
                continue;
            }
            if (encounter.state() != StrategicEncounterState.MATERIALIZED) continue;

            if (group.totalStrength() == 0) {
                discardLoadedEntities(level, encounter);
                data.completeStrategicEncounter(encounter.encounterId());
                continue;
            }

            boolean playerNearby = level != null && hasPlayerWithin(
                    level,
                    group.position(),
                    effectiveDematerializationRadius()
            );
            if (playerNearby) {
                data.touchEncounterPlayerSeen(encounter.encounterId(), now);
                releaseMissingReservations(level, data, encounter);
                if (!spawnBudget.exhausted()) fillWave(level, data, group, encounter, spawnBudget);
                continue;
            }

            long grace = DrewCraftConfig.STRATEGIC_DEMATERIALIZATION_GRACE_TICKS.get();
            if (now - encounter.lastPlayerSeenGameTime() >= grace) {
                discardLoadedEntities(level, encounter);
                data.completeStrategicEncounter(encounter.encounterId());
            }
        }
        return processed;
    }

    private static void createNearbyEncounters(MinecraftServer server, DrewCraftSavedData data,
                                               long now, int budget,
                                               StrategicSpawnBudget spawnBudget) {
        int processed = 0;
        int radius = DrewCraftConfig.STRATEGIC_MATERIALIZATION_RADIUS_BLOCKS.get();
        for (StrategicGroup group : data.strategicGroups()) {
            if (processed >= budget || spawnBudget.exhausted()) break;
            if (group.totalStrength() <= 0
                    || group.state() == StrategicGroupState.DESTROYED
                    || group.state() == StrategicGroupState.MATERIALIZED
                    || data.strategicEncounterForGroup(group.groupId()).isPresent()) {
                continue;
            }
            ServerLevel level = levelFor(server, group.position().dimension());
            if (level == null || !hasPlayerWithin(level, group.position(), radius)) continue;
            if (!isGroupChunkAlreadyLoaded(level, group.position())) continue;

            processed++;
            DrewCraftSavedData.BeginEncounterResult result = data.beginStrategicEncounter(group.groupId(), now);
            if (!result.created()) continue;
            StrategicEncounter encounter = result.encounter();
            fillWave(level, data, group, encounter, spawnBudget);
            if (encounter.activeEntityCount() > 0) {
                data.markEncounterMaterialized(encounter.encounterId());
            } else {
                data.completeStrategicEncounter(encounter.encounterId());
            }
        }
    }

    private static void fillWave(ServerLevel level, DrewCraftSavedData data,
                                 StrategicGroup group, StrategicEncounter encounter,
                                 StrategicSpawnBudget spawnBudget) {
        int cap = DrewCraftConfig.STRATEGIC_MAX_ACTIVE_ENTITIES_PER_ENCOUNTER.get();
        List<String> wave = StrategicEncounterPlanner.nextWave(group, encounter, cap);
        int ordinal = encounter.activeEntityCount();
        for (String entityTypeId : wave) {
            if (spawnBudget.exhausted()) break;
            BlockPos spawnPos = findLoadedSpawnPosition(level, group.position(), ordinal++);
            if (spawnPos == null) break;
            EntityType<?> rawType = EntityType.byString(entityTypeId).orElse(null);
            if (rawType == null) {
                DrewCraft.LOGGER.warn("Unknown strategic entity type {}; skipping tactical spawn", entityTypeId);
                continue;
            }

            Entity entity = createTaggedEntity(
                    rawType, level, spawnPos, group.groupId(), encounter.encounterId(), entityTypeId
            );
            if (entity == null) continue;

            // Register authority before addFreshEntity triggers EntityJoinLevelEvent.
            data.registerEncounterEntity(encounter.encounterId(), entity.getUUID(), entityTypeId);
            if (level.addFreshEntity(entity)) {
                spawnBudget.tryConsume();
            } else {
                encounter.detachSurvivor(entity.getUUID());
                data.markStrategicDirty();
            }
        }
    }

    private static <T extends Entity> T createTaggedEntity(EntityType<T> type, ServerLevel level,
                                                            BlockPos pos, UUID groupId,
                                                            UUID encounterId, String entityTypeId) {
        return type.create(
                level,
                entity -> StrategicEntityTags.tag(entity, groupId, encounterId, entityTypeId),
                pos,
                MobSpawnType.EVENT,
                true,
                false
        );
    }

    private static BlockPos findLoadedSpawnPosition(ServerLevel level, StrategicPosition center, int ordinal) {
        int baseX = (int) Math.floor(center.x());
        int baseZ = (int) Math.floor(center.z());
        for (int attempt = 0; attempt < 12; attempt++) {
            int index = ordinal + attempt;
            int ring = 1 + index / 8;
            int spoke = index & 7;
            int[] dx = {1, 1, 0, -1, -1, -1, 0, 1};
            int[] dz = {0, 1, 1, 1, 0, -1, -1, -1};
            int x = baseX + dx[spoke] * ring * 3;
            int z = baseZ + dz[spoke] * ring * 3;
            BlockPos probe = new BlockPos(x, level.getSeaLevel(), z);
            if (!level.hasChunkAt(probe)) continue;
            int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
            BlockPos candidate = new BlockPos(x, y, z);
            if (level.hasChunkAt(candidate)) return candidate;
        }
        return null;
    }

    private static boolean isGroupChunkAlreadyLoaded(ServerLevel level, StrategicPosition position) {
        return level.hasChunkAt(new BlockPos(
                (int) Math.floor(position.x()), level.getSeaLevel(), (int) Math.floor(position.z())
        ));
    }

    private static boolean hasPlayerWithin(ServerLevel level, StrategicPosition position, int radius) {
        double radiusSquared = (double) radius * radius;
        for (ServerPlayer player : level.players()) {
            double dx = player.getX() - position.x();
            double dz = player.getZ() - position.z();
            if (dx * dx + dz * dz <= radiusSquared) return true;
        }
        return false;
    }

    private static int effectiveDematerializationRadius() {
        return Math.max(
                DrewCraftConfig.STRATEGIC_MATERIALIZATION_RADIUS_BLOCKS.get(),
                DrewCraftConfig.STRATEGIC_DEMATERIALIZATION_RADIUS_BLOCKS.get()
        );
    }

    /**
     * If a persisted entity UUID is no longer loaded while a player is observing the encounter,
     * release it back into the abstract reserve. A later stale disk copy is rejected by join tags.
     */
    private static void releaseMissingReservations(ServerLevel level, DrewCraftSavedData data,
                                                   StrategicEncounter encounter) {
        boolean changed = false;
        for (UUID entityId : encounter.activeEntityIds()) {
            if (level.getEntity(entityId) == null) {
                encounter.detachSurvivor(entityId);
                changed = true;
            }
        }
        if (changed) data.markStrategicDirty();
    }

    private static void discardLoadedEntities(ServerLevel level, StrategicEncounter encounter) {
        if (level == null) return;
        for (UUID entityId : encounter.activeEntityIds()) {
            Entity entity = level.getEntity(entityId);
            if (entity != null) entity.discard();
        }
    }

    private static ServerLevel levelFor(MinecraftServer server, String dimensionId) {
        for (ServerLevel level : server.getAllLevels()) {
            if (level.dimension().location().toString().equals(dimensionId)) return level;
        }
        return null;
    }
}
