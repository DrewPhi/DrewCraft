package dev.drewcraft.service;

import dev.drewcraft.adapter.atmosphere.ProjectAtmosphereWeatherService;
import dev.drewcraft.adapter.terrain.TerrainDiffusionTerrainService;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.service.power.PowerSample;
import dev.drewcraft.service.power.PowerService;
import dev.drewcraft.service.terrain.TerrainSample;
import dev.drewcraft.service.terrain.TerrainService;
import dev.drewcraft.service.vehicle.VehicleQueryResult;
import dev.drewcraft.service.vehicle.VehicleService;
import dev.drewcraft.service.weather.WeatherSample;
import dev.drewcraft.service.weather.WeatherService;
import net.neoforged.fml.ModList;

/** Central service selection boundary for DrewCraft integrations. */
public final class DrewCraftServices {
    private static final TerrainService TERRAIN = new TerrainDiffusionTerrainService();

    private static final TerrainService TERRAIN_DISABLED = new TerrainService() {
        @Override
        public String providerId() {
            return TerrainDiffusionTerrainService.PROVIDER_ID;
        }

        @Override
        public TerrainSample sample(net.minecraft.server.level.ServerLevel level, net.minecraft.core.BlockPos position) {
            return TerrainSample.unavailable(providerId(), position, "disabled_by_config");
        }
    };

    private static final WeatherService WEATHER_DISABLED = new WeatherService() {
        @Override
        public String providerId() {
            return ProjectAtmosphereWeatherService.PROVIDER_ID;
        }

        @Override
        public WeatherSample sample(net.minecraft.server.level.ServerLevel level, net.minecraft.core.BlockPos position) {
            return WeatherSample.unavailable(providerId(), position, "disabled_by_config");
        }
    };

    private static final WeatherService WEATHER_MISSING = new WeatherService() {
        @Override
        public String providerId() {
            return ProjectAtmosphereWeatherService.PROVIDER_ID;
        }

        @Override
        public WeatherSample sample(net.minecraft.server.level.ServerLevel level, net.minecraft.core.BlockPos position) {
            return WeatherSample.unavailable(providerId(), position, "projectatmosphere_mod_missing");
        }
    };

    private static final PowerService CREATE_PENDING = new PowerService() {
        @Override
        public String providerId() {
            return "create.kinetic";
        }

        @Override
        public PowerSample sample(net.minecraft.server.level.ServerLevel level, net.minecraft.core.BlockPos position) {
            return PowerSample.unavailable(providerId(), position, "step_6_not_implemented");
        }
    };

    private static final VehicleService MTS_PENDING = new VehicleService() {
        @Override
        public String providerId() {
            return "mts.vehicle";
        }

        @Override
        public VehicleQueryResult query(net.minecraft.server.level.ServerLevel level, net.minecraft.world.phys.Vec3 center, double radiusBlocks) {
            return VehicleQueryResult.unavailable(providerId(), "step_7a_not_implemented");
        }
    };

    private DrewCraftServices() {
    }

    public static TerrainService terrain() {
        return DrewCraftConfig.TERRAIN_DIFFUSION_ADAPTER.get() ? TERRAIN : TERRAIN_DISABLED;
    }

    public static WeatherService weather() {
        if (!DrewCraftConfig.PROJECT_ATMOSPHERE_ADAPTER.get()) {
            return WEATHER_DISABLED;
        }
        if (!ModList.get().isLoaded("projectatmosphere")) {
            return WEATHER_MISSING;
        }
        return AtmosphereHolder.INSTANCE;
    }

    public static PowerService power() {
        return CREATE_PENDING;
    }

    public static VehicleService vehicles() {
        return MTS_PENDING;
    }

    private static final class AtmosphereHolder {
        private static final WeatherService INSTANCE = new ProjectAtmosphereWeatherService();
    }
}
