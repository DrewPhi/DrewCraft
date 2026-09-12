package dev.drewcraft.strategic.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * A cached strategic route. The route is already solved before simulation reaches this class;
 * movement only consumes weighted segment cost and never searches the world.
 */
public final class StrategicRoute {
    private final List<StrategicPosition> waypoints;
    private final List<Double> segmentCostMultipliers;
    private int cursor;

    /** Backward-compatible flat-cost route constructor. */
    public StrategicRoute(List<StrategicPosition> waypoints, int cursor) {
        this(waypoints, flatMultipliers(waypoints), cursor);
    }

    public StrategicRoute(List<StrategicPosition> waypoints, List<Double> segmentCostMultipliers, int cursor) {
        Objects.requireNonNull(waypoints, "waypoints");
        Objects.requireNonNull(segmentCostMultipliers, "segmentCostMultipliers");
        if (waypoints.isEmpty()) {
            throw new IllegalArgumentException("route requires at least one waypoint");
        }
        if (segmentCostMultipliers.size() != Math.max(0, waypoints.size() - 1)) {
            throw new IllegalArgumentException("route requires one cost multiplier per waypoint segment");
        }
        String dimension = waypoints.getFirst().dimension();
        for (StrategicPosition waypoint : waypoints) {
            if (!dimension.equals(waypoint.dimension())) {
                throw new IllegalArgumentException("all route waypoints must share a dimension");
            }
        }
        ArrayList<Double> multipliers = new ArrayList<>(segmentCostMultipliers.size());
        for (Double multiplier : segmentCostMultipliers) {
            if (multiplier == null || !Double.isFinite(multiplier) || multiplier <= 0.0) {
                throw new IllegalArgumentException("route segment multipliers must be finite and positive");
            }
            multipliers.add(multiplier);
        }
        if (cursor < 0 || cursor > waypoints.size()) {
            throw new IllegalArgumentException("route cursor out of range");
        }
        this.waypoints = Collections.unmodifiableList(new ArrayList<>(waypoints));
        this.segmentCostMultipliers = Collections.unmodifiableList(multipliers);
        this.cursor = cursor;
    }

    public static StrategicRoute between(StrategicPosition start, StrategicPosition destination) {
        start.distanceTo(destination); // validate dimension
        return new StrategicRoute(List.of(start, destination), List.of(1.0), 1);
    }

    public List<StrategicPosition> waypoints() {
        return waypoints;
    }

    public List<Double> segmentCostMultipliers() {
        return segmentCostMultipliers;
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

    /** Weighted remaining traversal cost, in effective block-equivalent units. */
    public double remainingCostFrom(StrategicPosition position) {
        if (arrived()) {
            return 0.0;
        }
        double remaining = position.distanceTo(waypoints.get(cursor)) * multiplierForCurrentSegment();
        for (int i = cursor; i < waypoints.size() - 1; i++) {
            remaining += waypoints.get(i).distanceTo(waypoints.get(i + 1)) * segmentCostMultipliers.get(i);
        }
        return remaining;
    }

    /**
     * Consumes weighted movement budget. Difficult segments therefore reduce physical blocks
     * crossed per second without requiring any route recomputation.
     */
    public AdvanceResult advance(StrategicPosition position, double movementCostBudget) {
        Objects.requireNonNull(position, "position");
        if (!Double.isFinite(movementCostBudget) || movementCostBudget < 0.0) {
            throw new IllegalArgumentException("movement budget must be finite and non-negative");
        }
        if (!position.dimension().equals(waypoints.getFirst().dimension())) {
            throw new IllegalArgumentException("position dimension does not match route");
        }

        StrategicPosition current = position;
        double remainingBudget = movementCostBudget;
        double physicalMoved = 0.0;
        double costSpent = 0.0;

        while (remainingBudget > 0.0 && cursor < waypoints.size()) {
            StrategicPosition target = waypoints.get(cursor);
            double segmentRemaining = current.distanceTo(target);
            if (segmentRemaining <= 1.0e-9) {
                current = target;
                cursor++;
                continue;
            }

            double multiplier = multiplierForCurrentSegment();
            double segmentCost = segmentRemaining * multiplier;
            if (remainingBudget < segmentCost) {
                double physicalBudget = remainingBudget / multiplier;
                current = current.moveToward(target, physicalBudget);
                physicalMoved += physicalBudget;
                costSpent += remainingBudget;
                remainingBudget = 0.0;
            } else {
                current = target;
                cursor++;
                physicalMoved += segmentRemaining;
                costSpent += segmentCost;
                remainingBudget -= segmentCost;
            }
        }

        return new AdvanceResult(current, physicalMoved, costSpent, arrived());
    }

    private double multiplierForCurrentSegment() {
        int index = Math.max(0, cursor - 1);
        if (index >= segmentCostMultipliers.size()) {
            return 1.0;
        }
        return segmentCostMultipliers.get(index);
    }

    private static List<Double> flatMultipliers(List<StrategicPosition> waypoints) {
        Objects.requireNonNull(waypoints, "waypoints");
        if (waypoints.isEmpty()) {
            return List.of();
        }
        return Collections.nCopies(Math.max(0, waypoints.size() - 1), 1.0);
    }

    public record AdvanceResult(
            StrategicPosition position,
            double distanceMoved,
            double costSpent,
            boolean arrived
    ) {
    }
}
