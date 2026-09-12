package dev.drewcraft.service.power;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;

/**
 * DrewCraft-owned power contract. V1 models Create as kinetic power, not generic electricity.
 */
public interface PowerService {
    String providerId();

    PowerSample sample(ServerLevel level, BlockPos position);
}
