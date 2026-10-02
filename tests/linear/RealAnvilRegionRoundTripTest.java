package com.memesgmm.linear.linear;

import com.memesgmm.linear.LinearTestSupport;
import com.memesgmm.linear.util.LinearCompat;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.storage.RegionFile;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashMap;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

class RealAnvilRegionRoundTripTest {
    @TempDir Path temporary;

    @Test void realSavedRegionsSurviveLinearLibraryWriteAndColdReopen() throws Exception {
        Path sourceDirectory = Path.of("/tmp/drewcraft-linear-real-regions");
        int total = 0;
        try (var stream = Files.list(sourceDirectory)) {
            for (Path source : stream.filter(p -> p.toString().endsWith(".mca")).sorted().toList()) {
                byte[] before = MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source));
                String[] name = source.getFileName().toString().split("\\.");
                int rx = Integer.parseInt(name[1]), rz = Integer.parseInt(name[2]);
                Path copy = temporary.resolve(source.getFileName());
                Files.copy(source, copy);
                Map<ChunkPos, byte[]> raw = new HashMap<>();
                try (RegionFile anvil = LinearCompat.createRegionFile(LinearCompat.createDummyStorageInfo(),
                        copy, temporary, false)) {
                    for (int slot = 0; slot < 1024; slot++) {
                        ChunkPos position = new ChunkPos(rx*32+slot%32, rz*32+slot/32);
                        try (DataInputStream input = anvil.getChunkDataInputStream(position)) {
                            if (input != null) raw.put(position, input.readAllBytes());
                        }
                    }
                }
                Path encoded = temporary.resolve(source.getFileName().toString().replace(".mca", ".linear"));
                try (LinearRegionFile linear = new LinearRegionFile(encoded, false, LinearTestSupport.dummyStorageInfo())) {
                    for (var entry : raw.entrySet()) {
                        try (DataOutputStream output = linear.write(entry.getKey())) { output.write(entry.getValue()); }
                    }
                }
                try (LinearRegionFile reopened = new LinearRegionFile(encoded, false, LinearTestSupport.dummyStorageInfo())) {
                    for (var entry : raw.entrySet()) {
                        try (DataInputStream input = reopened.read(entry.getKey())) {
                            assertNotNull(input);
                            assertArrayEquals(entry.getValue(), input.readAllBytes());
                        }
                    }
                }
                assertArrayEquals(before, MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source)));
                total += raw.size();
                System.out.println(source.getFileName()+": "+raw.size()+" chunk payloads verified; Linear bytes="+Files.size(encoded));
            }
        }
        assertEquals(5120, total);
    }
}
