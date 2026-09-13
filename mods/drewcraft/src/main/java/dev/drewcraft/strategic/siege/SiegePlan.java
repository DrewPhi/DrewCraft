package dev.drewcraft.strategic.siege;

import java.util.List;

/** Result of one bounded local siege search. Empty breach steps means ordinary/open traversal won. */
public record SiegePlan(Status status, List<Point> path, List<BreachStep> breaches,
                        int expandedNodes, double totalCost, long gridFingerprint) {
    public SiegePlan {
        path = List.copyOf(path);
        breaches = List.copyOf(breaches);
        if (expandedNodes < 0) throw new IllegalArgumentException("expandedNodes must be non-negative");
    }

    public boolean success() { return status == Status.OPEN_ROUTE || status == Status.BREACH_ROUTE; }
    public boolean requiresBreaching() { return status == Status.BREACH_ROUTE && !breaches.isEmpty(); }

    public enum Status { OPEN_ROUTE, BREACH_ROUTE, NO_ROUTE, BOUNDED_OUT }
    public record Point(int x, int z) { }
    public record BreachStep(int x, int z, SiegeCellKind kind, double score) { }
}
