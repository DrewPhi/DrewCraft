package dev.drewcraft.strategic.simulation;

import dev.drewcraft.DrewCraft;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupType;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.List;
import net.minecraft.server.MinecraftServer;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * Coarse strategic scheduler. It only advances already-cached route progress; it never loads
 * chunks, creates entities, or performs route/path search.
 */
public final class StrategicScheduler {
    private static volatile CycleStats lastStats = CycleStats.empty();
    private static long nextDueGameTime = Long.MIN_VALUE;
    private static long lastObservedGameTime = Long.MIN_VALUE;
    private static int groupCursor;

    private StrategicScheduler() {
    }

    public static void onServerTick(ServerTickEvent.Post event) {
        if (!DrewCraftConfig.STRATEGIC_KERNEL.get()) {
            return;
        }
        MinecraftServer server = event.getServer();
        long now = server.overworld().getGameTime();
        int interval = DrewCraftConfig.STRATEGIC_SCHEDULER_INTERVAL_TICKS.get();

        if (lastObservedGameTime != Long.MIN_VALUE && now < lastObservedGameTime) {
            nextDueGameTime = Long.MIN_VALUE;
            groupCursor = 0;
        }
        lastObservedGameTime = now;
        if (nextDueGameTime != Long.MIN_VALUE && now < nextDueGameTime) {
            return;
        }
        nextDueGameTime = now + interval;

        DrewCraftSavedData data = DrewCraftSavedData.get(server);
        List<StrategicGroup> scheduledGroups = data.strategicGroups();
        if (!DrewCraftConfig.STRATEGIC_HERDS.get()) {
            scheduledGroups = scheduledGroups.stream()
                    .filter(group -> group.groupType() != StrategicGroupType.HERD)
                    .toList();
        }
        CycleStats stats = advanceGroupsFromIndex(
                scheduledGroups,
                now,
                DrewCraftConfig.STRATEGIC_MAX_GROUPS_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_MAX_MILLIS_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_MAX_CATCHUP_SECONDS.get(),
                groupCursor
        );
        groupCursor = stats.nextCursor();
        lastStats = stats;
        if (stats.groupsUpdated() > 0) {
            data.markStrategicDirty();
        }
        if (stats.groupsFailed() > 0) {
            DrewCraft.LOGGER.warn("Strategic scheduler completed with {} malformed/failed group(s)", stats.groupsFailed());
        }
    }

    public static CycleStats advanceGroups(
            Collection<StrategicGroup> groups,
            long currentGameTime,
            int maxGroups,
            double maxMillis,
            double maxCatchupSeconds
    ) {
        return advanceGroupsFromIndex(groups, currentGameTime, maxGroups, maxMillis, maxCatchupSeconds, 0);
    }

    /** Round-robin bounded advancement used by the live scheduler and fairness tests. */
    public static CycleStats advanceGroupsFromIndex(
            Collection<StrategicGroup> groups,
            long currentGameTime,
            int maxGroups,
            double maxMillis,
            double maxCatchupSeconds,
            int startIndex
    ) {
        if (maxGroups < 1) {
            throw new IllegalArgumentException("maxGroups must be positive");
        }
        if (!Double.isFinite(maxMillis) || maxMillis <= 0.0) {
            throw new IllegalArgumentException("maxMillis must be finite and positive");
        }

        List<StrategicGroup> ordered = new ArrayList<>(groups);
        ordered.sort(Comparator.comparing(group -> group.groupId().toString()));
        int total = ordered.size();
        int normalizedStart = total == 0 ? 0 : Math.floorMod(startIndex, total);
        long started = System.nanoTime();
        long deadlineNanos = started + Math.max(1L, (long) (maxMillis * 1_000_000.0));
        int processed = 0;
        int updated = 0;
        int moved = 0;
        int arrived = 0;
        int clamped = 0;
        int failed = 0;

        for (int offset = 0; offset < total; offset++) {
            if (processed >= maxGroups || (processed > 0 && System.nanoTime() >= deadlineNanos)) {
                break;
            }
            StrategicGroup group = ordered.get((normalizedStart + offset) % total);
            processed++;
            try {
                StrategicGroup.AdvanceResult result = group.advanceToGameTime(currentGameTime, maxCatchupSeconds);
                if (result.elapsedSeconds() > 0.0) {
                    updated++;
                }
                if (result.changedPosition()) {
                    moved++;
                }
                if (result.arrived()) {
                    arrived++;
                }
                if (result.catchupClamped()) {
                    clamped++;
                }
            } catch (RuntimeException ex) {
                failed++;
                DrewCraft.LOGGER.error("Strategic group {} failed during coarse simulation", group.groupId(), ex);
            }
        }

        long elapsed = System.nanoTime() - started;
        int nextCursor = total == 0 ? 0 : (normalizedStart + Math.max(1, processed)) % total;
        return new CycleStats(
                ordered.size(),
                processed,
                Math.max(0, ordered.size() - processed),
                updated,
                moved,
                arrived,
                clamped,
                failed,
                elapsed,
                nextCursor
        );
    }

    /** Explicit bounded admin/test advancement that does not move the scheduler's game-time anchor. */
    public static CycleStats advanceBySeconds(
            Collection<StrategicGroup> groups,
            double seconds,
            int maxGroups,
            double maxMillis,
            double maxCatchupSeconds
    ) {
        List<StrategicGroup> ordered = new ArrayList<>(groups);
        ordered.sort(Comparator.comparing(group -> group.groupId().toString()));
        long started = System.nanoTime();
        long deadlineNanos = started + Math.max(1L, (long) (maxMillis * 1_000_000.0));
        int processed = 0;
        int updated = 0;
        int moved = 0;
        int arrived = 0;
        int clamped = 0;
        int failed = 0;

        for (StrategicGroup group : ordered) {
            if (processed >= maxGroups || (processed > 0 && System.nanoTime() >= deadlineNanos)) {
                break;
            }
            processed++;
            try {
                StrategicGroup.AdvanceResult result = group.advanceBySeconds(seconds, maxCatchupSeconds);
                if (result.elapsedSeconds() > 0.0) updated++;
                if (result.changedPosition()) moved++;
                if (result.arrived()) arrived++;
                if (result.catchupClamped()) clamped++;
            } catch (RuntimeException ex) {
                failed++;
            }
        }
        return new CycleStats(
                ordered.size(), processed, Math.max(0, ordered.size() - processed), updated,
                moved, arrived, clamped, failed, System.nanoTime() - started, 0
        );
    }

    public static CycleStats lastStats() {
        return lastStats;
    }

    public static void resetRuntime() {
        nextDueGameTime = Long.MIN_VALUE;
        lastObservedGameTime = Long.MIN_VALUE;
        groupCursor = 0;
        lastStats = CycleStats.empty();
    }

    public record CycleStats(
            int groupsSeen,
            int groupsProcessed,
            int groupsDeferred,
            int groupsUpdated,
            int groupsMoved,
            int groupsArrived,
            int groupsClamped,
            int groupsFailed,
            long elapsedNanos,
            int nextCursor
    ) {
        public static CycleStats empty() {
            return new CycleStats(0, 0, 0, 0, 0, 0, 0, 0, 0L, 0);
        }

        public double elapsedMillis() {
            return elapsedNanos / 1_000_000.0;
        }
    }
}
