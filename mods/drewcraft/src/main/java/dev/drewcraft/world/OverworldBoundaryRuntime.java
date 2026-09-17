package dev.drewcraft.world;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/** Enforces the generated-area boundary without applying vanilla's cross-dimension world border. */
public final class OverworldBoundaryRuntime {
    private static final String FILE_NAME = "drewcraft-overworld-boundary.json";
    private static final long RELOAD_INTERVAL_TICKS = 100L;
    private static OverworldBoundary boundary;
    private static long lastReload = Long.MIN_VALUE;

    private OverworldBoundaryRuntime() {
    }

    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer player)
                || player.level().dimension() != Level.OVERWORLD) {
            return;
        }
        long gameTime = player.serverLevel().getGameTime();
        if (boundary == null || gameTime - lastReload >= RELOAD_INTERVAL_TICKS) {
            boundary = load(player);
            lastReload = gameTime;
        }
        OverworldBoundary active = boundary;
        if (active == null || active.contains(player.getX(), player.getZ())) {
            return;
        }
        OverworldBoundary.Position safe = active.clampInside(player.getX(), player.getZ());
        player.stopRiding();
        player.teleportTo(safe.x(), player.getY(), safe.z());
        player.setDeltaMovement(0.0, 0.0, 0.0);
        if (player.tickCount % 40 == 0) {
            player.displayClientMessage(Component.literal(
                    "That part of the Overworld is not generated yet. The boundary will expand automatically."), true);
        }
    }

    private static OverworldBoundary load(ServerPlayer player) {
        Path path = player.getServer().getWorldPath(LevelResource.ROOT).resolve(FILE_NAME);
        if (!Files.isRegularFile(path)) {
            return null;
        }
        try (Reader reader = Files.newBufferedReader(path)) {
            JsonObject json = JsonParser.parseReader(reader).getAsJsonObject();
            if (json.get("schemaVersion").getAsInt() != 1 || !json.get("enabled").getAsBoolean()
                    || !"minecraft:overworld".equals(json.get("dimension").getAsString())) {
                return null;
            }
            return new OverworldBoundary(
                    json.get("centerX").getAsDouble(),
                    json.get("centerZ").getAsDouble(),
                    json.get("radiusBlocks").getAsDouble());
        } catch (IOException | RuntimeException ignored) {
            return null;
        }
    }
}
