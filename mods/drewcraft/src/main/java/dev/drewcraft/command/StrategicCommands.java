package dev.drewcraft.command;

import com.mojang.brigadier.arguments.DoubleArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.routing.StrategicCell;
import dev.drewcraft.strategic.routing.StrategicRoutingService;
import dev.drewcraft.strategic.routing.StrategicTerrainCapture;
import dev.drewcraft.strategic.routing.StrategicTerrainClass;
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
                .then(Commands.literal("create-test").executes(context -> createTest(context.getSource())))
                .then(Commands.literal("list").executes(context -> list(context.getSource())))
                .then(Commands.literal("inspect")
                        .then(Commands.argument("groupId", StringArgumentType.word())
                                .executes(context -> inspect(context.getSource(), StringArgumentType.getString(context, "groupId")))))
                .then(Commands.literal("destination")
                        .then(Commands.argument("groupId", StringArgumentType.word())
                                .then(Commands.argument("x", DoubleArgumentType.doubleArg())
                                        .then(Commands.argument("z", DoubleArgumentType.doubleArg())
                                                .executes(context -> destination(
                                                        context.getSource(),
                                                        StringArgumentType.getString(context, "groupId"),
                                                        DoubleArgumentType.getDouble(context, "x"),
                                                        DoubleArgumentType.getDouble(context, "z")
                                                ))))))
                .then(Commands.literal("route")
                        .then(Commands.argument("groupId", StringArgumentType.word())
                                .executes(context -> route(context.getSource(), StringArgumentType.getString(context, "groupId")))))
                .then(Commands.literal("eta")
                        .then(Commands.argument("groupId", StringArgumentType.word())
                                .executes(context -> eta(context.getSource(), StringArgumentType.getString(context, "groupId")))))
                .then(Commands.literal("step")
                        .then(Commands.argument("seconds", IntegerArgumentType.integer(1, 3600))
                                .executes(context -> step(context.getSource(), IntegerArgumentType.getInteger(context, "seconds")))))
                .then(Commands.literal("perf").executes(context -> perf(context.getSource())))
                .then(Commands.literal("routing-perf").executes(context -> routingPerf(context.getSource())))
                .then(Commands.literal("terrain")
                        .then(Commands.literal("capture-here").executes(context -> captureHere(context.getSource())))
                        .then(Commands.literal("set-here")
                                .then(Commands.argument("class", StringArgumentType.word())
                                        .executes(context -> setTerrainHere(
                                                context.getSource(),
                                                StringArgumentType.getString(context, "class")
                                        )))));
    }

    private static int createTest(CommandSourceStack source) {
        String dimension = source.getLevel().dimension().location().toString();
        StrategicPosition start = new StrategicPosition(dimension, source.getPosition().x, source.getPosition().z);
        StrategicPosition destination = new StrategicPosition(dimension, start.x() + 10000.0, start.z());
        StrategicRoutingService.RoutingResult planned = StrategicRoutingService.plan(start, destination);
        if (!planned.success()) {
            source.sendFailure(Component.literal("Strategic route failed: " + planned.stats().status()));
            return 0;
        }
        StrategicGroup group = StrategicGroup.testGroup(start, destination, source.getLevel().getGameTime());
        group.assignRoute(planned.route(), source.getLevel().getGameTime());
        DrewCraftSavedData.get(source.getServer()).upsertStrategicGroup(group);
        source.sendSuccess(() -> Component.literal(
                "Created routed strategic test group " + group.groupId()
                        + " at " + formatPosition(group.position())
                        + " -> " + formatPosition(group.destination())
                        + " waypoints=" + group.route().waypoints().size()
                        + " eta=" + String.format(Locale.ROOT, "%.1fs", group.etaSeconds())
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
        if (groups.size() > shown) source.sendSuccess(() -> Component.literal("... " + (groups.size() - shown) + " more"), false);
        return groups.size();
    }

    private static int inspect(CommandSourceStack source, String rawId) {
        StrategicGroup group = find(source, rawId);
        if (group == null) return 0;
        source.sendSuccess(() -> Component.literal(
                shortDescription(group)
                        + " destination=" + formatPosition(group.destination())
                        + " routeCursor=" + group.route().cursor() + "/" + group.route().waypoints().size()
                        + " speed=" + String.format(Locale.ROOT, "%.2f", group.movementSpeedBlocksPerSecond()) + " effective-b/s"
                        + " strength=" + group.totalStrength()
                        + " eta=" + String.format(Locale.ROOT, "%.1fs", group.etaSeconds())
                        + " lastSimGameTime=" + group.lastSimulatedGameTime()
        ), false);
        return 1;
    }

    private static int destination(CommandSourceStack source, String rawId, double x, double z) {
        StrategicGroup group = find(source, rawId);
        if (group == null) return 0;
        StrategicPosition destination = new StrategicPosition(group.position().dimension(), x, z);
        StrategicRoutingService.RoutingResult planned = StrategicRoutingService.plan(group.position(), destination);
        if (!planned.success()) {
            source.sendFailure(Component.literal("Route failed: " + planned.stats().status()
                    + " expanded=" + planned.stats().expandedNodes()));
            return 0;
        }
        group.assignRoute(planned.route(), source.getLevel().getGameTime());
        DrewCraftSavedData.get(source.getServer()).upsertStrategicGroup(group);
        source.sendSuccess(() -> Component.literal(
                "Assigned route to " + group.groupId()
                        + " waypoints=" + group.route().waypoints().size()
                        + " weightedCost=" + String.format(Locale.ROOT, "%.1f", planned.stats().weightedCost())
                        + " eta=" + String.format(Locale.ROOT, "%.1fs", group.etaSeconds())
                        + " cacheHit=" + planned.stats().cacheHit()
        ), true);
        return 1;
    }

    private static int route(CommandSourceStack source, String rawId) {
        StrategicGroup group = find(source, rawId);
        if (group == null) return 0;
        source.sendSuccess(() -> Component.literal(
                "route " + group.groupId()
                        + " cursor=" + group.route().cursor() + "/" + group.route().waypoints().size()
                        + " remainingDistance=" + String.format(Locale.ROOT, "%.1f", group.route().remainingDistanceFrom(group.position()))
                        + " remainingCost=" + String.format(Locale.ROOT, "%.1f", group.route().remainingCostFrom(group.position()))
                        + " destination=" + formatPosition(group.destination())
        ), false);
        int limit = Math.min(8, group.route().waypoints().size());
        for (int i = 0; i < limit; i++) {
            int index = i;
            source.sendSuccess(() -> Component.literal("  [" + index + "] " + formatPosition(group.route().waypoints().get(index))), false);
        }
        if (group.route().waypoints().size() > limit) {
            source.sendSuccess(() -> Component.literal("  ... " + (group.route().waypoints().size() - limit) + " more waypoints"), false);
        }
        return 1;
    }

    private static int eta(CommandSourceStack source, String rawId) {
        StrategicGroup group = find(source, rawId);
        if (group == null) return 0;
        source.sendSuccess(() -> Component.literal(
                "ETA " + group.groupId() + " = " + String.format(Locale.ROOT, "%.1fs (%.1f min)", group.etaSeconds(), group.etaSeconds() / 60.0)
        ), false);
        return 1;
    }

    private static int step(CommandSourceStack source, int seconds) {
        DrewCraftSavedData data = DrewCraftSavedData.get(source.getServer());
        StrategicScheduler.CycleStats stats = StrategicScheduler.advanceBySeconds(
                data.strategicGroups(), seconds, DrewCraftConfig.STRATEGIC_MAX_GROUPS_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_MAX_MILLIS_PER_CYCLE.get(), DrewCraftConfig.STRATEGIC_MAX_CATCHUP_SECONDS.get());
        if (stats.groupsUpdated() > 0) data.markStrategicDirty();
        source.sendSuccess(() -> Component.literal(formatStats("manual-step", stats)), true);
        return stats.groupsProcessed();
    }

    private static int perf(CommandSourceStack source) {
        source.sendSuccess(() -> Component.literal(formatStats("last-cycle", StrategicScheduler.lastStats())), false);
        return 1;
    }

    private static int routingPerf(CommandSourceStack source) {
        StrategicRoutingService.ServiceStats stats = StrategicRoutingService.stats();
        source.sendSuccess(() -> Component.literal(
                "routing cell=" + stats.cellSizeBlocks() + "b"
                        + " knownCells=" + stats.knownTerrainCells()
                        + " terrainVersion=" + stats.terrainVersion()
                        + " cache=" + stats.routeCacheEntries()
                        + " hits=" + stats.cacheHits()
                        + " misses=" + stats.cacheMisses()
                        + " success=" + stats.successfulPlans()
                        + " failed=" + stats.failedPlans()
                        + " lastStatus=" + stats.lastPlan().status()
                        + " lastExpanded=" + stats.lastPlan().expandedNodes()
                        + " lastCpu=" + String.format(Locale.ROOT, "%.3fms", stats.lastPlan().elapsedMillis())
        ), false);
        return 1;
    }

    private static int captureHere(CommandSourceStack source) {
        StrategicTerrainCostMapAccess access = currentCell(source);
        int captured = 0;
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                StrategicTerrainCapture.CaptureResult result = StrategicTerrainCapture.captureLoadedCell(
                        source.getLevel(), access.cell().offset(dx, dz), StrategicRoutingService.terrainCosts());
                if (result.captured()) captured++;
            }
        }
        int finalCaptured = captured;
        source.sendSuccess(() -> Component.literal("Captured " + finalCaptured + "/9 already-loaded coarse terrain cells; no chunks were force-loaded."), true);
        return captured;
    }

    private static int setTerrainHere(CommandSourceStack source, String rawClass) {
        StrategicTerrainClass terrainClass;
        try {
            terrainClass = StrategicTerrainClass.valueOf(rawClass.toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            source.sendFailure(Component.literal("Unknown terrain class. Use ROAD, BRIDGE, NORMAL, UNKNOWN, DIFFICULT, WATER, or BLOCKED."));
            return 0;
        }
        StrategicTerrainCostMapAccess access = currentCell(source);
        StrategicRoutingService.terrainCosts().put(access.cell(), terrainClass);
        source.sendSuccess(() -> Component.literal("Set coarse cell " + access.cell().x() + "," + access.cell().z() + " to " + terrainClass + "; route-cache version invalidated."), true);
        return 1;
    }

    private static StrategicTerrainCostMapAccess currentCell(CommandSourceStack source) {
        String dimension = source.getLevel().dimension().location().toString();
        StrategicPosition position = new StrategicPosition(dimension, source.getPosition().x, source.getPosition().z);
        int cellSize = StrategicRoutingService.terrainCosts().cellSizeBlocks();
        return new StrategicTerrainCostMapAccess(StrategicCell.fromPosition(position, cellSize));
    }

    private static StrategicGroup find(CommandSourceStack source, String rawId) {
        UUID groupId;
        try {
            groupId = UUID.fromString(rawId);
        } catch (IllegalArgumentException ex) {
            source.sendFailure(Component.literal("Invalid group UUID: " + rawId));
            return null;
        }
        StrategicGroup group = DrewCraftSavedData.get(source.getServer()).strategicGroup(groupId).orElse(null);
        if (group == null) source.sendFailure(Component.literal("Unknown strategic group: " + groupId));
        return group;
    }

    private static String shortDescription(StrategicGroup group) {
        return group.groupId() + " type=" + group.groupType() + " faction=" + group.factionId()
                + " state=" + group.state() + " pos=" + formatPosition(group.position());
    }

    private static String formatPosition(StrategicPosition position) {
        return position.dimension() + "@" + String.format(Locale.ROOT, "%.1f,%.1f", position.x(), position.z());
    }

    private static String formatStats(String label, StrategicScheduler.CycleStats stats) {
        return "strategic " + label + " seen=" + stats.groupsSeen() + " processed=" + stats.groupsProcessed()
                + " deferred=" + stats.groupsDeferred() + " updated=" + stats.groupsUpdated() + " moved=" + stats.groupsMoved()
                + " arrived=" + stats.groupsArrived() + " clamped=" + stats.groupsClamped() + " failed=" + stats.groupsFailed()
                + " cpu=" + String.format(Locale.ROOT, "%.3fms", stats.elapsedMillis());
    }

    private record StrategicTerrainCostMapAccess(StrategicCell cell) {
    }
}
