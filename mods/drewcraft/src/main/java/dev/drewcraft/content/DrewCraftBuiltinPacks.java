package dev.drewcraft.content;

import dev.drewcraft.DrewCraft;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackSource;
import net.neoforged.neoforge.event.AddPackFindersEvent;

/** Registers required pack-owned world-generation overrides above mod data. */
public final class DrewCraftBuiltinPacks {
    private DrewCraftBuiltinPacks() {
    }

    public static void register(AddPackFindersEvent event) {
        event.addPackFinders(
                ResourceLocation.fromNamespaceAndPath(
                        DrewCraft.MOD_ID,
                        "data/drewcraft/datapacks/source_worldgen"
                ),
                PackType.SERVER_DATA,
                Component.literal("DrewCraft source world generation"),
                PackSource.BUILT_IN,
                true,
                Pack.Position.TOP
        );
    }
}
