package dev.drewcraft.aot;

import net.minecraft.network.chat.Component;
import net.neoforged.neoforge.event.CommandEvent;

public final class AotCommandRuntime {
    private AotCommandRuntime() {}

    public static void onCommand(CommandEvent event) {
        if (!AotCommandPolicy.blocks(event.getParseResults())) return;
        event.setCanceled(true);
        event.getParseResults().getContext().getSource().sendFailure(
                Component.literal("Special AOT privileges are disabled on DrewCraft."));
    }
}
