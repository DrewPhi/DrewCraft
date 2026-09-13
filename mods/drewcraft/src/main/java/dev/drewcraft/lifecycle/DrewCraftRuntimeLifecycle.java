package dev.drewcraft.lifecycle;

import dev.drewcraft.radar.RadarEngine;
import dev.drewcraft.radar.WeatherRadarEngine;
import dev.drewcraft.strategic.encounter.StrategicMaterializationRuntime;
import dev.drewcraft.strategic.objective.StrategicObjectiveCatalog;
import dev.drewcraft.strategic.routing.StrategicRoutingService;
import dev.drewcraft.strategic.siege.SiegeRuntime;
import dev.drewcraft.strategic.simulation.StrategicScheduler;
import dev.drewcraft.strategic.source.SourceProductionScheduler;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;

/** Clears process-local caches and cursors when an integrated or dedicated server ends. */
public final class DrewCraftRuntimeLifecycle {
    private DrewCraftRuntimeLifecycle() { }

    public static void onServerStopped(ServerStoppedEvent event) {
        StrategicScheduler.resetRuntime();
        StrategicMaterializationRuntime.resetRuntime();
        SourceProductionScheduler.resetRuntime();
        SiegeRuntime.resetRuntime();
        StrategicObjectiveCatalog.clear();
        StrategicRoutingService.reset();
        RadarEngine.get().clearCache();
        WeatherRadarEngine.get().clearCache();
    }
}
