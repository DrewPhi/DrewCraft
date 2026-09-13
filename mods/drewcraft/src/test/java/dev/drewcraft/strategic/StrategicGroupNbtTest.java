package dev.drewcraft.strategic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicMission;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import dev.drewcraft.strategic.model.StrategicTargetKnowledge;
import dev.drewcraft.strategic.persistence.StrategicGroupNbt;
import java.util.Map;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.Test;

class StrategicGroupNbtTest {
    @Test
    void roundTripsIdentityProgressCompositionAndMission() {
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 10.0, 20.0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 1010.0, 20.0);
        StrategicMission mission = new StrategicMission(
                "drewcraft:test_army",
                StrategicTargetKnowledge.SCOUTED_REGION,
                "scouted regional objective; no player lookup",
                destination,
                400L
        );
        StrategicGroup original = new StrategicGroup(
                UUID.randomUUID(), "drewcraft:undead", StrategicGroupType.ARMY, UUID.randomUUID(),
                start, StrategicRoute.between(start, destination), mission, 2.0,
                Map.of("minecraft:zombie", 16, "minecraft:skeleton", 4), 20,
                StrategicGroupState.TRAVELING, 400L
        );
        original.advanceBySeconds(40.0, 40.0);

        CompoundTag tag = StrategicGroupNbt.save(original);
        StrategicGroup restored = StrategicGroupNbt.load(tag);

        assertEquals(original.groupId(), restored.groupId());
        assertEquals(original.factionId(), restored.factionId());
        assertEquals(original.groupType(), restored.groupType());
        assertEquals(original.position(), restored.position());
        assertEquals(original.destination(), restored.destination());
        assertEquals(original.route().cursor(), restored.route().cursor());
        assertEquals(original.route().segmentCostMultipliers(), restored.route().segmentCostMultipliers());
        assertEquals(original.totalStrength(), restored.totalStrength());
        assertEquals(original.composition(), restored.composition());
        assertEquals(original.state(), restored.state());
        assertEquals(original.lastSimulatedGameTime(), restored.lastSimulatedGameTime());
        assertEquals(original.mission(), restored.mission());
    }

    @Test
    void migratesSchemaOneFlatRouteToUnitCostMultipliersAndLegacyMission() {
        StrategicGroup group = StrategicGroup.testGroup(
                new StrategicPosition("minecraft:overworld", 0.0, 0.0),
                new StrategicPosition("minecraft:overworld", 100.0, 0.0),
                0L
        );
        CompoundTag tag = StrategicGroupNbt.save(group);
        tag.putInt("SchemaVersion", 1);
        tag.getCompound("Route").remove("SegmentCostMultipliers");
        tag.remove("Mission");

        StrategicGroup restored = StrategicGroupNbt.load(tag);
        assertEquals(1, restored.route().segmentCostMultipliers().size());
        assertEquals(1.0, restored.route().segmentCostMultipliers().getFirst(), 1.0e-9);
        assertEquals(StrategicTargetKnowledge.LEGACY_ROUTE, restored.mission().targetKnowledge());
        assertEquals(restored.destination(), restored.mission().target());
    }

    @Test
    void migratesSchemaTwoToLegacyMission() {
        StrategicGroup group = StrategicGroup.testGroup(
                new StrategicPosition("minecraft:overworld", 0.0, 0.0),
                new StrategicPosition("minecraft:overworld", 100.0, 0.0),
                0L
        );
        CompoundTag tag = StrategicGroupNbt.save(group);
        tag.putInt("SchemaVersion", 2);
        tag.remove("Mission");

        StrategicGroup restored = StrategicGroupNbt.load(tag);
        assertEquals(StrategicTargetKnowledge.LEGACY_ROUTE, restored.mission().targetKnowledge());
        assertEquals(restored.destination(), restored.mission().target());
    }

    @Test
    void rejectsFutureGroupSchema() {
        StrategicGroup group = StrategicGroup.testGroup(
                new StrategicPosition("minecraft:overworld", 0.0, 0.0),
                new StrategicPosition("minecraft:overworld", 100.0, 0.0),
                0L
        );
        CompoundTag tag = StrategicGroupNbt.save(group);
        tag.putInt("SchemaVersion", StrategicGroup.CURRENT_SCHEMA_VERSION + 1);

        assertThrows(IllegalStateException.class, () -> StrategicGroupNbt.load(tag));
    }
}
