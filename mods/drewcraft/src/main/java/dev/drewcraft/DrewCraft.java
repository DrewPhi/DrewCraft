package dev.drewcraft;

import com.mojang.logging.LogUtils;
import dev.drewcraft.command.DrewCraftCommands;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.flak.FlakRuntime;
import dev.drewcraft.content.DrewCraftBlocks;
import dev.drewcraft.net.DrewCraftProtocol;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.standard.StandardGrantRuntime;
import dev.drewcraft.lifecycle.DrewCraftRuntimeLifecycle;
import dev.drewcraft.strategic.encounter.StrategicMaterializationRuntime;
import dev.drewcraft.strategic.production.ProductionStrategicSeedRuntime;
import dev.drewcraft.strategic.siege.SiegeRuntime;
import dev.drewcraft.strategic.simulation.StrategicScheduler;
import dev.drewcraft.strategic.source.SourceProductionScheduler;
import dev.drewcraft.world.OverworldBoundaryRuntime;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.neoforge.common.NeoForge;
import org.slf4j.Logger;

@Mod(DrewCraft.MOD_ID)
public final class DrewCraft {
    public static final String MOD_ID = "drewcraft";
    public static final Logger LOGGER = LogUtils.getLogger();

    private static volatile String modVersion = "unknown";

    public DrewCraft(IEventBus modEventBus, ModContainer modContainer) {
        modVersion = modContainer.getModInfo().getVersion().toString();
        DrewCraftBlocks.register(modEventBus);
        modContainer.registerConfig(ModConfig.Type.SERVER, DrewCraftConfig.SPEC);
        NeoForge.EVENT_BUS.addListener(DrewCraftCommands::register);
        NeoForge.EVENT_BUS.addListener(StandardGrantRuntime::onPlayerLoggedIn);
        NeoForge.EVENT_BUS.addListener(OverworldBoundaryRuntime::onPlayerTick);
        NeoForge.EVENT_BUS.addListener(StrategicScheduler::onServerTick);
        NeoForge.EVENT_BUS.addListener(StrategicMaterializationRuntime::onServerTick);
        NeoForge.EVENT_BUS.addListener(StrategicMaterializationRuntime::onLivingDeath);
        NeoForge.EVENT_BUS.addListener(StrategicMaterializationRuntime::onEntityJoinLevel);
        NeoForge.EVENT_BUS.addListener(SourceProductionScheduler::onServerTick);
        NeoForge.EVENT_BUS.addListener(SiegeRuntime::onServerTick);
        NeoForge.EVENT_BUS.addListener(FlakRuntime::onServerTick);
        NeoForge.EVENT_BUS.addListener(ProductionStrategicSeedRuntime::onServerStarted);
        NeoForge.EVENT_BUS.addListener(ProductionStrategicSeedRuntime::onChunkLoad);
        NeoForge.EVENT_BUS.addListener(ProductionStrategicSeedRuntime::onServerStopped);
        NeoForge.EVENT_BUS.addListener(DrewCraftRuntimeLifecycle::onServerStopped);

        LOGGER.info(
                "DrewCraft integration platform {} loaded (protocol {}, persistence schema {})",
                modVersion,
                DrewCraftProtocol.CURRENT,
                DrewCraftSavedData.CURRENT_SCHEMA_VERSION
        );
    }

    public static String version() {
        return modVersion;
    }
}
