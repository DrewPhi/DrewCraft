package dev.drewcraft.aot;

import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.coordinates.BlockPosArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import java.util.Random;
import dev.drewcraft.DrewCraft;

/** Explicit, administrator-only placement; never runs during world generation. */
public final class AotDockCommands {
    private AotDockCommands() {}

    public static LiteralArgumentBuilder<CommandSourceStack> node() {
        var origin = Commands.argument("origin", BlockPosArgument.blockPos());
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            origin.then(Commands.literal(facing.getName()).executes(ctx -> place(
                    ctx.getSource(), BlockPosArgument.getBlockPos(ctx, "origin"), facing)));
        }
        return Commands.literal("aot").requires(s -> s.hasPermission(4))
                .then(Commands.literal("dock").then(origin));
    }

    private static int place(CommandSourceStack source, BlockPos origin, Direction facing) {
        if (!AotIsolation.automaticDocksSuppressed) {
            source.sendFailure(Component.literal("AOT dock protection is not active."));
            return 0;
        }
        ServerLevel level = source.getServer().overworld();
        try {
            Class<?> trackerType = Class.forName("daot.world.PortalLocationTracker");
            Object tracker = trackerType.getMethod("get", ServerLevel.class).invoke(null, level);
            if (trackerType.getMethod("getRandomOverworldDock", Random.class)
                    .invoke(tracker, new Random(0)) != null) {
                source.sendFailure(Component.literal("An AOT dock is already registered; refusing a second dock."));
                return 0;
            }
            var template = level.getStructureManager().get(ResourceLocation.parse("dannys-aot:docks1"))
                    .orElseThrow(() -> new IllegalStateException("Upstream dock template is missing"));
            if (!template.getSize().equals(new net.minecraft.core.Vec3i(48, 20, 35))) {
                throw new IllegalStateException("Unexpected dock template footprint");
            }
            Rotation rotation = switch (facing) {
                case WEST -> Rotation.CLOCKWISE_90;
                case NORTH -> Rotation.CLOCKWISE_180;
                case EAST -> Rotation.COUNTERCLOCKWISE_90;
                default -> Rotation.NONE;
            };
            // Fail before writing if this volume could overwrite terrain/builds.
            // Only loaded ocean/air is accepted; this command never pregenerates.
            for (BlockPos local : BlockPos.betweenClosed(0, 0, 0, 47, 19, 34)) {
                BlockPos pos = StructureTemplate.transform(local,
                        net.minecraft.world.level.block.Mirror.NONE, rotation, BlockPos.ZERO).offset(origin);
                if (!level.isInWorldBounds(pos) || !level.getWorldBorder().isWithinBounds(pos)
                        || !level.hasChunk(pos.getX() >> 4, pos.getZ() >> 4)) {
                    source.sendFailure(Component.literal("Dock footprint must be inside loaded Overworld chunks and bounds."));
                    return 0;
                }
                var state = level.getBlockState(pos);
                if ((!state.isAir() && !state.is(Blocks.WATER)) || level.getBlockEntity(pos) != null) {
                    source.sendFailure(Component.literal("Dock footprint is not clear ocean/air at " + pos.toShortString()
                            + "; nothing was placed."));
                    return 0;
                }
            }
            // Use the upstream operation: skips template air, activates portal
            // markers and persists the return dock. No modified upstream jar.
            var place = Class.forName("daot.world.OverworldDocksGenerator").getDeclaredMethod(
                    "placeDocksStructure", ServerLevel.class, BlockPos.class, Direction.class, RandomSource.class);
            place.setAccessible(true);
            place.invoke(null, level, origin.below(3), facing, level.random);
            Object saved = trackerType.getMethod("getRandomOverworldDock", Random.class)
                    .invoke(tracker, new Random(0));
            if (!origin.equals(saved)) throw new IllegalStateException("Dock return registration failed");
            source.sendSuccess(() -> Component.literal("AOT dock placed and return registered at "
                    + origin.toShortString() + " facing " + facing.getName()), true);
            return 1;
        } catch (ReflectiveOperationException | RuntimeException e) {
            DrewCraft.LOGGER.error("Manual AOT dock placement failed", e);
            source.sendFailure(Component.literal("AOT dock placement failed; inspect server log before retrying."));
            return 0;
        }
    }
}
