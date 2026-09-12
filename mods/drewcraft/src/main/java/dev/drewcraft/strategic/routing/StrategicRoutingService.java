package dev.drewcraft.strategic.routing;

import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Process-local routing facade. Solved routes are cached by exact endpoints and terrain-map
 * version. Terrain changes therefore invalidate old templates without periodic recomputation.
 */
public final class StrategicRoutingService {
    private static RuntimeState state;

    private StrategicRoutingService() {
    }

    public static synchronized StrategicTerrainCostMap terrainCosts() {
        return runtime().terrain;
    }

    public static synchronized RoutingResult plan(StrategicPosition start, StrategicPosition destination) {
        RuntimeState runtime = runtime();
        RouteKey key = RouteKey.of(start, destination, runtime.terrain.version());
        RouteTemplate cached = runtime.cache.get(key);
        if (cached != null) {
            runtime.cacheHits++;
            StrategicRoute route = cached.instantiate();
            runtime.last = new RoutingStats(
                    true,
                    true,
                    route.waypoints().size(),
                    0,
                    0.0,
                    route.remainingCostFrom(start),
                    "cache_hit"
            );
            return new RoutingResult(true, route, runtime.last);
        }

        runtime.cacheMisses++;
        StrategicRoutePlanner planner = new StrategicRoutePlanner(
                runtime.terrain,
                DrewCraftConfig.STRATEGIC_ROUTING_MAX_EXPANDED_NODES.get(),
                DrewCraftConfig.STRATEGIC_ROUTING_DETOUR_PADDING_CELLS.get()
        );
        StrategicRoutePlanner.PlanResult planned = planner.plan(start, destination);
        if (!planned.success()) {
            runtime.failures++;
            runtime.last = new RoutingStats(
                    false,
                    false,
                    0,
                    planned.expandedNodes(),
                    planned.elapsedMillis(),
                    Double.POSITIVE_INFINITY,
                    planned.status()
            );
            return new RoutingResult(false, null, runtime.last);
        }

        runtime.successes++;
        RouteTemplate template = RouteTemplate.from(planned.route());
        runtime.cache.put(key, template);
        trim(runtime);
        runtime.last = new RoutingStats(
                true,
                false,
                planned.route().waypoints().size(),
                planned.expandedNodes(),
                planned.elapsedMillis(),
                planned.weightedCost(),
                planned.status()
        );
        return new RoutingResult(true, template.instantiate(), runtime.last);
    }

    public static synchronized ServiceStats stats() {
        RuntimeState runtime = runtime();
        return new ServiceStats(
                runtime.terrain.cellSizeBlocks(),
                runtime.terrain.knownCellCount(),
                runtime.terrain.version(),
                runtime.cache.size(),
                runtime.cacheHits,
                runtime.cacheMisses,
                runtime.successes,
                runtime.failures,
                runtime.last
        );
    }

    /** Clears only solved route templates; terrain-cost knowledge remains intact. */
    public static synchronized void invalidateRoutes() {
        runtime().cache.clear();
    }

    /** Test/admin reset. Changing routing cell size also recreates state automatically. */
    public static synchronized void reset() {
        state = null;
    }

    private static RuntimeState runtime() {
        int configuredCellSize = DrewCraftConfig.STRATEGIC_ROUTING_CELL_SIZE_BLOCKS.get();
        int configuredCacheEntries = DrewCraftConfig.STRATEGIC_ROUTING_CACHE_ENTRIES.get();
        if (state == null
                || state.terrain.cellSizeBlocks() != configuredCellSize
                || state.maxCacheEntries != configuredCacheEntries) {
            state = new RuntimeState(configuredCellSize, configuredCacheEntries);
        }
        return state;
    }

    private static void trim(RuntimeState runtime) {
        while (runtime.cache.size() > runtime.maxCacheEntries) {
            RouteKey eldest = runtime.cache.keySet().iterator().next();
            runtime.cache.remove(eldest);
        }
    }

    private static final class RuntimeState {
        final StrategicTerrainCostMap terrain;
        final int maxCacheEntries;
        final LinkedHashMap<RouteKey, RouteTemplate> cache = new LinkedHashMap<>(16, 0.75f, true);
        long cacheHits;
        long cacheMisses;
        long successes;
        long failures;
        RoutingStats last = RoutingStats.empty();

        RuntimeState(int cellSizeBlocks, int maxCacheEntries) {
            this.terrain = new StrategicTerrainCostMap(cellSizeBlocks);
            this.maxCacheEntries = maxCacheEntries;
        }
    }

    private record RouteKey(
            String dimension,
            long startX,
            long startZ,
            long destinationX,
            long destinationZ,
            long terrainVersion
    ) {
        static RouteKey of(StrategicPosition start, StrategicPosition destination, long terrainVersion) {
            Objects.requireNonNull(start, "start");
            Objects.requireNonNull(destination, "destination");
            start.distanceTo(destination);
            return new RouteKey(
                    start.dimension(),
                    Double.doubleToLongBits(start.x()),
                    Double.doubleToLongBits(start.z()),
                    Double.doubleToLongBits(destination.x()),
                    Double.doubleToLongBits(destination.z()),
                    terrainVersion
            );
        }
    }

    private record RouteTemplate(List<StrategicPosition> waypoints, List<Double> multipliers) {
        static RouteTemplate from(StrategicRoute route) {
            return new RouteTemplate(
                    List.copyOf(route.waypoints()),
                    List.copyOf(route.segmentCostMultipliers())
            );
        }

        StrategicRoute instantiate() {
            return new StrategicRoute(new ArrayList<>(waypoints), new ArrayList<>(multipliers), 1);
        }
    }

    public record RoutingResult(boolean success, StrategicRoute route, RoutingStats stats) {
    }

    public record RoutingStats(
            boolean success,
            boolean cacheHit,
            int waypointCount,
            int expandedNodes,
            double elapsedMillis,
            double weightedCost,
            String status
    ) {
        static RoutingStats empty() {
            return new RoutingStats(false, false, 0, 0, 0.0, 0.0, "none");
        }
    }

    public record ServiceStats(
            int cellSizeBlocks,
            int knownTerrainCells,
            long terrainVersion,
            int routeCacheEntries,
            long cacheHits,
            long cacheMisses,
            long successfulPlans,
            long failedPlans,
            RoutingStats lastPlan
    ) {
    }
}
