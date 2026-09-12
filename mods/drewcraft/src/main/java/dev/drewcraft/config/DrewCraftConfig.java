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

    public static final ModConfigSpec.BooleanValue MTS_VEHICLE_ADAPTER = BUILDER
            .comment("Enable Immersive Vehicles / MTS integration once implemented and validated.")
            .define("integrations.mtsVehicle", false);

    public static final ModConfigSpec.BooleanValue STRATEGIC_KERNEL = BUILDER
            .comment("Enable DrewCraft strategic-world persistence/simulation once implemented.")
            .define("features.strategicKernel", false);

    public static final ModConfigSpec.BooleanValue RADAR = BUILDER
            .comment("Enable DrewCraft radar once implemented.")
            .define("features.radar", false);

    public static final ModConfigSpec SPEC = BUILDER.build();

    private DrewCraftConfig() {
    }

    public static String integrationSummary() {
        return "terrain=" + TERRAIN_DIFFUSION_ADAPTER.get()
                + ", atmosphere=" + PROJECT_ATMOSPHERE_ADAPTER.get()
                + ", create=" + CREATE_POWER_ADAPTER.get()
                + ", mts=" + MTS_VEHICLE_ADAPTER.get()
                + ", strategic=" + STRATEGIC_KERNEL.get()
                + ", radar=" + RADAR.get();
    }
}
