package dev.drewcraft.strategic.source;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import java.util.Map;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.Test;

class SourceProductionTransactionTest {
    @Test
    void rediscoveryIsIdempotentAndClearingNeverReactivates() {
        DrewCraftSavedData data = emptyData();
        SourceDescriptor descriptor = descriptor(0);
        DrewCraftSavedData.DiscoverSourceResult first = data.discoverSource(descriptor, 0L);
        DrewCraftSavedData.DiscoverSourceResult second = data.discoverSource(descriptor, 50L);
        assertTrue(first.created());
        assertFalse(second.created());
        assertEquals(first.source().sourceId(), second.source().sourceId());
        assertEquals(1, data.sourceRecords().size());

        assertTrue(data.clearSource(first.source().sourceId(), 500L, "PLAYER_BREAK", "Drew"));
        DrewCraftSavedData.DiscoverSourceResult afterClear = data.discoverSource(descriptor, 1000L);
        assertFalse(afterClear.created());
        assertEquals(SourceState.CLEARED, afterClear.source().state());
        assertEquals(1, data.sourceRecords().size());

        DrewCraftSavedData restored = DrewCraftSavedData.load(data.save(new CompoundTag(), null), null);
        assertEquals(SourceState.CLEARED, restored.sourceRecord(first.source().sourceId()).orElseThrow().state());
    }

    @Test
    void committedGroupSurvivesClearButNoPostClearCommitCanSucceed() {
        DrewCraftSavedData data = emptyData();
        SourceRecord source = data.discoverSource(descriptor(0), 0L).source();
        long dueTime = source.nextActionGameTime();
        long generation = source.generation();
        StrategicGroup committed = groupFor(source, 0, dueTime);

        assertTrue(data.commitSourceLaunch(source.sourceId(), generation, committed, dueTime));
        assertEquals(1, data.strategicGroups().size());
        assertTrue(data.clearSource(source.sourceId(), dueTime + 1, "EXPLOSION", null));
        assertEquals(SourceState.CLEARED, source.state());
        assertEquals(1, data.strategicGroups().size());
        assertEquals(source.sourceId(), data.strategicGroups().getFirst().sourceId().orElseThrow());

        StrategicGroup rejected = groupFor(source, 1, dueTime + 100000L);
        assertFalse(data.commitSourceLaunch(source.sourceId(), source.generation(), rejected, dueTime + 100000L));
        assertEquals(1, data.strategicGroups().size());
    }

    @Test
    void clearDuringPlanningInvalidatesSchedulerCommit() {
        DrewCraftSavedData data = emptyData();
        SourceRecord source = data.discoverSource(descriptor(0), 0L).source();
        long now = source.nextActionGameTime();

        SourceProductionScheduler.CycleStats stats = SourceProductionScheduler.runCycle(
                data, now, 16, 4, 1200L,
                (planningSource, gameTime) -> {
                    data.clearSource(planningSource.sourceId(), gameTime, "PLAYER_BREAK", "Drew");
                    return new SourceLaunchPlanner.PlanResult(groupFor(planningSource, 0, gameTime), "ok");
                }
        );

        assertEquals(0, stats.groupsLaunched());
        assertEquals(1, stats.rejectedCommits());
        assertEquals(SourceState.CLEARED, source.state());
        assertTrue(data.strategicGroups().isEmpty());
    }

    @Test
    void productionCycleObeysGlobalLaunchCap() {
        DrewCraftSavedData data = emptyData();
        SourceRecord first = data.discoverSource(descriptor(0), 0L).source();
        SourceRecord second = data.discoverSource(descriptor(100), 0L).source();
        long now = Math.max(first.nextActionGameTime(), second.nextActionGameTime());

        SourceProductionScheduler.CycleStats stats = SourceProductionScheduler.runCycle(
                data, now, 16, 1, 1200L,
                (source, gameTime) -> new SourceLaunchPlanner.PlanResult(
                        groupFor(source, source.launchSerial(), gameTime), "ok"
                )
        );

        assertEquals(1, stats.groupsLaunched());
        assertEquals(1, data.strategicGroups().size());
    }

    private static DrewCraftSavedData emptyData() {
        CompoundTag tag = new CompoundTag();
        tag.putInt("SchemaVersion", DrewCraftSavedData.CURRENT_SCHEMA_VERSION);
        return DrewCraftSavedData.load(tag, null);
    }

    private static SourceDescriptor descriptor(int offset) {
        return new SourceDescriptor(
                "minecraft:overworld", "drewcraft:test_fort", offset, 64, offset,
                new SourceCorePosition("minecraft:overworld", offset + 1, 65, offset + 1),
                SourceClass.TEST, "drewcraft:test_hostile"
        );
    }

    private static StrategicGroup groupFor(SourceRecord source, long serial, long gameTime) {
        StrategicPosition start = new StrategicPosition(source.dimension(), source.anchorX() + 0.5, source.anchorZ() + 0.5);
        StrategicPosition destination = new StrategicPosition(source.dimension(), start.x() + 128.0 + serial, start.z());
        return new StrategicGroup(
                UUID.nameUUIDFromBytes((source.sourceId() + ":" + serial).getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                source.factionId(), StrategicGroupType.PATROL, source.sourceId(),
                start, StrategicRoute.between(start, destination), source.movementSpeedBlocksPerSecond(),
                Map.of("minecraft:zombie", source.launchStrength()), source.launchStrength(),
                StrategicGroupState.TRAVELING, gameTime
        );
    }
}
