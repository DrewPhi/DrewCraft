package dev.drewcraft.strategic.source;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Explosion;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Player-facing objective block. Persistent SourceRecord state remains authoritative. */
public final class SourceCoreBlock extends Block {
    public SourceCoreBlock(Properties properties) {
        super(properties);
    }

    @Override
    public void playerDestroy(Level level, Player player, BlockPos pos, BlockState state,
                              @Nullable BlockEntity blockEntity, ItemStack tool) {
        super.playerDestroy(level, player, pos, state, blockEntity, tool);
        if (level instanceof ServerLevel serverLevel) {
            SourceCoreRuntime.clearAt(serverLevel, pos, "PLAYER_BREAK", player.getGameProfile().getName());
        }
    }

    @Override
    public void wasExploded(Level level, BlockPos pos, Explosion explosion) {
        if (level instanceof ServerLevel serverLevel) {
            SourceCoreRuntime.clearAt(serverLevel, pos, "EXPLOSION", null);
        }
        super.wasExploded(level, pos, explosion);
    }
}
