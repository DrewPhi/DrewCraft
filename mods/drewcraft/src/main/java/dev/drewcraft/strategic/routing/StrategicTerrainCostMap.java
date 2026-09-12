package dev.drewcraft.strategic.routing;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * Mutable coarse terrain-cost cache used by strategic routing. This cache never reads Minecraft
 * world state itself; producers may populate it from offline pregeneration metadata or explicitly
 * sampled already-loaded terrain. Missing cells use an explicit conservative UNKNOWN cost.
 */
public final class StrategicTerrainCostMap {
    private final int cellSizeBlocks;
    private final Map<StrategicCell, StrategicTerrainClass> classes = new HashMap<>();
    private long version;

    public StrategicTerrainCostMap(int cellSizeBlocks) {
        if (cellSizeBlocks <= 0) {
            throw new IllegalArgumentException("cellSizeBlocks must be positive");
        }
        this.cellSizeBlocks = cellSizeBlocks;
    }

    public int cellSizeBlocks() {
        return cellSizeBlocks;
    }

    public long version() {
        return version;
    }

    public int knownCellCount() {
        return classes.size();
    }

    public StrategicTerrainClass terrainClass(StrategicCell cell) {
        Objects.requireNonNull(cell, "cell");
        return classes.getOrDefault(cell, StrategicTerrainClass.UNKNOWN);
    }

    public double multiplier(StrategicCell cell) {
        return terrainClass(cell).multiplier();
    }

    public boolean traversable(StrategicCell cell) {
        return terrainClass(cell).traversable();
    }

    /** Returns true only when the effective stored value changed. */
    public boolean put(StrategicCell cell, StrategicTerrainClass terrainClass) {
        Objects.requireNonNull(cell, "cell");
        Objects.requireNonNull(terrainClass, "terrainClass");
        StrategicTerrainClass previous = classes.put(cell, terrainClass);
        if (previous != terrainClass) {
            version++;
            return true;
        }
        return false;
    }

    public boolean remove(StrategicCell cell) {
        Objects.requireNonNull(cell, "cell");
        if (classes.remove(cell) != null) {
            version++;
            return true;
        }
        return false;
    }

    public void clear() {
        if (!classes.isEmpty()) {
            classes.clear();
            version++;
        }
    }
}
