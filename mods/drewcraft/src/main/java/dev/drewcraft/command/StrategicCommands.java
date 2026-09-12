package dev.drewcraft.command;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.simulation.StrategicScheduler;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;

final class StrategicCommands {
    private StrategicCommands() {
    }

    static LiteralArgumentBuilder<CommandSourceStack> node() {
        return Commands.literal("strategic")
                .then(Commands.literal("create-test")
                        .executes(context -> createTest(context.getSource())))
                .then(Commands.literal("list")
                        .executes(context -> list(context.getSource())))
                .then(Commands.literal("inspect")
                        .then(Commands.argument("groupId", StringArgumentType.word())
                                .executes(context -> inspect(
                                        context.getSource(),
                                        StringArgumentType.getString(context, "groupId")
                                ))))
                .then(Commands.literal("step")
                        .then(Commands.argument("seconds", IntegerArgumentType.integer(1, 3600))
                                .executes(context -> step(
                                        context.getSource(),
                                        IntegerArgumentType.getInteger(context, "seconds")
                                ))))
                .then(Commands.literal("perf")
                        .executes(context -> perf(context.getSource())));
    }

    private static int createTest(CommandSourceStack source) {
        String dimension = source.getLevel().dimension().location().toString();
        StrategicPosition start = new StrategicPosition(dimension, source.getPosition().x, source.getPosition().z);
        StrategicPosition destination = new StrategicPosition(dimension, start.x() + 1000.0, start.z());
        StrategicGroup group = StrategicGroup.testGroup(start, destination, source.getLevel().getGameTime());
        DrewCraftSavedData.get(source.getServer()).upsertStrategicGroup(group);
        source.sendSuccess(() -> Component.literal(
                "Created strategic test group " + group.groupId()
                        + " at " + formatPosition(group.position())
                        + " -> " + formatPosition(group.destination())
                        + " (cached waypoint route; no path search)"
        ), true);
        return 1;
    }

    private static int list(CommandSourceStack source) {
        List<StrategicGroup> groups = DrewCraftSavedData.get(source.getServer()).strategicGroups();
        source.sendSuccess(() -> Component.literal("Strategic groups: " + groups.size()), false);
        int shown = Math.min(groups.size(), 20);
        for (int i = 0; i < shown; i++) {
            StrategicGroup group = groups.get(i);
            source.sendSuccess(() -> Component.literal(shortDescription(group)), false);
        }
        if (groups.size() > shown) {
            source.sendSuccess(() -> Component.literal("... " + (groups.size() - shown) + " more"), false);
        }
        return groups.size();
    }

    private static int inspect(CommandSourceStack source, String rawId) {
        UUID groupId;
        try {
            groupId = UUID.fromString(rawId);
        } catch (IllegalArgumentException ex) {
            source.sendFailure(Component.literal("Invalid group UUID: " + rawId));
            return 0;
        }
        return DrewCraftSavedData.get(source.getServer()).strategicGroup(groupId)
                .map(group -> {
                    source.sendSuccess(() -> Component.literal(
                            shortDescription(group)
                                    + " destination=" + formatPosition(group.destination())
                                    + " routeCursor=" + group.route().cursor() + "/" + group.route().waypoints().size()
                                    + " speed=" + String.format(Locale.ROOT, "%.2f", group.movementSpeedBlocksPerSecond()) + "b/s"
                                    + " strength=" + group.totalStrength()
                                    + " eta=" + String.format(Locale.ROOT, "%.1fs", group.etaSeconds())
                                    + " lastSimGameTime=" + group.lastSimulatedGameTime()
                    ), false);
                    return 1;
                })
                .orElseGet(() -> {
                    source.sendFailure(Component.literal("Unknown strategic group: " + groupId));
                    return 0;
                });
    }

    private static int step(CommandSourceStack source, int seconds) {
        DrewCraftSavedData data = DrewCraftSavedData.get(source.getServer());
        StrategicScheduler.CycleStats stats = StrategicScheduler.advanceBySeconds(
                data.strategicGroups(),
                seconds,
                DrewCraftConfig.STRATEGIC_MAX_GROUPS_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_MAX_MILLIS_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_MAX_CATCHUP_SECONDS.get()
        );
        if (stats.groupsUpdated() > 0) {
            data.markStrategicDirty();
        }
        source.sendSuccess(() -> Component.literal(formatStats("manual-step", stats)), true);
        return stats.groupsProcessed();
    }

    private static int perf(CommandSourceStack source) {
        StrategicScheduler.CycleStats stats = StrategicScheduler.lastStats();
        source.sendSuccess(() -> Component.literal(formatStats("last-cycle", stats)), false);
        return 1;
    }

    private static String shortDescription(StrategicGroup group) {
        return group.groupId()
                + " type=" + group.groupType()
                + " faction=" + group.factionId()
                + " state=" + group.state()
                + " pos=" + formatPosition(group.position());
    }

    private static String formatPosition(StrategicPosition position) {
        return position.dimension() + "@"
                + String.format(Locale.ROOT, "%.1f,%.1f", position.x(), position.z());
    }

    private static String formatStats(String label, StrategicScheduler.CycleStats stats) {
        return "strategic " + label
                + " seen=" + stats.groupsSeen()
                + " processed=" + stats.groupsProcessed()
                + " deferred=" + stats.groupsDeferred()
                + " updated=" + stats.groupsUpdated()
                + " moved=" + stats.groupsMoved()
                + " arrived=" + stats.groupsArrived()
                + " clamped=" + stats.groupsClamped()
                + " failed=" + stats.groupsFailed()
                + " cpu=" + String.format(Locale.ROOT, "%.3fms", stats.elapsedMillis());
    }
}
