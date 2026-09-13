package dev.drewcraft.command;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import dev.drewcraft.content.DrewCraftBlocks;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.source.SourceClass;
import dev.drewcraft.strategic.source.SourceCorePosition;
import dev.drewcraft.strategic.source.SourceDescriptor;
import dev.drewcraft.strategic.source.SourceProductionScheduler;
import dev.drewcraft.strategic.source.SourceRecord;
import dev.drewcraft.strategic.source.SourceState;
import java.util.List;
import java.util.UUID;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;

final class SourceCommands {
    private SourceCommands() {
    }

    static LiteralArgumentBuilder<CommandSourceStack> node() {
        return Commands.literal("source")
                .then(Commands.literal("create-test").executes(context -> createTest(context.getSource())))
                .then(Commands.literal("list").executes(context -> list(context.getSource())))
                .then(Commands.literal("inspect")
                        .then(Commands.argument("sourceId", StringArgumentType.word())
                                .executes(context -> inspect(context.getSource(), StringArgumentType.getString(context, "sourceId")))))
                .then(Commands.literal("clear")
                        .then(Commands.argument("sourceId", StringArgumentType.word())
                                .executes(context -> clear(context.getSource(), StringArgumentType.getString(context, "sourceId")))))
                .then(Commands.literal("perf").executes(context -> perf(context.getSource())));
    }

    private static int createTest(CommandSourceStack commandSource) {
        BlockPos pos = BlockPos.containing(commandSource.getPosition());
        String dimension = commandSource.getLevel().dimension().location().toString();
        SourceDescriptor descriptor = new SourceDescriptor(
                dimension,
                "drewcraft:test_source",
                pos.getX(), pos.getY(), pos.getZ(),
                new SourceCorePosition(dimension, pos.getX(), pos.getY(), pos.getZ()),
                SourceClass.TEST,
                "drewcraft:test_hostile"
        );
        DrewCraftSavedData data = DrewCraftSavedData.get(commandSource.getServer());
        DrewCraftSavedData.DiscoverSourceResult result = data.discoverSource(
                descriptor, commandSource.getLevel().getGameTime()
        );
        if (result.source().state() != SourceState.CLEARED) {
            commandSource.getLevel().setBlock(pos, DrewCraftBlocks.SOURCE_CORE.get().defaultBlockState(), 3);
        }
        commandSource.sendSuccess(() -> Component.literal(
                (result.created() ? "Discovered" : "Rediscovered") + " test hostile source "
                        + result.source().sourceId() + " state=" + result.source().state()
                        + " core=" + formatCore(result.source().corePosition())
        ), true);
        return result.created() ? 1 : 0;
    }

    private static int list(CommandSourceStack commandSource) {
        List<SourceRecord> sources = DrewCraftSavedData.get(commandSource.getServer()).sourceRecords();
        commandSource.sendSuccess(() -> Component.literal("Strategic sources: " + sources.size()), false);
        for (int i = 0; i < Math.min(20, sources.size()); i++) {
            SourceRecord source = sources.get(i);
            commandSource.sendSuccess(() -> Component.literal(shortDescription(source)), false);
        }
        return sources.size();
    }

    private static int inspect(CommandSourceStack commandSource, String rawId) {
        SourceRecord source = find(commandSource, rawId);
        if (source == null) return 0;
        long groups = DrewCraftSavedData.get(commandSource.getServer()).strategicGroups().stream()
                .filter(group -> group.sourceId().map(source.sourceId()::equals).orElse(false))
                .count();
        commandSource.sendSuccess(() -> Component.literal(
                shortDescription(source)
                        + " structure=" + source.structureId()
                        + " anchor=" + source.anchorX() + "," + source.anchorY() + "," + source.anchorZ()
                        + " core=" + formatCore(source.corePosition())
                        + " budget=" + source.populationBudget()
                        + " launchStrength=" + source.launchStrength()
                        + " nextAction=" + source.nextActionGameTime()
                        + " generation=" + source.generation()
                        + " launches=" + source.launchSerial()
                        + " existingGroups=" + groups
                        + source.clearedAtGameTime().map(time -> " clearedAt=" + time).orElse("")
                        + source.clearCause().map(cause -> " cause=" + cause).orElse("")
                        + source.clearedBy().map(actor -> " by=" + actor).orElse("")
        ), false);
        return 1;
    }

    private static int clear(CommandSourceStack commandSource, String rawId) {
        SourceRecord source = find(commandSource, rawId);
        if (source == null) return 0;
        boolean changed = DrewCraftSavedData.get(commandSource.getServer()).clearSource(
                source.sourceId(), commandSource.getLevel().getGameTime(), "ADMIN", commandSource.getTextName()
        );
        if (changed) {
            commandSource.getServer().overworld().getDataStorage().save();
        }
        commandSource.sendSuccess(() -> Component.literal(
                "Source " + source.sourceId() + (changed ? " permanently CLEARED" : " was already CLEARED")
        ), true);
        return changed ? 1 : 0;
    }

    private static int perf(CommandSourceStack commandSource) {
        SourceProductionScheduler.CycleStats stats = SourceProductionScheduler.lastStats();
        commandSource.sendSuccess(() -> Component.literal(
                "source-cycle total=" + stats.totalSources()
                        + " seen=" + stats.sourcesSeen()
                        + " due=" + stats.sourcesDue()
                        + " launched=" + stats.groupsLaunched()
                        + " routeFailures=" + stats.routeFailures()
                        + " rejectedCommits=" + stats.rejectedCommits()
                        + " nextCursor=" + stats.nextCursor()
                        + " cpu=" + String.format(java.util.Locale.ROOT, "%.3fms", stats.elapsedMillis())
        ), false);
        return 1;
    }

    private static SourceRecord find(CommandSourceStack commandSource, String rawId) {
        UUID id;
        try {
            id = UUID.fromString(rawId);
        } catch (IllegalArgumentException ex) {
            commandSource.sendFailure(Component.literal("Invalid source UUID: " + rawId));
            return null;
        }
        SourceRecord source = DrewCraftSavedData.get(commandSource.getServer()).sourceRecord(id).orElse(null);
        if (source == null) commandSource.sendFailure(Component.literal("Unknown strategic source: " + id));
        return source;
    }

    private static String shortDescription(SourceRecord source) {
        return source.sourceId() + " class=" + source.sourceClass() + " faction=" + source.factionId()
                + " state=" + source.state() + " budget=" + source.populationBudget();
    }

    private static String formatCore(SourceCorePosition core) {
        return core.dimension() + "@" + core.x() + "," + core.y() + "," + core.z();
    }
}
