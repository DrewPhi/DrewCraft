package dev.drewcraft.strategic.siege;

import dev.drewcraft.DrewCraft;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.block.Block;

/** Data-pack extensible siege safety tags. */
public final class SiegeBlockTags {
    public static final TagKey<Block> PROTECTED = TagKey.create(
            Registries.BLOCK, ResourceLocation.fromNamespaceAndPath(DrewCraft.MOD_ID, "siege_protected")
    );
    public static final TagKey<Block> DECORATIVE = TagKey.create(
            Registries.BLOCK, ResourceLocation.fromNamespaceAndPath(DrewCraft.MOD_ID, "siege_decorative")
    );

    private SiegeBlockTags() { }
}
