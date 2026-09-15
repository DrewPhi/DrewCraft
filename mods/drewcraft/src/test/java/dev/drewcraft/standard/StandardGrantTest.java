package dev.drewcraft.standard;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.Test;

final class StandardGrantTest {
    @Test
    void firstLoginGrantsAndRelogDoesNot() {
        CompoundTag fresh = new CompoundTag();
        assertTrue(StandardGrantRuntime.shouldGrant(fresh));
        StandardGrantRuntime.markGranted(fresh);
        assertFalse(StandardGrantRuntime.shouldGrant(fresh));
    }

    @Test
    void missingDataTreatsPlayerAsNew() {
        assertTrue(StandardGrantRuntime.shouldGrant(null));
    }
}
