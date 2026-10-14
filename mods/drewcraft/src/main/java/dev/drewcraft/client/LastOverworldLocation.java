package dev.drewcraft.client;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.drewcraft.DrewCraft;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.client.event.ClientPlayerNetworkEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/** Local-only preload center. Never exposes player positions over HTTP. */
@EventBusSubscriber(modid = DrewCraft.MOD_ID, value = Dist.CLIENT)
public final class LastOverworldLocation {
    private static int ticks;

    @SubscribeEvent
    public static void tick(ClientTickEvent.Post event) {
        if (++ticks % 200 == 0) record(Minecraft.getInstance().player);
    }

    @SubscribeEvent
    public static void logout(ClientPlayerNetworkEvent.LoggingOut event) {
        record(event.getPlayer());
    }

    private static void record(LocalPlayer player) {
        if (player == null || !player.level().dimension().location().toString().equals("minecraft:overworld")) return;
        var server = Minecraft.getInstance().getCurrentServer();
        if (server == null) return;
        var root = FMLPaths.GAMEDIR.get();
        var metadata = root.resolve("drewcraft-preload-world.json");
        if (!Files.isRegularFile(metadata)) return;
        try {
            JsonObject identity = JsonParser.parseString(Files.readString(metadata)).getAsJsonObject();
            String address = server.ip.contains(":") ? server.ip : server.ip + ":25565";
            if (!identity.get("address").getAsString().equals(address)) return;
            JsonObject record = new JsonObject();
            record.add("identity", identity);
            record.addProperty("x", player.getBlockX());
            record.addProperty("z", player.getBlockZ());
            var target = root.resolve("drewcraft-last-location.json");
            var pending = root.resolve("drewcraft-last-location.json.tmp");
            Files.writeString(pending, record.toString(), StandardCharsets.UTF_8);
            try {
                Files.move(pending, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            } catch (AtomicMoveNotSupportedException ignored) {
                Files.move(pending, target, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (Exception error) {
            DrewCraft.LOGGER.debug("Could not record local preload center", error);
        }
    }
}
