package dev.drewcraft.command;

import com.mojang.brigadier.Command;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import dev.drewcraft.standard.FlightstoneStandardDesign;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Admin/dev commands for inspecting the canonical Flightstone Standard design. */
public final class FlightstoneStandardCommands {
    private FlightstoneStandardCommands() {
    }

    public static LiteralArgumentBuilder<CommandSourceStack> node() {
        return Commands.literal("standard")
                .then(Commands.literal("give")
                        .executes(context -> give(context.getSource())));
    }

    private static int give(CommandSourceStack source) throws CommandSyntaxException {
        ServerPlayer player = source.getPlayerOrException();
        var bannerPatterns = source.getServer().registryAccess().lookupOrThrow(Registries.BANNER_PATTERN);
        ItemStack standard = FlightstoneStandardDesign.create(bannerPatterns);

        if (!player.getInventory().add(standard)) {
            player.drop(standard, false);
        }

        source.sendSuccess(
                () -> Component.literal("Gave canonical Flightstone Standard. Combine it with a shield normally to copy the heraldry."),
                false
        );
        return Command.SINGLE_SUCCESS;
    }
}
