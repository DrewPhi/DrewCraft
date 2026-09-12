package dev.drewcraft.strategic.routing;

import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;

/** Process-local routing facade over the coarse terrain map and deterministic LRU route cache. */
public final class StrategicRoutingService {
    private static RuntimeState state;

    private StrategicRoutingService() {
    }

    public static synchronized StrategicTerrainCostMap terrainCosts() {
        return runtime().terrain;
    }

    public static synchronized RoutingResult plan(StrategicPosition start, StrategicPosition destination) {
        RuntimeState runtime = runtime();
        long terrainVersion = runtime.terrain.version();
        StrategicRoute cached = runtime.cache.get(start, destination, terrainVersion);
        if (cached != null) {
            runtime.last = new RoutingStats(true, true, cached.waypoints().size(), 0, 0.0,
                    cached.remainingCostFrom(start), "cache_hit");
            return new RoutingResult(true, cached, runtime.last);
        }

        StrategicRoutePlanner planner = new StrategicRoutePlanner(
                runtime.terrain,
                DrewCraftConfig.STRATEGIC_ROUTING_MAX_EXPANDED_NODES.get(),
                DrewCraftConfig.STRATEGIC_ROUTING_DETOUR_PADDING_CELLS.get()
        );
        StrategicRoutePlanner.PlanResult planned = planner.plan(start, destination);
        if (!planned.success()) {
            runtime.failures++;
            runtime.last = new RoutingStats(false, false, 0, planned.expandedNodes(), planned.elapsedMillis(),
                    Double.POSITIVE_INFINITY, planned.status());
            return new RoutingResult(false, null, runtime.last);
        }

        runtime.successes++;
        runtime.cache.put(start, destination, terrainVersion, planned.route());
        StrategicRoute fresh = runtime.cache.get(start, destination, terrainVersion);
        runtime.last = new RoutingStats(true, false, fresh.waypoints().size(), planned.expandedNodes(),
                planned.elapsedMillis(), planned.weightedCost(), planned.status());
        return new RoutingResult(true, fresh, runtime.last);
    }

    public static synchronized ServiceStats stats() {
        RuntimeState runtime = runtime();
        return new ServiceStats(runtime.terrain.cellSizeBlocks(), runtime.terrain.knownCellCount(),
                runtime.terrain.version(), runtime.cache.size(), runtime.cache.hits(), runtime.cache.misses(),
                runtime.successes, runtime.failures, runtime.last);
    }

    public static synchronized void invalidateRoutes() {
        runtime().cache.clear();
    }

    public static synchronized void reset() {
        state = null;
    }

    private static RuntimeState runtime() {
        int configuredCellSize = DrewCraftConfig.STRATEGIC_ROUTING_CELL_SIZE_BLOCKS.get();
        int configuredCacheEntries = DrewCraftConfig.STRATEGIC_ROUTING_CACHE_ENTRIES.get();
        if (state == null || state.terrain.cellSizeBlocks() != configuredCellSize || state.maxCacheEntries != configuredCacheEntries) {
            state = new RuntimeState(configuredCellSize, configuredCacheEntries);
        }
        return state;
    }

    private static final class RuntimeState {
        final StrategicTerrainCostMap terrain;
        final int maxCacheEntries;
        final StrategicRouteCache cache;
        long successes;
        long failures;
        RoutingStats last = RoutingStats.empty();

        RuntimeState(int cellSizeBlocks, int maxCacheEntries) {
            this.terrain = new StrategicTerrainCostMap(cellSizeBlocks);
            this.maxCacheEntries = maxCacheEntries;
            this.cache = new StrategicRouteCache(maxCacheEntries);
        }
    }

    public record RoutingResult(boolean success, StrategicRoute route, RoutingStats stats) {
    }

    public record RoutingStats(boolean success, boolean cacheHit, int waypointCount, int expandedNodes,
                               double elapsedMillis, double weightedCost, String status) {
        static RoutingStats empty() {
            return new RoutingStats(false, false, 0, 0, 0.0, 0.0, "none");
        }
    }

    public record ServiceStats(int cellSizeBlocks, int knownTerrainCells, long terrainVersion,
                               int routeCacheEntries, long cacheHits, long cacheMisses,
                               long successfulPlans, long failedPlans, RoutingStats lastPlan) {
    }
}
