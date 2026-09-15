package dev.drewcraft.standard;

import dev.drewcraft.persistence.DrewCraftSavedData;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Unbreakable spawn progression monument and durable campaign archive.
 *
 * <p>Right-click reads the persistent Covenant progression: how many required
 * sites are cleared, which seals are archived, and whether the capital is
 * revealed. Sparse by design: founding text, first clear, halfway,
 * completion, frontier, victory. Physical books remain collectible; this
 * block is the record that cannot be lost.
 */
public final class FlightstoneMonumentBlock extends Block {
    public static final int REQUIRED_SITES = 8;

    public FlightstoneMonumentBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, net.minecraft.core.BlockPos pos,
                                              Player player, BlockHitResult hitResult) {
        if (!(level instanceof ServerLevel serverLevel)) {
            return InteractionResult.SUCCESS;
        }
        DrewCraftSavedData data = DrewCraftSavedData.get(serverLevel.getServer());
        List<String> cleared = data.covenantClearedSites();
        player.displayClientMessage(Component.literal("[Flightstone] ")
                .withStyle(ChatFormatting.GOLD)
                .append(Component.literal(describe(cleared)).withStyle(ChatFormatting.YELLOW)), false);
        for (String site : cleared) {
            String archive = data.covenantArchives().get(site);
            if (archive != null) {
                player.displayClientMessage(Component.literal("  seal: " + archive)
                        .withStyle(ChatFormatting.GRAY), false);
            }
        }
        return InteractionResult.SUCCESS;
    }

    static String describe(List<String> cleared) {
        int count = cleared.size();
        if (count == 0) {
            return "The founding light burns. Eight chains bind the sky; none are broken.";
        }
        if (count < REQUIRED_SITES / 2) {
            return count + " of " + REQUIRED_SITES + " seals recovered. The Closed Sky stirs.";
        }
        if (count < REQUIRED_SITES) {
            return count + " of " + REQUIRED_SITES + " seals recovered. Vespera is close.";
        }
        return "All eight seals recovered. Vespera, the Rooted Crown, is revealed.";
    }
}
