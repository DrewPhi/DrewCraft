package dev.drewcraft.strategic.simulation;

import dev.drewcraft.DrewCraft;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.model.StrategicGroup;
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
        }
        lastObservedGameTime = now;
        if (nextDueGameTime != Long.MIN_VALUE && now < nextDueGameTime) {
            return;
        }
        nextDueGameTime = now + interval;

        DrewCraftSavedData data = DrewCraftSavedData.get(server);
        CycleStats stats = advanceGroups(
                data.strategicGroups(),
                now,
                DrewCraftConfig.STRATEGIC_MAX_GROUPS_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_MAX_MILLIS_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_MAX_CATCHUP_SECONDS.get()
        );
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
        if (maxGroups < 1) {
            throw new IllegalArgumentException("maxGroups must be positive");
        }
        if (!Double.isFinite(maxMillis) || maxMillis <= 0.0) {
            throw new IllegalArgumentException("maxMillis must be finite and positive");
        }

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
        return new CycleStats(
                ordered.size(),
                processed,
                Math.max(0, ordered.size() - processed),
                updated,
                moved,
                arrived,
                clamped,
                failed,
                elapsed
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
                moved, arrived, clamped, failed, System.nanoTime() - started
        );
    }

    public static CycleStats lastStats() {
        return lastStats;
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
            long elapsedNanos
    ) {
        public static CycleStats empty() {
            return new CycleStats(0, 0, 0, 0, 0, 0, 0, 0, 0L);
        }

        public double elapsedMillis() {
            return elapsedNanos / 1_000_000.0;
        }
    }
}
