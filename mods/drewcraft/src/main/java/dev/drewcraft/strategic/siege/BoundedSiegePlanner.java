package dev.drewcraft.strategic.siege;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;

/**
 * Bounded Dijkstra/A* style local planner. It optimizes for useful progress to the goal and only
 * includes block destruction when no cheaper open corridor exists. Protected cells are impassable.
 */
public final class BoundedSiegePlanner {
    private static final int[][] DIRS = {{1,0},{-1,0},{0,1},{0,-1}};

    private BoundedSiegePlanner() { }

    public static SiegePlan plan(SiegeGrid grid, int maxExpandedNodes, int maxBreachCells) {
        if (maxExpandedNodes < 1) throw new IllegalArgumentException("maxExpandedNodes must be positive");
        if (maxBreachCells < 0) throw new IllegalArgumentException("maxBreachCells must be non-negative");

        record Key(int x, int z, int breaches) { }
        record QueueNode(Key key, double cost, double priority) { }
        record Prev(Key previous) { }

        Comparator<QueueNode> order = Comparator.comparingDouble(QueueNode::priority)
                .thenComparingDouble(QueueNode::cost)
                .thenComparingInt(n -> n.key().x())
                .thenComparingInt(n -> n.key().z())
                .thenComparingInt(n -> n.key().breaches());
        PriorityQueue<QueueNode> open = new PriorityQueue<>(order);
        Map<Key, Double> best = new HashMap<>();
        Map<Key, Prev> previous = new HashMap<>();

        Key start = new Key(grid.startX(), grid.startZ(), 0);
        best.put(start, 0.0);
        open.add(new QueueNode(start, 0.0, heuristic(grid.startX(), grid.startZ(), grid)));

        int expanded = 0;
        Key goal = null;
        while (!open.isEmpty()) {
            QueueNode current = open.poll();
            Double known = best.get(current.key());
            if (known == null || current.cost() > known + 1.0e-9) continue;
            if (++expanded > maxExpandedNodes) {
                return new SiegePlan(SiegePlan.Status.BOUNDED_OUT, List.of(), List.of(), expanded - 1,
                        Double.POSITIVE_INFINITY, grid.fingerprint());
            }
            if (current.key().x() == grid.goalX() && current.key().z() == grid.goalZ()) {
                goal = current.key();
                break;
            }

            for (int[] dir : DIRS) {
                int nx = current.key().x() + dir[0];
                int nz = current.key().z() + dir[1];
                if (!grid.contains(nx, nz)) continue;
                SiegeCell cell = grid.cell(nx, nz);
                if (!cell.kind().traversable()) continue;
                int nextBreaches = current.key().breaches() + (cell.kind().breachable() ? 1 : 0);
                if (nextBreaches > maxBreachCells) continue;
                double stepCost = cell.traversalCost();
                if (!Double.isFinite(stepCost)) continue;
                double nextCost = current.cost() + stepCost;
                Key next = new Key(nx, nz, nextBreaches);
                if (nextCost + 1.0e-9 >= best.getOrDefault(next, Double.POSITIVE_INFINITY)) continue;
                best.put(next, nextCost);
                previous.put(next, new Prev(current.key()));
                open.add(new QueueNode(next, nextCost, nextCost + heuristic(nx, nz, grid)));
            }
        }

        if (goal == null) {
            return new SiegePlan(SiegePlan.Status.NO_ROUTE, List.of(), List.of(), expanded,
                    Double.POSITIVE_INFINITY, grid.fingerprint());
        }

        ArrayList<SiegePlan.Point> reversed = new ArrayList<>();
        Key cursor = goal;
        while (cursor != null) {
            reversed.add(new SiegePlan.Point(cursor.x(), cursor.z()));
            Prev prev = previous.get(cursor);
            cursor = prev == null ? null : prev.previous();
        }
        Collections.reverse(reversed);

        ArrayList<SiegePlan.BreachStep> breaches = new ArrayList<>();
        for (SiegePlan.Point point : reversed) {
            SiegeCell cell = grid.cell(point.x(), point.z());
            if (cell.kind().breachable()) {
                breaches.add(new SiegePlan.BreachStep(point.x(), point.z(), cell.kind(), cell.traversalCost()));
            }
        }
        SiegePlan.Status status = breaches.isEmpty() ? SiegePlan.Status.OPEN_ROUTE : SiegePlan.Status.BREACH_ROUTE;
        return new SiegePlan(status, reversed, breaches, expanded, best.get(goal), grid.fingerprint());
    }

    private static double heuristic(int x, int z, SiegeGrid grid) {
        return Math.abs(grid.goalX() - x) + Math.abs(grid.goalZ() - z);
    }
}
