package dev.drewcraft.strategic.source;

import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.persistence.DrewCraftSavedData;
import java.util.List;
import net.minecraft.server.MinecraftServer;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/** Bounded source scheduler. It iterates persistent records only and never scans distant chunks. */
public final class SourceProductionScheduler {
    private static long nextDueGameTime = Long.MIN_VALUE;
    private static long lastObservedGameTime = Long.MIN_VALUE;
    private static int sourceCursor;
    private static volatile CycleStats lastStats = CycleStats.empty();

    private SourceProductionScheduler() {
    }

    public static void onServerTick(ServerTickEvent.Post event) {
        if (!DrewCraftConfig.STRATEGIC_KERNEL.get()) return;
        MinecraftServer server = event.getServer();
        long now = server.overworld().getGameTime();
        if (lastObservedGameTime != Long.MIN_VALUE && now < lastObservedGameTime) {
            nextDueGameTime = Long.MIN_VALUE;
            sourceCursor = 0;
        }
        lastObservedGameTime = now;
        if (nextDueGameTime != Long.MIN_VALUE && now < nextDueGameTime) return;
        nextDueGameTime = now + DrewCraftConfig.STRATEGIC_SOURCE_INTERVAL_TICKS.get();

        lastStats = runCycleFromIndex(
                DrewCraftSavedData.get(server),
                now,
                DrewCraftConfig.STRATEGIC_MAX_SOURCES_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_MAX_LAUNCHES_PER_CYCLE.get(),
                DrewCraftConfig.STRATEGIC_SOURCE_ROUTE_RETRY_TICKS.get(),
                sourceCursor,
                SourceLaunchPlanner::plan
        );
        sourceCursor = lastStats.nextCursor();
    }

    /** Deterministic zero-cursor harness used by focused tests/admin tooling. */
    public static CycleStats runCycle(DrewCraftSavedData data, long gameTime,
                                      int maxSources, int maxLaunches, long retryTicks,
                                      Planner planner) {
        return runCycleFromIndex(data, gameTime, maxSources, maxLaunches, retryTicks, 0, planner);
    }

    public static CycleStats runCycleFromIndex(DrewCraftSavedData data, long gameTime,
                                               int maxSources, int maxLaunches, long retryTicks,
                                               int startIndex, Planner planner) {
        long started = System.nanoTime();
        List<SourceRecord> sources = data.sourceRecords();
        int total = sources.size();
        int seen = 0;
        int due = 0;
        int launched = 0;
        int routeFailures = 0;
        int rejectedCommits = 0;
        int normalizedStart = total == 0 ? 0 : Math.floorMod(startIndex, total);

        while (seen < Math.min(maxSources, total) && launched < maxLaunches) {
            SourceRecord source = sources.get((normalizedStart + seen) % total);
            seen++;
            if (!source.canLaunch(gameTime)) continue;
            due++;
            long expectedGeneration = source.generation();
            SourceLaunchPlanner.PlanResult planned = planner.plan(source, gameTime);
            if (!planned.success()) {
                data.postponeSourceLaunch(source.sourceId(), expectedGeneration, gameTime, retryTicks);
                routeFailures++;
                continue;
            }
            if (data.commitSourceLaunch(source.sourceId(), expectedGeneration, planned.group(), gameTime)) {
                launched++;
            } else {
                rejectedCommits++;
            }
        }

        int nextCursor = total == 0 ? 0 : (normalizedStart + Math.max(1, seen)) % total;
        return new CycleStats(
                total, seen, due, launched, routeFailures, rejectedCommits, nextCursor,
                (System.nanoTime() - started) / 1_000_000.0
        );
    }

    public static CycleStats lastStats() { return lastStats; }

    @FunctionalInterface
    public interface Planner {
        SourceLaunchPlanner.PlanResult plan(SourceRecord source, long gameTime);
    }

    public record CycleStats(int totalSources, int sourcesSeen, int sourcesDue, int groupsLaunched,
                             int routeFailures, int rejectedCommits, int nextCursor, double elapsedMillis) {
        static CycleStats empty() { return new CycleStats(0, 0, 0, 0, 0, 0, 0, 0.0); }
    }
}
