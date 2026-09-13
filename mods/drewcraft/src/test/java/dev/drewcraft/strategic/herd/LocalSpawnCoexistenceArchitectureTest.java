package dev.drewcraft.strategic.herd;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;

/**
 * Architecture guard for BP7. DrewCraft strategic ecology is additive: it must not install a
 * global natural-spawn/spawner suppression path, and untagged joins must exit before stale-tag
 * cancellation is considered.
 */
class LocalSpawnCoexistenceArchitectureTest {
    @Test
    void strategicEcologyDoesNotHookOrReplaceVanillaSpawnSystems() throws IOException {
        Path main = Path.of("src/main/java/dev/drewcraft");
        String allJava;
        try (var files = Files.walk(main)) {
            allJava = files
                    .filter(path -> path.toString().endsWith(".java"))
                    .map(LocalSpawnCoexistenceArchitectureTest::read)
                    .reduce("", (a, b) -> a + "\n" + b);
        }

        assertFalse(allJava.contains("MobSpawnEvent"), "strategic code must not cancel global mob-spawn events");
        assertFalse(allJava.contains("NaturalSpawner"), "strategic code must not replace vanilla natural spawning");
        assertFalse(allJava.contains("SpawnPlacements"), "strategic code must not rewrite vanilla spawn placement rules");
        assertFalse(allJava.contains("BaseSpawner"), "strategic code must not rewrite ordinary spawner behavior");
    }

    @Test
    void untaggedEntityJoinReturnsBeforeAnyCancellation() throws IOException {
        String runtime = Files.readString(Path.of(
                "src/main/java/dev/drewcraft/strategic/encounter/StrategicMaterializationRuntime.java"
        ));
        int emptyReturn = runtime.indexOf("if (tagged.isEmpty()) return;");
        int cancellation = runtime.indexOf("event.setCanceled(true)");
        assertTrue(emptyReturn >= 0, "untagged entity fast-return contract missing");
        assertTrue(cancellation > emptyReturn, "join cancellation must only occur after DrewCraft strategic tag validation");
    }

    @Test
    void herdKillSwitchOnlyGatesStrategicHerdRecordsAndTaggedCopies() throws IOException {
        String scheduler = Files.readString(Path.of(
                "src/main/java/dev/drewcraft/strategic/simulation/StrategicScheduler.java"
        ));
        String runtime = Files.readString(Path.of(
                "src/main/java/dev/drewcraft/strategic/encounter/StrategicMaterializationRuntime.java"
        ));
        String config = Files.readString(Path.of(
                "src/main/java/dev/drewcraft/config/DrewCraftConfig.java"
        ));

        assertTrue(config.contains("features.strategicHerds"), "independent strategic-herd feature switch missing");
        assertTrue(scheduler.contains("group.groupType() != StrategicGroupType.HERD"),
                "disabled herds must be excluded from coarse strategic movement");
        assertTrue(runtime.contains("group.groupType() == StrategicGroupType.HERD && !DrewCraftConfig.STRATEGIC_HERDS.get()"),
                "disabled herds must not materialize and active strategic herd copies must reconcile");
        assertFalse(runtime.contains("getEntitiesOfClass(Animal.class"),
                "herd disabling must never scan/mutate ordinary animal populations");
    }

    private static String read(Path path) {
        try {
            return Files.readString(path);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}
