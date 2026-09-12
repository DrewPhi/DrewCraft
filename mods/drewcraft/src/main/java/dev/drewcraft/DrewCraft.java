package dev.drewcraft;

import com.mojang.logging.LogUtils;
import dev.drewcraft.command.DrewCraftCommands;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.net.DrewCraftProtocol;
import dev.drewcraft.persistence.DrewCraftSavedData;
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
        modContainer.registerConfig(ModConfig.Type.SERVER, DrewCraftConfig.SPEC);
        NeoForge.EVENT_BUS.addListener(DrewCraftCommands::register);

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
