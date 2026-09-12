package dev.drewcraft.adapter.terrain;

import dev.drewcraft.service.terrain.TerrainSample;
import dev.drewcraft.service.terrain.TerrainService;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.levelgen.Heightmap;

/**
 * Terrain Diffusion Plus adapter for already-realized terrain.
 *
 * This adapter intentionally never calls Terrain Diffusion's inference pipeline and never
 * force-loads an unloaded chunk. It samples the Minecraft world state produced by the pinned
 * Terrain Diffusion Plus generator, keeping neural generation out of tick-time consumers such
 * as aircraft physics and radar.
 */
public final class TerrainDiffusionTerrainService implements TerrainService {
    public static final String PROVIDER_ID = "terrain_diffusion_plus.realized_world";

    @Override
    public String providerId() {
        return PROVIDER_ID;
    }

    @Override
    public TerrainSample sample(ServerLevel level, BlockPos position) {
        if (level == null || position == null) {
            return TerrainSample.unavailable(PROVIDER_ID, BlockPos.ZERO, "invalid_request");
        }

        int chunkX = position.getX() >> 4;
        int chunkZ = position.getZ() >> 4;
        if (!level.hasChunk(chunkX, chunkZ)) {
            return TerrainSample.unavailable(PROVIDER_ID, position, "chunk_not_loaded_no_force_load");
        }

        int firstAirY = level.getHeight(Heightmap.Types.WORLD_SURFACE, position.getX(), position.getZ());
        int surfaceY = Math.max(level.getMinBuildHeight(), firstAirY - 1);
        BlockPos surfacePos = new BlockPos(position.getX(), surfaceY, position.getZ());

        String biomeId = level.getBiome(surfacePos)
                .unwrapKey()
                .map(key -> key.location().toString())
                .orElse("unregistered");
        String surfaceBlockId = BuiltInRegistries.BLOCK
                .getKey(level.getBlockState(surfacePos).getBlock())
                .toString();

        return TerrainSample.available(
                PROVIDER_ID,
                position,
                surfaceY,
                biomeId,
                surfaceBlockId,
                level.getSeaLevel(),
                "realized_world_sample_no_inference"
        );
    }
}
