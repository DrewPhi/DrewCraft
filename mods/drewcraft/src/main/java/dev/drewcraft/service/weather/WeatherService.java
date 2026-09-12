package dev.drewcraft.service.weather;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;

/**
 * DrewCraft-owned atmospheric query contract.
 *
 * Units are part of the contract: Celsius, metres/second and radians.
 * Pressure and humidity may be absent when the upstream provider does not expose them.
 */
public interface WeatherService {
    String providerId();

    WeatherSample sample(ServerLevel level, BlockPos position);
}
