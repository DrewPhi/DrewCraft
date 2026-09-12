package dev.drewcraft.config;

import net.neoforged.neoforge.common.ModConfigSpec;

public final class DrewCraftConfig {
    private static final ModConfigSpec.Builder BUILDER = new ModConfigSpec.Builder();

    public static final ModConfigSpec.BooleanValue TERRAIN_DIFFUSION_ADAPTER = BUILDER
            .comment("Enable the Terrain Diffusion Plus realized-world adapter. Sampling never force-loads chunks or invokes neural inference.")
            .define("integrations.terrainDiffusion", true);

    public static final ModConfigSpec.BooleanValue PROJECT_ATMOSPHERE_ADAPTER = BUILDER
            .comment("Enable the read-only Project Atmosphere public API adapter. The adapter fails closed if the upstream API shape changes.")
            .define("integrations.projectAtmosphere", true);

    public static final ModConfigSpec.BooleanValue CREATE_POWER_ADAPTER = BUILDER
            .comment("Enable the read-only Create kinetic-power adapter used by DrewCraft machinery.")
            .define("integrations.createPower", true);

    public static final ModConfigSpec.BooleanValue CREATE_RADARS_ADAPTER = BUILDER
            .comment("Enable DrewCraft weather/terrain integration with the official Create: Radars monitor and ground radar.")
            .define("integrations.createRadars", true);

    public static final ModConfigSpec.BooleanValue MTS_VEHICLE_ADAPTER = BUILDER
            .comment("Enable the read-only Immersive Vehicles / MTS vehicle observation adapter.")
            .define("integrations.mtsVehicle", true);

    public static final ModConfigSpec.BooleanValue AVIATION_WEATHER = BUILDER
            .comment("Enable server-authoritative Project Atmosphere wind/turbulence in MTS aircraft aerodynamics.")
            .define("features.aviationWeather", true);

    public static final ModConfigSpec.BooleanValue STRATEGIC_KERNEL = BUILDER
            .comment("Enable DrewCraft strategic-world persistence/simulation once implemented.")
            .define("features.strategicKernel", false);

    public static final ModConfigSpec.BooleanValue RADAR = BUILDER
            .comment("Enable DrewCraft radar sensing and Create: Radars weather/terrain integration.")
            .define("features.radar", true);

    public static final ModConfigSpec SPEC = BUILDER.build();

    private DrewCraftConfig() {
    }

    public static String integrationSummary() {
        return "terrain=" + TERRAIN_DIFFUSION_ADAPTER.get()
                + ", atmosphere=" + PROJECT_ATMOSPHERE_ADAPTER.get()
                + ", create=" + CREATE_POWER_ADAPTER.get()
                + ", createRadars=" + CREATE_RADARS_ADAPTER.get()
                + ", mts=" + MTS_VEHICLE_ADAPTER.get()
                + ", aviationWeather=" + AVIATION_WEATHER.get()
                + ", strategic=" + STRATEGIC_KERNEL.get()
                + ", radar=" + RADAR.get();
    }
}
