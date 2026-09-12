package dev.drewcraft.strategic.routing;

import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;

/** LRU cache of immutable solved-route templates keyed by endpoints and terrain-map version. */
public final class StrategicRouteCache {
    private final int maxEntries;
    private final LinkedHashMap<RouteKey, RouteTemplate> entries = new LinkedHashMap<>(16, 0.75f, true);
    private long hits;
    private long misses;

    public StrategicRouteCache(int maxEntries) {
        if (maxEntries <= 0) throw new IllegalArgumentException("maxEntries must be positive");
        this.maxEntries = maxEntries;
    }

    public StrategicRoute get(StrategicPosition start, StrategicPosition destination, long terrainVersion) {
        RouteTemplate template = entries.get(RouteKey.of(start, destination, terrainVersion));
        if (template == null) {
            misses++;
            return null;
        }
        hits++;
        return template.instantiate();
    }

    public void put(StrategicPosition start, StrategicPosition destination, long terrainVersion, StrategicRoute route) {
        entries.put(RouteKey.of(start, destination, terrainVersion), RouteTemplate.from(route));
        while (entries.size() > maxEntries) entries.remove(entries.keySet().iterator().next());
    }

    public void clear() { entries.clear(); }
    public int size() { return entries.size(); }
    public long hits() { return hits; }
    public long misses() { return misses; }

    private record RouteKey(String dimension, long startX, long startZ, long destX, long destZ, long terrainVersion) {
        static RouteKey of(StrategicPosition start, StrategicPosition destination, long terrainVersion) {
            Objects.requireNonNull(start, "start");
            Objects.requireNonNull(destination, "destination");
            start.distanceTo(destination);
            return new RouteKey(start.dimension(), Double.doubleToLongBits(start.x()), Double.doubleToLongBits(start.z()),
                    Double.doubleToLongBits(destination.x()), Double.doubleToLongBits(destination.z()), terrainVersion);
        }
    }

    private record RouteTemplate(List<StrategicPosition> waypoints, List<Double> multipliers) {
        static RouteTemplate from(StrategicRoute route) {
            return new RouteTemplate(List.copyOf(route.waypoints()), List.copyOf(route.segmentCostMultipliers()));
        }

        StrategicRoute instantiate() {
            return new StrategicRoute(new ArrayList<>(waypoints), new ArrayList<>(multipliers), 1);
        }
    }
}
