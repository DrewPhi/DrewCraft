package dev.drewcraft.command;

import com.mojang.brigadier.CommandDispatcher;
import dev.drewcraft.DrewCraft;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.net.DrewCraftProtocol;
import dev.drewcraft.persistence.DrewCraftSavedData;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

public final class DrewCraftCommands {
    private DrewCraftCommands() {
    }

    public static void register(RegisterCommandsEvent event) {
        CommandDispatcher<CommandSourceStack> dispatcher = event.getDispatcher();
        dispatcher.register(
                Commands.literal("drewcraft")
                        .requires(source -> source.hasPermission(2))
                        .then(Commands.literal("status")
                                .executes(context -> status(context.getSource())))
                        .then(Commands.literal("state")
                                .then(Commands.literal("touch")
                                        .executes(context -> touchState(context.getSource()))))
        );
    }

    private static int status(CommandSourceStack source) {
        DrewCraftSavedData data = DrewCraftSavedData.get(source.getServer());
        source.sendSuccess(() -> Component.literal(
                "DrewCraft " + DrewCraft.version()
                        + " | protocol=" + DrewCraftProtocol.CURRENT
                        + " | persistenceSchema=" + DrewCraftSavedData.CURRENT_SCHEMA_VERSION
                        + " | lastTouched=" + data.lastTouchedGameTime()
        ), false);
        source.sendSuccess(() -> Component.literal("Feature flags: " + DrewCraftConfig.integrationSummary()), false);
        return 1;
    }

    private static int touchState(CommandSourceStack source) {
        long gameTime = source.getLevel().getGameTime();
        DrewCraftSavedData.get(source.getServer()).touch(gameTime);
        source.sendSuccess(() -> Component.literal("DrewCraft SavedData marked dirty at gameTime=" + gameTime), true);
        return 1;
    }
}
