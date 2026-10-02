package com.memesgmm.linear.linear;

import com.memesgmm.linear.LinearTestSupport;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import java.security.MessageDigest;
import static org.junit.jupiter.api.Assertions.*;

class ConverterSafetyTest {
    @TempDir Path temp;
    @Test void validUnpaddedFinalSectorIsNotMistakenForCorruption() throws Exception {
        LinearTestSupport.resetState();
        Path source = temp.resolve("r.0.0.mca");
        byte[] raw = new byte[8192 + 8];
        java.nio.ByteBuffer.wrap(raw).putInt((2 << 8) | 1);
        java.nio.ByteBuffer.wrap(raw, 8192, 4).putInt(4);
        raw[8196] = 3; // Uncompressed raw bytes; final sector has no padding.
        raw[8197] = 1; raw[8198] = 2; raw[8199] = 3;
        Files.write(source, raw);
        MCAConverter.convertFolder(temp);
        assertFalse(Files.exists(source));
        try (var linear = new LinearRegionFile(temp.resolve("r.0.0.linear"), false, LinearTestSupport.dummyStorageInfo());
             var input = linear.read(new net.minecraft.world.level.ChunkPos(0, 0))) {
            assertArrayEquals(new byte[]{1,2,3}, input.readAllBytes());
        }
    }
    @Test void invalidAnvilLocationFailsWithoutVanillaHeaderRepairOrDeletion() throws Exception {
        LinearTestSupport.resetState();
        Path source = temp.resolve("r.0.0.mca");
        byte[] raw = new byte[8192];
        java.nio.ByteBuffer.wrap(raw).putInt((2 << 8) | 1);
        Files.write(source, raw);
        assertThrows(IllegalStateException.class, () -> MCAConverter.convertFolder(temp));
        assertArrayEquals(raw, Files.readAllBytes(source));
        assertFalse(Files.exists(temp.resolve("r.0.0.linear")));
    }
    @Test void corruptedRegionWithWorldSnapshotPolicyNeverRegeneratesOrMovesEvidence() throws Exception {
        LinearTestSupport.resetState();
        var field = com.memesgmm.linear.config.LinearConfig.class.getDeclaredField("backupEnabled");
        field.setAccessible(true);
        field.setBoolean(null, false);
        Path broken = temp.resolve("r.0.0.linear");
        Files.write(broken, new byte[]{1, 2, 3});
        try (var linear = new LinearRegionFile(broken, false, LinearTestSupport.dummyStorageInfo())) {
            assertThrows(IllegalStateException.class, () -> linear.read(new net.minecraft.world.level.ChunkPos(0, 0)));
            assertThrows(IllegalStateException.class, () -> linear.read(new net.minecraft.world.level.ChunkPos(0, 0)));
            assertArrayEquals(new byte[]{1, 2, 3}, Files.readAllBytes(broken));
        } finally { LinearTestSupport.resetState(); }
    }
    private Path sample() throws Exception {
        return Files.copy(Path.of("/tmp/drewcraft-linear-real-regions/r.-6.1.mca"), temp.resolve("r.-6.1.mca"));
    }
    @Test void actualConverterVerifiesBeforeDeletingAndHandlesEquivalentInterruptedRun() throws Exception {
        LinearTestSupport.resetState();
        Path source = sample();
        MCAConverter.convertFolder(temp);
        assertFalse(Files.exists(source));
        assertTrue(Files.exists(temp.resolve("r.-6.1.linear")));
        sample();
        MCAConverter.convertFolder(temp);
        assertFalse(Files.exists(source));
    }
    @Test void incompleteExistingTargetFailsClosedAndRetainsOriginal() throws Exception {
        LinearTestSupport.resetState();
        Path source = sample();
        byte[] before = MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source));
        Files.write(temp.resolve("r.-6.1.linear"), new byte[]{1,2,3});
        assertThrows(IllegalStateException.class, () -> MCAConverter.convertFolder(temp));
        assertArrayEquals(before, MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source)));
        assertTrue(Files.exists(temp.resolve("r.-6.1.linear")));
    }
    @Test void externalChunkIsCopiedBeforeExternalFileRemoval() throws Exception {
        LinearTestSupport.resetState();
        Path source = temp.resolve("r.0.0.mca");
        byte[] bytes = new byte[2_000_000];
        new java.util.Random(17).nextBytes(bytes);
        var pos = new net.minecraft.world.level.ChunkPos(0, 0);
        try (var anvil = com.memesgmm.linear.util.LinearCompat.createRegionFile(
                LinearTestSupport.dummyStorageInfo(), source, temp, false)) {
            try (var out = anvil.getChunkDataOutputStream(pos)) { out.write(bytes); }
        }
        assertTrue(Files.exists(temp.resolve("c.0.0.mcc")));
        MCAConverter.convertFolder(temp);
        assertFalse(Files.exists(source));
        assertFalse(Files.exists(temp.resolve("c.0.0.mcc")));
        try (var linear = new LinearRegionFile(temp.resolve("r.0.0.linear"), false, LinearTestSupport.dummyStorageInfo());
             var input = linear.read(pos)) {
            assertArrayEquals(bytes, input.readAllBytes());
            assertNull(linear.read(new net.minecraft.world.level.ChunkPos(1, 1)));
        }
    }
}
