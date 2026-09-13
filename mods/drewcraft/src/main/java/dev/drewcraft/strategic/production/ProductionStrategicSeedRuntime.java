package dev.drewcraft.strategic.production;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.drewcraft.DrewCraft;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.herd.WildHerdDescriptor;
import dev.drewcraft.strategic.herd.WildHerdRegistration;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.objective.StrategicObjectiveCatalog;
import dev.drewcraft.strategic.routing.StrategicCell;
import dev.drewcraft.strategic.routing.StrategicRoutingService;
import dev.drewcraft.strategic.routing.StrategicTerrainClass;
import dev.drewcraft.strategic.source.GeneratedSourceRegistration;
import dev.drewcraft.strategic.source.SourceClass;
import dev.drewcraft.strategic.source.SourceCorePosition;
import dev.drewcraft.strategic.source.SourceDescriptor;
import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.neoforge.event.level.ChunkEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;

/**
 * Imports the offline-built production strategic seed file. This class never searches structures,
 * animals, or distant chunks. Source authority is registered from the file at server start; the
 * physical Source Core is placed only when its exact chunk is already loaded or naturally loads.
 */
public final class ProductionStrategicSeedRuntime {
    public static final String FILE_NAME = "drewcraft-strategic-seeds.json";
    public static final String WORLD_METADATA_FILE_NAME = "drewcraft-world.json";
    private static final int SCHEMA_VERSION = 1;
    private static final Map<String, Map<Long, List<SourceDescriptor>>> SOURCES_BY_CHUNK = new HashMap<>();

    private ProductionStrategicSeedRuntime() {
    }

    public static synchronized void onServerStarted(ServerStartedEvent event) {
        MinecraftServer server = event.getServer();
        SOURCES_BY_CHUNK.clear();
        Path worldRoot = server.getWorldPath(LevelResource.ROOT);
        Path file = worldRoot.resolve(FILE_NAME);
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
            validateWorldIdentity(worldRoot.resolve(WORLD_METADATA_FILE_NAME), worldId, worldRevision);

            DrewCraftSavedData data = DrewCraftSavedData.get(server);
            TerrainSeed terrain = parseTerrain(root.getAsJsonObject("terrain"));
            List<StrategicObjectiveCatalog.StrategicObjective> objectiveSeeds = parseObjectives(root.getAsJsonArray("objectives"));
            List<SourceDescriptor> sourceSeeds = parseSources(root.getAsJsonArray("sources"));
            List<WildHerdDescriptor> herdSeeds = parseHerds(root.getAsJsonArray("herds"));
            validateSourcesAgainstPersistentState(data, sourceSeeds);

            StrategicRoutingService.reset();
            int terrainCells = importTerrain(terrain);
            StrategicObjectiveCatalog.replace(objectiveSeeds);
            int sources = importSources(server, data, sourceSeeds);
            int herds = importHerds(data, herdSeeds, server.overworld().getGameTime());
            DrewCraft.LOGGER.info(
                    "Imported DrewCraft production seeds world={} revision={} sources={} herds={} objectives={} terrainCells={}",
                    worldId, worldRevision, sources, herds, objectiveSeeds.size(), terrainCells
            );
        } catch (Exception ex) {
            SOURCES_BY_CHUNK.clear();
            StrategicObjectiveCatalog.clear();
            StrategicRoutingService.reset();
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
            placeCoreIfLoaded(level, descriptor);
        }
    }

    public static synchronized void onServerStopped(ServerStoppedEvent event) {
        SOURCES_BY_CHUNK.clear();
        StrategicObjectiveCatalog.clear();
    }

    private static TerrainSeed parseTerrain(JsonObject terrain) {
        if (terrain == null) return new TerrainSeed(64, Map.of());
        int cellSize = requiredInt(terrain, "cellSizeBlocks");
        JsonArray cells = terrain.getAsJsonArray("cells");
        Map<StrategicCell, StrategicTerrainClass> parsed = new HashMap<>();
        if (cells != null) {
            for (JsonElement element : cells) {
                JsonObject cell = element.getAsJsonObject();
                StrategicCell key = new StrategicCell(requiredString(cell, "dimension"), requiredInt(cell, "x"), requiredInt(cell, "z"));
                if (parsed.put(key, StrategicTerrainClass.valueOf(requiredString(cell, "terrainClass"))) != null) {
                    throw new IllegalArgumentException("duplicate strategic terrain cell " + key);
                }
            }
        }
        return new TerrainSeed(cellSize, parsed);
    }

    private static int importTerrain(TerrainSeed terrain) {
        if (terrain.cellSize() != StrategicRoutingService.terrainCosts().cellSizeBlocks()) {
            throw new IllegalStateException("production terrain cell size does not match server routing configuration");
        }
        terrain.cells().forEach(StrategicRoutingService.terrainCosts()::put);
        return terrain.cells().size();
    }

    private static List<StrategicObjectiveCatalog.StrategicObjective> parseObjectives(JsonArray items) {
        List<StrategicObjectiveCatalog.StrategicObjective> objectives = new ArrayList<>();
        if (items != null) {
            for (JsonElement element : items) {
                JsonObject item = element.getAsJsonObject();
                JsonObject position = item.getAsJsonObject("position");
                objectives.add(new StrategicObjectiveCatalog.StrategicObjective(
                        requiredString(item, "id"), requiredString(item, "kind"),
                        new StrategicPosition(requiredString(item, "dimension"),
                                requiredDouble(position, "x"), requiredDouble(position, "z"))
                ));
            }
        }
        if (objectives.stream().map(StrategicObjectiveCatalog.StrategicObjective::id).distinct().count() != objectives.size()) {
            throw new IllegalArgumentException("duplicate strategic objective ID");
        }
        return objectives;
    }

    private static List<SourceDescriptor> parseSources(JsonArray items) {
        List<SourceDescriptor> descriptors = new ArrayList<>();
        if (items == null) return descriptors;
        for (JsonElement element : items) {
            JsonObject item = element.getAsJsonObject();
            String dimension = requiredString(item, "dimension");
            JsonObject anchor = item.getAsJsonObject("anchor");
            JsonObject core = item.getAsJsonObject("core");
            descriptors.add(new SourceDescriptor(
                    dimension,
                    requiredString(item, "structureId"),
                    requiredInt(anchor, "x"), requiredInt(anchor, "y"), requiredInt(anchor, "z"),
                    new SourceCorePosition(
                            dimension,
                            requiredInt(core, "x"), requiredInt(core, "y"), requiredInt(core, "z")
                    ),
                    SourceClass.valueOf(requiredString(item, "sourceClass")),
                    requiredString(item, "factionId")
            ));
        }
        Set<java.util.UUID> ids = new HashSet<>();
        Set<SourceCorePosition> cores = new HashSet<>();
        for (SourceDescriptor descriptor : descriptors) {
            if (!ids.add(descriptor.stableSourceId()) || !cores.add(descriptor.corePosition())) {
                throw new IllegalArgumentException("duplicate source identity/core in production seeds");
            }
        }
        return descriptors;
    }

    private static void validateSourcesAgainstPersistentState(DrewCraftSavedData data, List<SourceDescriptor> descriptors) {
        for (SourceDescriptor descriptor : descriptors) {
            data.sourceRecord(descriptor.stableSourceId()).ifPresent(existing -> {
                if (!existing.identityMatches(descriptor)) throw new IllegalStateException("source identity conflict");
            });
            data.sourceAtCore(descriptor.corePosition()).ifPresent(existing -> {
                if (!existing.sourceId().equals(descriptor.stableSourceId())) throw new IllegalStateException("source core conflict");
            });
        }
    }

    private static int importSources(MinecraftServer server, DrewCraftSavedData data, List<SourceDescriptor> descriptors) {
        int count = 0;
        long gameTime = server.overworld().getGameTime();
        for (SourceDescriptor descriptor : descriptors) {
            data.discoverSource(descriptor, gameTime);
            String dimension = descriptor.dimension();
            long chunkKey = ChunkPos.asLong(descriptor.corePosition().x() >> 4, descriptor.corePosition().z() >> 4);
            SOURCES_BY_CHUNK
                    .computeIfAbsent(dimension, ignored -> new HashMap<>())
                    .computeIfAbsent(chunkKey, ignored -> new ArrayList<>())
                    .add(descriptor);

            // Spawn/forced chunks may have loaded before ServerStartedEvent. Do not wait for a
            // future unload/reload: place the core now only if its exact chunk is already loaded.
            ServerLevel level = levelFor(server, dimension);
            if (level != null) placeCoreIfLoaded(level, descriptor);
            count++;
        }
        return count;
    }

    private static void placeCoreIfLoaded(ServerLevel level, SourceDescriptor descriptor) {
        SourceCorePosition core = descriptor.corePosition();
        BlockPos corePos = new BlockPos(core.x(), core.y(), core.z());
        if (!level.hasChunkAt(corePos)) return;
        GeneratedSourceRegistration.RegistrationResult result = GeneratedSourceRegistration.register(level, descriptor);
        if (!result.corePlaced() && !"already_cleared".equals(result.status())) {
            DrewCraft.LOGGER.debug("Production source {} core placement status={}", result.source().sourceId(), result.status());
        }
    }

    private static List<WildHerdDescriptor> parseHerds(JsonArray items) {
        List<WildHerdDescriptor> descriptors = new ArrayList<>();
        if (items == null) return descriptors;
        for (JsonElement element : items) {
            JsonObject item = element.getAsJsonObject();
            JsonObject origin = item.getAsJsonObject("origin");
            JsonObject destination = item.getAsJsonObject("destination");
            descriptors.add(new WildHerdDescriptor(
                    requiredString(item, "dimension"),
                    requiredString(item, "species"),
                    requiredInt(origin, "x"), requiredInt(origin, "z"),
                    requiredInt(destination, "x"), requiredInt(destination, "z"),
                    requiredInt(item, "count"),
                    requiredDouble(item, "speedBlocksPerSecond")
            ));
        }
        if (descriptors.stream().map(WildHerdDescriptor::stableHerdId).distinct().count() != descriptors.size()) {
            throw new IllegalArgumentException("duplicate production herd route");
        }
        return descriptors;
    }

    private static int importHerds(DrewCraftSavedData data, List<WildHerdDescriptor> descriptors, long gameTime) {
        int count = 0;
        for (WildHerdDescriptor descriptor : descriptors) {
            WildHerdRegistration.RegistrationResult result = WildHerdRegistration.register(data, descriptor, gameTime);
            if (result.success()) count++;
            else DrewCraft.LOGGER.warn("Could not register production herd {}: {}", descriptor.stableHerdId(), result.status());
        }
        return count;
    }

    private record TerrainSeed(int cellSize, Map<StrategicCell, StrategicTerrainClass> cells) { }

    private static void validateWorldIdentity(Path metadataFile, String expectedWorldId, int expectedRevision) throws Exception {
        if (!Files.isRegularFile(metadataFile)) {
            throw new IllegalStateException("production world metadata is missing: " + metadataFile);
        }
        try (Reader reader = Files.newBufferedReader(metadataFile)) {
            JsonObject metadata = JsonParser.parseReader(reader).getAsJsonObject();
            if (requiredInt(metadata, "schemaVersion") != SCHEMA_VERSION) {
                throw new IllegalStateException("unsupported production world metadata schema");
            }
            String actualWorldId = requiredString(metadata, "worldId");
            int actualRevision = requiredInt(metadata, "worldRevision");
            if (!expectedWorldId.equals(actualWorldId) || expectedRevision != actualRevision) {
                throw new IllegalStateException(
                        "strategic seed/world identity mismatch: seeds=" + expectedWorldId + "@" + expectedRevision
                                + " world=" + actualWorldId + "@" + actualRevision
                );
            }
        }
    }

    private static ServerLevel levelFor(MinecraftServer server, String dimensionId) {
        for (ServerLevel level : server.getAllLevels()) {
            if (level.dimension().location().toString().equals(dimensionId)) return level;
        }
        return null;
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
