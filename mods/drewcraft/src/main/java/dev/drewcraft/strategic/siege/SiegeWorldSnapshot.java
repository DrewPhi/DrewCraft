package dev.drewcraft.strategic.siege;

import java.util.HashMap;
import java.util.Map;
import net.minecraft.tags.BlockTags;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;

/**
 * Converts a small already-loaded horizontal neighborhood into the pure planner grid. Never asks
 * Minecraft to generate/load a chunk. The first obstructing foot/head block is the breach target.
 */
public final class SiegeWorldSnapshot {
    private final SiegeGrid grid;
    private final Map<Long, BlockPos> blockersByLocalKey;
    private final int originX;
    private final int originZ;
    private final int baseY;

    private SiegeWorldSnapshot(SiegeGrid grid, Map<Long, BlockPos> blockersByLocalKey,
                               int originX, int originZ, int baseY) {
        this.grid = grid;
        this.blockersByLocalKey = Map.copyOf(blockersByLocalKey);
        this.originX = originX;
        this.originZ = originZ;
        this.baseY = baseY;
    }

    public SiegeGrid grid() { return grid; }
    public BlockPos blockerFor(int localX, int localZ) { return blockersByLocalKey.get(key(localX, localZ)); }
    public BlockPos worldPoint(int localX, int localZ) { return new BlockPos(originX + localX, baseY, originZ + localZ); }

    public static SiegeWorldSnapshot capture(ServerLevel level, BlockPos center, BlockPos localGoal, int radius) {
        if (radius < 2 || radius > 64) throw new IllegalArgumentException("radius must be 2..64");
        int size = radius * 2 + 1;
        int originX = center.getX() - radius;
        int originZ = center.getZ() - radius;
        int baseY = center.getY();
        int startX = radius;
        int startZ = radius;
        int goalX = clamp(localGoal.getX() - originX, 0, size - 1);
        int goalZ = clamp(localGoal.getZ() - originZ, 0, size - 1);
        SiegeGrid.Builder builder = SiegeGrid.builder(size, size).start(startX, startZ).goal(goalX, goalZ);
        HashMap<Long, BlockPos> blockers = new HashMap<>();

        for (int lx = 0; lx < size; lx++) {
            for (int lz = 0; lz < size; lz++) {
                BlockPos foot = new BlockPos(originX + lx, baseY, originZ + lz);
                BlockPos head = foot.above();
                SiegeCell cell = classifyColumn(level, foot, head, blockers, lx, lz);
                builder.set(lx, lz, cell);
            }
        }
        // The mob already occupies its own cell, even if rounding catches the block below/edge.
        builder.set(startX, startZ, SiegeCell.open());
        blockers.remove(key(startX, startZ));
        return new SiegeWorldSnapshot(builder.build(), blockers, originX, originZ, baseY);
    }

    public static SiegeCell classifyBlock(ServerLevel level, BlockPos pos) {
        if (!level.hasChunkAt(pos)) return SiegeCell.protectedCell();
        BlockState state = level.getBlockState(pos);
        if (state.isAir() || state.getCollisionShape(level, pos).isEmpty()) return SiegeCell.open();
        if (level.getBlockEntity(pos) != null || state.is(SiegeBlockTags.PROTECTED)) return SiegeCell.protectedCell();
        // The 2-D local planner must never interpret a natural hillside as a wall to mine through.
        if (state.is(BlockTags.DIRT) || state.is(BlockTags.BASE_STONE_OVERWORLD)
                || state.is(BlockTags.BASE_STONE_NETHER) || state.is(BlockTags.SAND)) {
            return SiegeCell.protectedCell();
        }
        float hardness = state.getDestroySpeed(level, pos);
        if (hardness < 0.0F) return SiegeCell.protectedCell();
        if (state.hasProperty(BlockStateProperties.OPEN) && state.getValue(BlockStateProperties.OPEN)) return SiegeCell.open();
        if (state.getBlock() instanceof FenceGateBlock) return new SiegeCell(SiegeCellKind.GATE, hardness);
        if (state.getBlock() instanceof DoorBlock || state.getBlock() instanceof TrapDoorBlock) {
            return new SiegeCell(SiegeCellKind.DOOR, hardness);
        }
        if (state.is(SiegeBlockTags.DECORATIVE)) return new SiegeCell(SiegeCellKind.DECORATIVE, hardness);
        if (hardness <= 1.5F) return new SiegeCell(SiegeCellKind.WEAK_BARRIER, hardness);
        return new SiegeCell(SiegeCellKind.SOLID_BARRIER, hardness);
    }

    private static SiegeCell classifyColumn(ServerLevel level, BlockPos foot, BlockPos head,
                                            Map<Long, BlockPos> blockers, int lx, int lz) {
        SiegeCell footCell = classifyBlock(level, foot);
        SiegeCell headCell = classifyBlock(level, head);
        if (footCell.kind() == SiegeCellKind.OPEN && headCell.kind() == SiegeCellKind.OPEN) return SiegeCell.open();
        SiegeCell selected;
        BlockPos selectedPos;
        if (footCell.kind() == SiegeCellKind.PROTECTED || headCell.kind() == SiegeCellKind.PROTECTED) {
            selected = SiegeCell.protectedCell();
            selectedPos = footCell.kind() == SiegeCellKind.PROTECTED ? foot : head;
        } else if (footCell.kind() != SiegeCellKind.OPEN) {
            selected = footCell;
            selectedPos = foot;
        } else {
            selected = headCell;
            selectedPos = head;
        }
        blockers.put(key(lx, lz), selectedPos);
        return selected;
    }

    private static long key(int x, int z) { return ((long) x << 32) ^ (z & 0xffffffffL); }
    private static int clamp(int value, int min, int max) { return Math.max(min, Math.min(max, value)); }
}
