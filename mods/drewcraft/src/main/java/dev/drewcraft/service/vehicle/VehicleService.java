package dev.drewcraft.service.vehicle;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

/** DrewCraft-owned vehicle query contract. */
public interface VehicleService {
    String providerId();

    VehicleQueryResult query(ServerLevel level, Vec3 center, double radiusBlocks);
}
