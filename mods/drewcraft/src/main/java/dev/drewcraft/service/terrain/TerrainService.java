package dev.drewcraft.service.terrain;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;

/**
 * DrewCraft-owned terrain query contract.
 *
 * Third-party terrain-generator types must not escape through this interface.
 */
public interface TerrainService {
    String providerId();

    TerrainSample sample(ServerLevel level, BlockPos position);
}
