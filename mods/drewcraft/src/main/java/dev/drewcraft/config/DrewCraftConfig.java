package dev.drewcraft.config;

import net.neoforged.neoforge.common.ModConfigSpec;

public final class DrewCraftConfig {
    private static final ModConfigSpec.Builder BUILDER = new ModConfigSpec.Builder();

    public static final ModConfigSpec.BooleanValue TERRAIN_DIFFUSION_ADAPTER = BUILDER
            .comment("Enable the Terrain Diffusion Plus realized-world adapter. Sampling never force-loads chunks or invokes neural inference.")
            .define("integrations.terrainDiffusion", true);

    public static final ModConfigSpec.BooleanValue PROJECT_ATMOSPHERE_ADAPTER = BUILDER
            .comment("Post-V1: enable the read-only Project Atmosphere public API adapter. Disabled in the focused V1.")
            .define("integrations.projectAtmosphere", false);

    public static final ModConfigSpec.BooleanValue CREATE_POWER_ADAPTER = BUILDER
            .comment("Enable the read-only Create kinetic-power adapter used by DrewCraft machinery.")
            .define("integrations.createPower", true);

    public static final ModConfigSpec.BooleanValue CREATE_RADARS_ADAPTER = BUILDER
            .comment("Post-V1: enable DrewCraft weather/terrain integration with Create: Radars. The upstream radar mod can still run independently.")
            .define("integrations.createRadars", false);

    public static final ModConfigSpec.BooleanValue MTS_VEHICLE_ADAPTER = BUILDER
            .comment("Enable the read-only Immersive Vehicles / MTS vehicle observation adapter.")
            .define("integrations.mtsVehicle", true);

    public static final ModConfigSpec.BooleanValue AVIATION_WEATHER = BUILDER
            .comment("Post-V1: enable server-authoritative Project Atmosphere wind/turbulence in MTS aircraft aerodynamics.")
            .define("features.aviationWeather", false);

    public static final ModConfigSpec.BooleanValue STRATEGIC_KERNEL = BUILDER
            .comment("Post-V1: enable the DrewCraft strategic-world persistence/simulation kernel.")
            .define("features.strategicKernel", false);

    public static final ModConfigSpec.BooleanValue STRATEGIC_HERDS = BUILDER
            .comment("Post-V1: enable movement/materialization of explicitly registered strategic wild herds. Disabling preserves records and ordinary Minecraft ecology.")
            .define("features.strategicHerds", false);

    public static final ModConfigSpec.IntValue STRATEGIC_SCHEDULER_INTERVAL_TICKS = BUILDER
            .comment("Ticks between coarse strategic simulation cycles. No strategic pathfinding or entity AI runs here.")
            .defineInRange("strategic.schedulerIntervalTicks", 100, 20, 1200);

    public static final ModConfigSpec.IntValue STRATEGIC_MAX_GROUPS_PER_CYCLE = BUILDER
            .comment("Hard cap on strategic groups processed in one scheduler cycle.")
            .defineInRange("strategic.maxGroupsPerCycle", 64, 1, 10000);

    public static final ModConfigSpec.DoubleValue STRATEGIC_MAX_MILLIS_PER_CYCLE = BUILDER
            .comment("Soft CPU-time budget for one coarse strategic scheduler cycle.")
            .defineInRange("strategic.maxMillisPerCycle", 5.0, 0.1, 100.0);

    public static final ModConfigSpec.DoubleValue STRATEGIC_MAX_CATCHUP_SECONDS = BUILDER
            .comment("Maximum elapsed strategic movement applied to a group in one cycle; excess is intentionally discarded.")
            .defineInRange("strategic.maxCatchupSeconds", 300.0, 1.0, 86400.0);

    public static final ModConfigSpec.IntValue STRATEGIC_ROUTING_CELL_SIZE_BLOCKS = BUILDER
            .comment("Coarse strategic routing cell width. Routing never operates at per-block world resolution.")
            .defineInRange("strategic.routing.cellSizeBlocks", 64, 16, 512);

    public static final ModConfigSpec.IntValue STRATEGIC_ROUTING_MAX_EXPANDED_NODES = BUILDER
            .comment("Hard A* node-expansion cap for a single strategic route calculation.")
            .defineInRange("strategic.routing.maxExpandedNodes", 20000, 100, 250000);

    public static final ModConfigSpec.IntValue STRATEGIC_ROUTING_DETOUR_PADDING_CELLS = BUILDER
            .comment("Extra coarse cells allowed around the start/destination bounding box for route detours.")
            .defineInRange("strategic.routing.detourPaddingCells", 32, 0, 512);

    public static final ModConfigSpec.IntValue STRATEGIC_ROUTING_CACHE_ENTRIES = BUILDER
            .comment("Maximum number of solved strategic route templates retained in the in-memory LRU cache.")
            .defineInRange("strategic.routing.cacheEntries", 512, 1, 10000);

    public static final ModConfigSpec.IntValue STRATEGIC_MATERIALIZATION_INTERVAL_TICKS = BUILDER
            .comment("Ticks between bounded checks for nearby strategic materialization/reconciliation.")
            .defineInRange("strategic.materialization.intervalTicks", 20, 5, 200);

    public static final ModConfigSpec.IntValue STRATEGIC_MATERIALIZATION_RADIUS_BLOCKS = BUILDER
            .comment("Player proximity radius at which an abstract strategic group may materialize.")
            .defineInRange("strategic.materialization.radiusBlocks", 160, 32, 512);

    public static final ModConfigSpec.IntValue STRATEGIC_DEMATERIALIZATION_RADIUS_BLOCKS = BUILDER
            .comment("Larger hysteresis radius outside which tactical entities may collapse back to strategic state.")
            .defineInRange("strategic.materialization.dematerializationRadiusBlocks", 224, 48, 768);

    public static final ModConfigSpec.IntValue STRATEGIC_DEMATERIALIZATION_GRACE_TICKS = BUILDER
            .comment("Grace period after the last nearby player before encounter reconciliation.")
            .defineInRange("strategic.materialization.graceTicks", 200, 0, 2400);

    public static final ModConfigSpec.IntValue STRATEGIC_MAX_ACTIVE_ENTITIES_PER_ENCOUNTER = BUILDER
            .comment("Hard cap on simultaneously loaded entities representing one strategic group. Remaining strength stays abstract and can enter later waves.")
            .defineInRange("strategic.materialization.maxActiveEntities", 64, 1, 256);

    public static final ModConfigSpec.IntValue STRATEGIC_MAX_NEW_ENTITIES_PER_CYCLE = BUILDER
            .comment("Global hard cap on successful strategic entity spawns in one materialization cycle across all encounters.")
            .defineInRange("strategic.materialization.maxNewEntitiesPerCycle", 128, 1, 1024);

    public static final ModConfigSpec.IntValue STRATEGIC_MAX_ENCOUNTERS_PROCESSED_PER_CYCLE = BUILDER
            .comment("Hard cap on encounter records inspected in one materialization cycle.")
            .defineInRange("strategic.materialization.maxEncountersPerCycle", 32, 1, 512);

    public static final ModConfigSpec.IntValue STRATEGIC_SOURCE_INTERVAL_TICKS = BUILDER
            .comment("Ticks between bounded hostile-source production cycles. Sources are persistent records; this never scans distant chunks.")
            .defineInRange("strategic.sources.intervalTicks", 200, 20, 2400);

    public static final ModConfigSpec.IntValue STRATEGIC_MAX_SOURCES_PER_CYCLE = BUILDER
            .comment("Hard cap on persistent hostile sources inspected in one production cycle.")
            .defineInRange("strategic.sources.maxSourcesPerCycle", 16, 1, 1024);

    public static final ModConfigSpec.IntValue STRATEGIC_MAX_LAUNCHES_PER_CYCLE = BUILDER
            .comment("Hard cap on new strategic groups committed by hostile sources in one production cycle.")
            .defineInRange("strategic.sources.maxLaunchesPerCycle", 4, 1, 128);

    public static final ModConfigSpec.DoubleValue STRATEGIC_SOURCE_MAX_MILLIS_PER_CYCLE = BUILDER
            .comment("Soft wall-clock budget for source route planning in one production cycle.")
            .defineInRange("strategic.sources.maxMillisPerCycle", 8.0, 0.1, 100.0);

    public static final ModConfigSpec.IntValue STRATEGIC_SOURCE_ROUTE_RETRY_TICKS = BUILDER
            .comment("Backoff after a source cannot obtain a bounded strategic route. Population is not consumed.")
            .defineInRange("strategic.sources.routeRetryTicks", 1200, 20, 24000);

    public static final ModConfigSpec.BooleanValue STRATEGIC_SIEGE = BUILDER
            .comment("Post-V1: enable path-first bounded tactical siege behavior for eligible materialized raids/armies.")
            .define("features.strategicSiege", false);

    public static final ModConfigSpec.IntValue STRATEGIC_SIEGE_INTERVAL_TICKS = BUILDER
            .comment("Ticks between bounded siege checks. Siege logic only runs for materialized loaded encounters.")
            .defineInRange("strategic.siege.intervalTicks", 20, 5, 200);

    public static final ModConfigSpec.IntValue STRATEGIC_SIEGE_RADIUS_BLOCKS = BUILDER
            .comment("Half-width of the already-loaded local siege-planning snapshot.")
            .defineInRange("strategic.siege.radiusBlocks", 12, 4, 32);

    public static final ModConfigSpec.IntValue STRATEGIC_SIEGE_BLOCKED_CHECKS = BUILDER
            .comment("Consecutive failed ordinary-navigation checks required before breach planning is allowed.")
            .defineInRange("strategic.siege.blockedChecksBeforePlan", 3, 1, 20);

    public static final ModConfigSpec.IntValue STRATEGIC_SIEGE_MAX_ENCOUNTERS_PER_CYCLE = BUILDER
            .comment("Hard cap on siege-eligible encounter records inspected per siege cycle.")
            .defineInRange("strategic.siege.maxEncountersPerCycle", 8, 1, 64);

    public static final ModConfigSpec.IntValue STRATEGIC_SIEGE_MAX_EXPANDED_NODES = BUILDER
            .comment("Hard local planner node-expansion bound for a single siege plan.")
            .defineInRange("strategic.siege.maxExpandedNodes", 1200, 32, 10000);

    public static final ModConfigSpec.IntValue STRATEGIC_SIEGE_MAX_BREACH_BLOCKS = BUILDER
            .comment("Maximum number of barrier cells permitted in one constrained breach corridor.")
            .defineInRange("strategic.siege.maxBreachBlocks", 4, 1, 12);

    public static final ModConfigSpec.IntValue STRATEGIC_SIEGE_BREAK_COOLDOWN_TICKS = BUILDER
            .comment("Minimum ticks between deliberate siege block breaks for one encounter.")
            .defineInRange("strategic.siege.breakCooldownTicks", 30, 5, 400);

    public static final ModConfigSpec.BooleanValue RADAR = BUILDER
            .comment("Post-V1: enable DrewCraft radar sensing and weather/terrain integration. Upstream Create: Radars remains independent.")
            .define("features.radar", false);

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
                + ", herds=" + STRATEGIC_HERDS.get()
                + ", siege=" + STRATEGIC_SIEGE.get()
                + ", radar=" + RADAR.get();
    }
}
