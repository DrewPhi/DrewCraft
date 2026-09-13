package dev.drewcraft.strategic.production;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.drewcraft.DrewCraft;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.herd.WildHerdDescriptor;
import dev.drewcraft.strategic.herd.WildHerdRegistration;
import dev.drewcraft.strategic.source.GeneratedSourceRegistration;
import dev.drewcraft.strategic.source.SourceClass;
import dev.drewcraft.strategic.source.SourceCorePosition;
import dev.drewcraft.strategic.source.SourceDescriptor;
import java.io.IOException;
import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.neoforge.event.level.ChunkEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * Imports the offline-built production strategic seed file. This class never searches structures,
 * animals, or distant chunks. Source authority is registered from the file at server start; the
 * physical Source Core is placed only when its exact chunk naturally loads.
 */
public final class ProductionStrategicSeedRuntime {
    public static final String FILE_NAME = "drewcraft-strategic-seeds.json";
    private static final int SCHEMA_VERSION = 1;
    private static final Map<String, Map<Long, List<SourceDescriptor>>> SOURCES_BY_CHUNK = new HashMap<>();

    private ProductionStrategicSeedRuntime() {
    }

    public static synchronized void onServerStarted(ServerStartedEvent event) {
        MinecraftServer server = event.getServer();
        SOURCES_BY_CHUNK.clear();
        Path file = server.getWorldPath(LevelResource.ROOT).resolve(FILE_NAME);
        if (!Files.isRegularFile(file)) {
            DrewCraft.LOGGER.warn("Production strategic seed file not found at {}; production sources/herds were not imported", file);
            return;
        }

        try (Reader reader = Files.newBufferedReader(file)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            if (requiredInt(root, "schemaVersion") != SCHEMA_VERSION) {
                throw new IllegalStateException("unsupported production strategic seed schema");
            }
            String worldId = requiredString(root, "worldId");
            int worldRevision = requiredInt(root, "worldRevision");
            DrewCraftSavedData data = DrewCraftSavedData.get(server);
            int sources = importSources(server, data, root.getAsJsonArray("sources"));
            int herds = importHerds(data, root.getAsJsonArray("herds"), server.overworld().getGameTime());
            DrewCraft.LOGGER.info(
                    "Imported DrewCraft production seeds world={} revision={} sources={} herds={}",
                    worldId, worldRevision, sources, herds
            );
        } catch (Exception ex) {
            SOURCES_BY_CHUNK.clear();
            DrewCraft.LOGGER.error("Failed to import production strategic seeds from {}", file, ex);
        }
    }

    public static synchronized void onChunkLoad(ChunkEvent.Load event) {
        if (!(event.getLevel() instanceof ServerLevel level)) return;
        String dimension = level.dimension().location().toString();
        Map<Long, List<SourceDescriptor>> byChunk = SOURCES_BY_CHUNK.get(dimension);
        if (byChunk == null) return;
        ChunkPos pos = event.getChunk().getPos();
        List<SourceDescriptor> descriptors = byChunk.get(ChunkPos.asLong(pos.x, pos.z));
        if (descriptors == null) return;
        for (SourceDescriptor descriptor : descriptors) {
            GeneratedSourceRegistration.RegistrationResult result = GeneratedSourceRegistration.register(level, descriptor);
            if (!result.corePlaced() && !"already_cleared".equals(result.status())) {
                DrewCraft.LOGGER.debug("Production source {} core placement status={}", result.source().sourceId(), result.status());
            }
        }
    }

    private static int importSources(MinecraftServer server, DrewCraftSavedData data, JsonArray items) {
        if (items == null) return 0;
        int count = 0;
        long gameTime = server.overworld().getGameTime();
        for (JsonElement element : items) {
            JsonObject item = element.getAsJsonObject();
            String dimension = requiredString(item, "dimension");
            JsonObject anchor = item.getAsJsonObject("anchor");
            JsonObject core = item.getAsJsonObject("core");
            SourceDescriptor descriptor = new SourceDescriptor(
                    dimension,
                    requiredString(item, "structureId"),
                    requiredInt(anchor, "x"), requiredInt(anchor, "y"), requiredInt(anchor, "z"),
                    new SourceCorePosition(
                            dimension,
                            requiredInt(core, "x"), requiredInt(core, "y"), requiredInt(core, "z")
                    ),
                    SourceClass.valueOf(requiredString(item, "sourceClass")),
                    requiredString(item, "factionId")
            );
            data.discoverSource(descriptor, gameTime);
            long chunkKey = ChunkPos.asLong(descriptor.corePosition().x() >> 4, descriptor.corePosition().z() >> 4);
            SOURCES_BY_CHUNK
                    .computeIfAbsent(dimension, ignored -> new HashMap<>())
                    .computeIfAbsent(chunkKey, ignored -> new ArrayList<>())
                    .add(descriptor);
            count++;
        }
        return count;
    }

    private static int importHerds(DrewCraftSavedData data, JsonArray items, long gameTime) {
        if (items == null) return 0;
        int count = 0;
        for (JsonElement element : items) {
            JsonObject item = element.getAsJsonObject();
            JsonObject origin = item.getAsJsonObject("origin");
            JsonObject destination = item.getAsJsonObject("destination");
            WildHerdDescriptor descriptor = new WildHerdDescriptor(
                    requiredString(item, "dimension"),
                    requiredString(item, "species"),
                    requiredInt(origin, "x"), requiredInt(origin, "z"),
                    requiredInt(destination, "x"), requiredInt(destination, "z"),
                    requiredInt(item, "count"),
                    requiredDouble(item, "speedBlocksPerSecond")
            );
            WildHerdRegistration.RegistrationResult result = WildHerdRegistration.register(data, descriptor, gameTime);
            if (result.success()) count++;
            else DrewCraft.LOGGER.warn("Could not register production herd {}: {}", descriptor.stableHerdId(), result.status());
        }
        return count;
    }

    private static String requiredString(JsonObject object, String name) {
        if (object == null || !object.has(name) || !object.get(name).isJsonPrimitive()) {
            throw new IllegalArgumentException("missing string field " + name);
        }
        String value = object.get(name).getAsString();
        if (value.isBlank()) throw new IllegalArgumentException("blank string field " + name);
        return value;
    }

    private static int requiredInt(JsonObject object, String name) {
        if (object == null || !object.has(name)) throw new IllegalArgumentException("missing integer field " + name);
        return object.get(name).getAsInt();
    }

    private static double requiredDouble(JsonObject object, String name) {
        if (object == null || !object.has(name)) throw new IllegalArgumentException("missing numeric field " + name);
        double value = object.get(name).getAsDouble();
        if (!Double.isFinite(value)) throw new IllegalArgumentException("non-finite numeric field " + name);
        return value;
    }
}
