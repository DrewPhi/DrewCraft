package dev.drewcraft.command;

import com.mojang.brigadier.arguments.DoubleArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.suggestion.SuggestionProvider;
import dev.drewcraft.flak.FlakBatteryRegistry;
import dev.drewcraft.flak.FlakZone;
import java.util.Map;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.phys.Vec3;

/** Admin diagnostics for flak zones: list, register test zones, remove. */
public final class FlakCommands {
    private static final SuggestionProvider<CommandSourceStack> ZONES =
            (context, builder) -> SharedSuggestionProvider.suggest(
                    FlakBatteryRegistry.zones().stream().map(FlakZone::zoneId).toList(), builder);

    private FlakCommands() {
    }

    public static LiteralArgumentBuilder<CommandSourceStack> node() {
        return Commands.literal("flak")
                .then(Commands.literal("list").executes(context -> list(context.getSource())))
                .then(Commands.literal("add-test")
                        .then(Commands.argument("zoneId", StringArgumentType.word())
                                .then(Commands.argument("radius", DoubleArgumentType.doubleArg(16.0, 512.0))
                                        .executes(context -> addTest(context.getSource(),
                                                StringArgumentType.getString(context, "zoneId"),
                                                DoubleArgumentType.getDouble(context, "radius"))))))
                .then(Commands.literal("remove")
                        .then(Commands.argument("zoneId", StringArgumentType.word()).suggests(ZONES)
                                .executes(context -> remove(context.getSource(),
                                        StringArgumentType.getString(context, "zoneId")))));
    }

    private static int list(CommandSourceStack source) {
        var zones = FlakBatteryRegistry.zones();
        if (zones.isEmpty()) {
            source.sendSuccess(() -> Component.literal("No live flak zones"), false);
            return 1;
        }
        Map<String, FlakBatteryRegistry.BurstRecord> bursts = FlakBatteryRegistry.lastBursts();
        for (FlakZone zone : zones) {
            var last = bursts.get(zone.zoneId());
            String extra = last == null ? "no bursts yet"
                    : "last burst " + String.format("%.1f", last.damage()) + " dmg @ tick " + last.gameTime();
            source.sendSuccess(() -> Component.literal(
                    zone.zoneId() + " site=" + zone.siteId() + " r=" + zone.radiusBlocks() + " " + extra), false);
        }
        return 1;
    }

    private static int addTest(CommandSourceStack source, String zoneId, double radius) {
        BlockPos origin = BlockPos.containing(source.getPosition());
        Vec3 center = new Vec3(origin.getX() + 0.5, origin.getY(), origin.getZ() + 0.5);
        boolean added = FlakBatteryRegistry.register(new FlakZone(
                zoneId, "test-site", center, radius, 1.0, 20, 1.0, 6.0));
        source.sendSuccess(() -> Component.literal(
                added ? "Registered test flak zone " + zoneId : "Zone already exists: " + zoneId), true);
        return added ? 1 : 0;
    }

    private static int remove(CommandSourceStack source, String zoneId) {
        boolean removed = FlakBatteryRegistry.remove(zoneId);
        source.sendSuccess(() -> Component.literal(
                removed ? "Removed flak zone " + zoneId : "Unknown flak zone: " + zoneId), true);
        return removed ? 1 : 0;
    }
}
