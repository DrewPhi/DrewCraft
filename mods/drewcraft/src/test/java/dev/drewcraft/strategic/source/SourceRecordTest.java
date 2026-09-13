package dev.drewcraft.strategic.source;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.Test;

class SourceRecordTest {
    @Test
    void generatedIdentityIsStableAndDoesNotComeFromPhysicalCoreAuthority() {
        SourceDescriptor first = descriptor(10, 70, 20, 12, 71, 22);
        SourceDescriptor rediscovered = descriptor(10, 70, 20, 12, 71, 22);
        SourceDescriptor differentStructureAnchor = descriptor(11, 70, 20, 12, 71, 22);

        assertEquals(first.stableSourceId(), rediscovered.stableSourceId());
        assertNotEquals(first.stableSourceId(), differentStructureAnchor.stableSourceId());
        assertTrue(SourceRecord.discovered(first, 100L).identityMatches(rediscovered));
    }

    @Test
    void clearIsIdempotentAndSurvivesNbtRoundTrip() {
        SourceRecord source = SourceRecord.discovered(descriptor(0, 64, 0, 1, 65, 1), 0L);
        long before = source.generation();
        assertTrue(source.clear(500L, "PLAYER_BREAK", "Drew"));
        assertFalse(source.clear(600L, "EXPLOSION", null));
        assertEquals(before + 1, source.generation());
        assertEquals(SourceState.CLEARED, source.state());

        CompoundTag tag = SourceRecordNbt.save(source);
        SourceRecord restored = SourceRecordNbt.load(tag);
        assertEquals(source.sourceId(), restored.sourceId());
        assertEquals(SourceState.CLEARED, restored.state());
        assertEquals(500L, restored.clearedAtGameTime().orElseThrow());
        assertEquals("PLAYER_BREAK", restored.clearCause().orElseThrow());
        assertEquals("Drew", restored.clearedBy().orElseThrow());
        assertFalse(restored.canLaunch(Long.MAX_VALUE - 1));
    }

    private static SourceDescriptor descriptor(int ax, int ay, int az, int cx, int cy, int cz) {
        return new SourceDescriptor(
                "minecraft:overworld", "drewcraft:test_fort", ax, ay, az,
                new SourceCorePosition("minecraft:overworld", cx, cy, cz),
                SourceClass.TEST, "drewcraft:test_hostile"
        );
    }
}
