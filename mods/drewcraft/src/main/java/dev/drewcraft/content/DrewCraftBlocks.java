package dev.drewcraft.content;

import dev.drewcraft.DrewCraft;
import dev.drewcraft.strategic.source.SourceCoreBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.PushReaction;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class DrewCraftBlocks {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(DrewCraft.MOD_ID);

    public static final DeferredBlock<SourceCoreBlock> SOURCE_CORE = BLOCKS.registerBlock(
            "source_core",
            SourceCoreBlock::new,
            BlockBehaviour.Properties.of()
                    .strength(4.0F, 6.0F)
                    .pushReaction(PushReaction.BLOCK)
    );

    private DrewCraftBlocks() {
    }

    public static void register(IEventBus modBus) {
        BLOCKS.register(modBus);
    }
}
