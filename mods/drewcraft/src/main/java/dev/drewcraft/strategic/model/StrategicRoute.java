package dev.drewcraft.strategic.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * A cached strategic route. This class only advances along supplied waypoints; it never searches
 * the Minecraft world or computes a path. Route generation belongs to the routing layer (BP2).
 */
public final class StrategicRoute {
    private final List<StrategicPosition> waypoints;
    private int cursor;

    public StrategicRoute(List<StrategicPosition> waypoints, int cursor) {
        Objects.requireNonNull(waypoints, "waypoints");
        if (waypoints.isEmpty()) {
            throw new IllegalArgumentException("route requires at least one waypoint");
        }
        String dimension = waypoints.getFirst().dimension();
        for (StrategicPosition waypoint : waypoints) {
            if (!dimension.equals(waypoint.dimension())) {
                throw new IllegalArgumentException("all route waypoints must share a dimension");
            }
        }
        if (cursor < 0 || cursor > waypoints.size()) {
            throw new IllegalArgumentException("route cursor out of range");
        }
        this.waypoints = Collections.unmodifiableList(new ArrayList<>(waypoints));
        this.cursor = cursor;
    }

    public static StrategicRoute between(StrategicPosition start, StrategicPosition destination) {
        start.distanceTo(destination); // validate dimension
        return new StrategicRoute(List.of(start, destination), 1);
    }

    public List<StrategicPosition> waypoints() {
        return waypoints;
    }

    public int cursor() {
        return cursor;
    }

    public boolean arrived() {
        return cursor >= waypoints.size();
    }

    public StrategicPosition destination() {
        return waypoints.getLast();
    }

    public double remainingDistanceFrom(StrategicPosition position) {
        if (arrived()) {
            return 0.0;
        }
        double remaining = position.distanceTo(waypoints.get(cursor));
        for (int i = cursor; i < waypoints.size() - 1; i++) {
            remaining += waypoints.get(i).distanceTo(waypoints.get(i + 1));
        }
        return remaining;
    }

    public AdvanceResult advance(StrategicPosition position, double movementBudget) {
        Objects.requireNonNull(position, "position");
        if (!Double.isFinite(movementBudget) || movementBudget < 0.0) {
            throw new IllegalArgumentException("movement budget must be finite and non-negative");
        }
        if (!position.dimension().equals(waypoints.getFirst().dimension())) {
            throw new IllegalArgumentException("position dimension does not match route");
        }

        StrategicPosition current = position;
        double remainingBudget = movementBudget;
        double moved = 0.0;

        while (remainingBudget > 0.0 && cursor < waypoints.size()) {
            StrategicPosition target = waypoints.get(cursor);
            double segmentRemaining = current.distanceTo(target);
            if (segmentRemaining <= 1.0e-9) {
                current = target;
                cursor++;
                continue;
            }
            if (remainingBudget < segmentRemaining) {
                current = current.moveToward(target, remainingBudget);
                moved += remainingBudget;
                remainingBudget = 0.0;
            } else {
                current = target;
                cursor++;
                moved += segmentRemaining;
                remainingBudget -= segmentRemaining;
            }
        }

        return new AdvanceResult(current, moved, arrived());
    }

    public record AdvanceResult(StrategicPosition position, double distanceMoved, boolean arrived) {
    }
}
