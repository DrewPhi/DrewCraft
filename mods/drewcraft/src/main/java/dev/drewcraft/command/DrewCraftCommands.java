package dev.drewcraft.command;

import com.mojang.brigadier.CommandDispatcher;
import dev.drewcraft.DrewCraft;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.net.DrewCraftProtocol;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.service.DrewCraftServices;
import dev.drewcraft.service.power.PowerSample;
import dev.drewcraft.service.terrain.TerrainSample;
import dev.drewcraft.service.weather.WeatherSample;
import java.util.Locale;
import java.util.OptionalDouble;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

public final class DrewCraftCommands {
    private DrewCraftCommands() {
    }

    public static void register(RegisterCommandsEvent event) {
        CommandDispatcher<CommandSourceStack> dispatcher = event.getDispatcher();
        dispatcher.register(
                Commands.literal("drewcraft")
                        .requires(source -> source.hasPermission(2))
                        .then(Commands.literal("status")
                                .executes(context -> status(context.getSource())))
                        .then(Commands.literal("state")
                                .then(Commands.literal("touch")
                                        .executes(context -> touchState(context.getSource()))))
                        .then(Commands.literal("env")
                                .then(Commands.literal("sample")
                                        .executes(context -> sampleEnvironment(context.getSource()))))
                        .then(Commands.literal("power")
                                .then(Commands.literal("sample")
                                        .executes(context -> samplePower(context.getSource()))))
        );
    }

    private static int status(CommandSourceStack source) {
        DrewCraftSavedData data = DrewCraftSavedData.get(source.getServer());
        source.sendSuccess(() -> Component.literal(
                "DrewCraft " + DrewCraft.version()
                        + " | protocol=" + DrewCraftProtocol.CURRENT
                        + " | persistenceSchema=" + DrewCraftSavedData.CURRENT_SCHEMA_VERSION
                        + " | lastTouched=" + data.lastTouchedGameTime()
        ), false);
        source.sendSuccess(() -> Component.literal("Feature flags: " + DrewCraftConfig.integrationSummary()), false);
        return 1;
    }

    private static int touchState(CommandSourceStack source) {
        long gameTime = source.getLevel().getGameTime();
        DrewCraftSavedData.get(source.getServer()).touch(gameTime);
        source.sendSuccess(() -> Component.literal("DrewCraft SavedData marked dirty at gameTime=" + gameTime), true);
        return 1;
    }

    private static int sampleEnvironment(CommandSourceStack source) {
        BlockPos position = BlockPos.containing(source.getPosition());
        TerrainSample terrain = DrewCraftServices.terrain().sample(source.getLevel(), position);
        WeatherSample weather = DrewCraftServices.weather().sample(source.getLevel(), position);

        source.sendSuccess(() -> Component.literal(
                "DrewCraft environment @ " + source.getLevel().dimension().location()
                        + " " + position.getX() + " " + position.getY() + " " + position.getZ()
        ), false);
        source.sendSuccess(() -> Component.literal(formatTerrain(terrain)), false);
        source.sendSuccess(() -> Component.literal(formatWeather(weather)), false);
        return terrain.available() || weather.available() ? 1 : 0;
    }

    private static int samplePower(CommandSourceStack source) {
        BlockPos position = BlockPos.containing(source.getPosition());
        PowerSample power = DrewCraftServices.power().sample(source.getLevel(), position);
        source.sendSuccess(() -> Component.literal(formatPower(power)), false);
        return power.available() ? 1 : 0;
    }

    private static String formatTerrain(TerrainSample sample) {
        if (!sample.available()) {
            return "terrain[" + sample.providerId() + "] unavailable: " + sample.status();
        }
        return "terrain[" + sample.providerId() + "]"
                + " surfaceY=" + sample.surfaceY().orElseThrow()
                + " biome=" + sample.biomeId().orElse("unknown")
                + " surfaceBlock=" + sample.surfaceBlockId().orElse("unknown")
                + " seaLevel=" + sample.seaLevel().orElseThrow()
                + " | " + sample.status();
    }

    private static String formatWeather(WeatherSample sample) {
        if (!sample.available()) {
            return "weather[" + sample.providerId() + "] unavailable: " + sample.status();
        }
        return "weather[" + sample.providerId() + "]"
                + " temp=" + number(sample.temperatureC(), "%.2fC")
                + " wind=" + number(sample.windSpeedMps(), "%.2fm/s")
                + " angle=" + number(sample.windAngleRad(), "%.3frad")
                + " rain=" + number(sample.rainIntensity(), "%.3f")
                + " cloud=" + number(sample.cloudCover(), "%.3f")
                + " storm=" + sample.storming().map(String::valueOf).orElse("n/a")
                + " snow=" + sample.snowing().map(String::valueOf).orElse("n/a")
                + " pressure=" + number(sample.pressureHpa(), "%.2fhPa")
                + " humidity=" + number(sample.humidityRelative(), "%.3f")
                + " visibility=" + number(sample.visibilityMeters(), "%.0fm")
                + " severity=" + number(sample.severity01(), "%.3f")
                + " | " + sample.status();
    }

    private static String formatPower(PowerSample sample) {
        if (!sample.available()) {
            return "power[" + sample.providerId() + "] unavailable: " + sample.status();
        }
        String source = sample.sourcePosition()
                .map(pos -> pos.getX() + "," + pos.getY() + "," + pos.getZ())
                .orElse("none");
        return "power[" + sample.providerId() + "]"
                + " powered=" + sample.kineticallyPowered().map(String::valueOf).orElse("n/a")
                + " speed=" + number(sample.speedRpm(), "%.2frpm")
                + " theoretical=" + number(sample.theoreticalSpeedRpm(), "%.2frpm")
                + " overstressed=" + sample.overstressed().map(String::valueOf).orElse("n/a")
                + " network=" + sample.networkPresent().map(String::valueOf).orElse("n/a")
                + " source=" + source
                + " | " + sample.status();
    }

    private static String number(OptionalDouble value, String format) {
        return value.isPresent() ? String.format(Locale.ROOT, format, value.getAsDouble()) : "n/a";
    }
}
