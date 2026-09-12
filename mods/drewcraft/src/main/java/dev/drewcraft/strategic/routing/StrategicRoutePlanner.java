package dev.drewcraft.strategic.routing;

import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.PriorityQueue;
import java.util.Set;

/** Bounded A* over the coarse strategic cost map. Never accesses Minecraft world/chunk state. */
public final class StrategicRoutePlanner {
    private static final int[][] DIRECTIONS = {
            {-1, -1}, {-1, 0}, {-1, 1},
            {0, -1},           {0, 1},
            {1, -1},  {1, 0}, {1, 1}
    };

    private final StrategicTerrainCostMap terrain;
    private final int maxExpandedNodes;
    private final int detourPaddingCells;

    public StrategicRoutePlanner(
            StrategicTerrainCostMap terrain,
            int maxExpandedNodes,
            int detourPaddingCells
    ) {
        this.terrain = Objects.requireNonNull(terrain, "terrain");
        if (maxExpandedNodes <= 0 || detourPaddingCells < 0) {
            throw new IllegalArgumentException("routing bounds must be non-negative and max nodes positive");
        }
        this.maxExpandedNodes = maxExpandedNodes;
        this.detourPaddingCells = detourPaddingCells;
    }

    public PlanResult plan(StrategicPosition start, StrategicPosition destination) {
        Objects.requireNonNull(start, "start");
        Objects.requireNonNull(destination, "destination");
        start.distanceTo(destination); // dimension validation

        int cellSize = terrain.cellSizeBlocks();
        StrategicCell startCell = StrategicCell.fromPosition(start, cellSize);
        StrategicCell goalCell = StrategicCell.fromPosition(destination, cellSize);

        if (!terrain.traversable(startCell) || !terrain.traversable(goalCell)) {
            return PlanResult.failure("start_or_destination_blocked", 0, 0L);
        }
        if (startCell.equals(goalCell)) {
            double multiplier = terrain.multiplier(goalCell);
            StrategicRoute route = new StrategicRoute(
                    List.of(start, destination),
                    List.of(multiplier),
                    1
            );
            return PlanResult.success(route, route.remainingCostFrom(start), 0, 0L);
        }

        long started = System.nanoTime();
        Bounds bounds = Bounds.around(startCell, goalCell, detourPaddingCells);
        PriorityQueue<Node> open = new PriorityQueue<>(Comparator
                .comparingDouble(Node::fScore)
                .thenComparingDouble(Node::gScore)
                .thenComparingInt(node -> node.cell().x())
                .thenComparingInt(node -> node.cell().z()));
        Map<StrategicCell, Double> gScore = new HashMap<>();
        Map<StrategicCell, StrategicCell> cameFrom = new HashMap<>();
        Set<StrategicCell> closed = new HashSet<>();

        gScore.put(startCell, 0.0);
        open.add(new Node(startCell, 0.0, heuristic(startCell, goalCell, cellSize)));

        int expanded = 0;
        while (!open.isEmpty()) {
            Node current = open.poll();
            if (!closed.add(current.cell())) {
                continue;
            }
            if (current.cell().equals(goalCell)) {
                List<StrategicCell> cells = reconstruct(cameFrom, current.cell());
                StrategicRoute route = toRoute(start, destination, cells, terrain);
                long nanos = System.nanoTime() - started;
                return PlanResult.success(route, route.remainingCostFrom(start), expanded, nanos);
            }
            if (++expanded > maxExpandedNodes) {
                return PlanResult.failure("max_expanded_nodes", expanded, System.nanoTime() - started);
            }

            for (int[] direction : DIRECTIONS) {
                StrategicCell neighbor = current.cell().offset(direction[0], direction[1]);
                if (!bounds.contains(neighbor) || closed.contains(neighbor) || !terrain.traversable(neighbor)) {
                    continue;
                }
                if (direction[0] != 0 && direction[1] != 0
                        && (!terrain.traversable(current.cell().offset(direction[0], 0))
                        || !terrain.traversable(current.cell().offset(0, direction[1])))) {
                    continue; // do not cut diagonally through blocked corners
                }

                double edgeCost = edgeCost(current.cell(), neighbor, cellSize);
                double tentative = current.gScore() + edgeCost;
                double previous = gScore.getOrDefault(neighbor, Double.POSITIVE_INFINITY);
                if (tentative + 1.0e-9 < previous) {
                    cameFrom.put(neighbor, current.cell());
                    gScore.put(neighbor, tentative);
                    double f = tentative + heuristic(neighbor, goalCell, cellSize);
                    open.add(new Node(neighbor, tentative, f));
                }
            }
        }
        return PlanResult.failure("no_route_within_bounds", expanded, System.nanoTime() - started);
    }

    private double edgeCost(StrategicCell from, StrategicCell to, int cellSize) {
        double physical = from.centerDistanceCells(to) * cellSize;
        double multiplier = (terrain.multiplier(from) + terrain.multiplier(to)) * 0.5;
        return physical * multiplier;
    }

    private static double heuristic(StrategicCell from, StrategicCell goal, int cellSize) {
        return from.centerDistanceCells(goal)
                * cellSize
                * StrategicTerrainClass.minimumTraversableMultiplier();
    }

    private static List<StrategicCell> reconstruct(
            Map<StrategicCell, StrategicCell> cameFrom,
            StrategicCell goal
    ) {
        ArrayList<StrategicCell> reversed = new ArrayList<>();
        StrategicCell cursor = goal;
        reversed.add(cursor);
        while (cameFrom.containsKey(cursor)) {
            cursor = cameFrom.get(cursor);
            reversed.add(cursor);
        }
        ArrayList<StrategicCell> path = new ArrayList<>(reversed.size());
        for (int i = reversed.size() - 1; i >= 0; i--) {
            path.add(reversed.get(i));
        }
        return path;
    }

    private static StrategicRoute toRoute(
            StrategicPosition start,
            StrategicPosition destination,
            List<StrategicCell> cells,
            StrategicTerrainCostMap terrain
    ) {
        int cellSize = terrain.cellSizeBlocks();
        ArrayList<StrategicPosition> waypoints = new ArrayList<>();
        ArrayList<Double> multipliers = new ArrayList<>();
        waypoints.add(start);

        for (int i = 1; i < cells.size(); i++) {
            StrategicCell cell = cells.get(i);
            StrategicPosition center = cell.center(cellSize);
            StrategicTerrainClass fromClass = terrain.terrainClass(cells.get(i - 1));
            StrategicTerrainClass toClass = terrain.terrainClass(cell);
            multipliers.add((fromClass.multiplier() + toClass.multiplier()) * 0.5);
            waypoints.add(center);
        }

        StrategicPosition last = waypoints.getLast();
        if (last.distanceTo(destination) > 1.0e-9) {
            multipliers.add(terrain.multiplier(cells.getLast()));
            waypoints.add(destination);
        } else {
            waypoints.set(waypoints.size() - 1, destination);
        }
        return new StrategicRoute(waypoints, multipliers, 1);
    }

    private record Node(StrategicCell cell, double gScore, double fScore) {
    }

    private record Bounds(int minX, int maxX, int minZ, int maxZ, String dimension) {
        static Bounds around(StrategicCell a, StrategicCell b, int padding) {
            return new Bounds(
                    Math.min(a.x(), b.x()) - padding,
                    Math.max(a.x(), b.x()) + padding,
                    Math.min(a.z(), b.z()) - padding,
                    Math.max(a.z(), b.z()) + padding,
                    a.dimension()
            );
        }

        boolean contains(StrategicCell cell) {
            return dimension.equals(cell.dimension())
                    && cell.x() >= minX && cell.x() <= maxX
                    && cell.z() >= minZ && cell.z() <= maxZ;
        }
    }

    public record PlanResult(
            boolean success,
            StrategicRoute route,
            double weightedCost,
            int expandedNodes,
            long elapsedNanos,
            String status
    ) {
        static PlanResult success(StrategicRoute route, double weightedCost, int expandedNodes, long elapsedNanos) {
            return new PlanResult(true, route, weightedCost, expandedNodes, elapsedNanos, "ok");
        }

        static PlanResult failure(String status, int expandedNodes, long elapsedNanos) {
            return new PlanResult(false, null, Double.POSITIVE_INFINITY, expandedNodes, elapsedNanos, status);
        }

        public double elapsedMillis() {
            return elapsedNanos / 1_000_000.0;
        }
    }
}
