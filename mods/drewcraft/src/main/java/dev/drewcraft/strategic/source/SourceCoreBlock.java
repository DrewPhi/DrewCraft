package dev.drewcraft.strategic.source;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
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
                              BlockEntity blockEntity, ItemStack tool) {
        super.playerDestroy(level, player, pos, state, blockEntity, tool);
        if (level instanceof ServerLevel serverLevel) {
            clearAndAnnounce(serverLevel, pos, "PLAYER_BREAK", player.getGameProfile().getName());
        }
    }

    @Override
    public void wasExploded(Level level, BlockPos pos, Explosion explosion) {
        if (level instanceof ServerLevel serverLevel) {
            clearAndAnnounce(serverLevel, pos, "EXPLOSION", null);
        }
        super.wasExploded(level, pos, explosion);
    }

    private static void clearAndAnnounce(ServerLevel level, BlockPos pos, String cause, String actor) {
        SourceCoreRuntime.ClearResult result = SourceCoreRuntime.clearAt(level, pos, cause, actor);
        if (!result.newlyCleared()) return;

        Component message = Component.literal("[DrewCraft] ")
                .withStyle(ChatFormatting.DARK_PURPLE)
                .append(Component.literal("Hostile source deactivated at ")
                        .withStyle(ChatFormatting.LIGHT_PURPLE))
                .append(Component.literal(pos.getX() + ", " + pos.getY() + ", " + pos.getZ())
                        .withStyle(ChatFormatting.AQUA))
                .append(Component.literal(". No new strategic forces can launch from it.")
                        .withStyle(ChatFormatting.GRAY));
        level.getServer().getPlayerList().broadcastSystemMessage(message, false);
    }
}
