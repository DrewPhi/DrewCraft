package dev.drewcraft.strategic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.persistence.StrategicGroupNbt;
import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.Test;

class StrategicGroupNbtTest {
    @Test
    void roundTripsIdentityProgressAndComposition() {
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 10.0, 20.0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 1010.0, 20.0);
        StrategicGroup original = StrategicGroup.testGroup(start, destination, 400L);
        original.advanceBySeconds(40.0, 40.0);

        CompoundTag tag = StrategicGroupNbt.save(original);
        StrategicGroup restored = StrategicGroupNbt.load(tag);

        assertEquals(original.groupId(), restored.groupId());
        assertEquals(original.factionId(), restored.factionId());
        assertEquals(original.groupType(), restored.groupType());
        assertEquals(original.position(), restored.position());
        assertEquals(original.destination(), restored.destination());
        assertEquals(original.route().cursor(), restored.route().cursor());
        assertEquals(original.totalStrength(), restored.totalStrength());
        assertEquals(original.composition(), restored.composition());
        assertEquals(original.state(), restored.state());
        assertEquals(original.lastSimulatedGameTime(), restored.lastSimulatedGameTime());
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
