package dev.drewcraft.command;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.herd.WildHerdDescriptor;
import dev.drewcraft.strategic.herd.WildHerdRegistration;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupType;
import java.util.List;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.EntityType;

/** Admin/debug surface for the additive BP7 wildlife layer. */
final class HerdCommands {
    private HerdCommands() {
    }

    static LiteralArgumentBuilder<CommandSourceStack> node() {
        return Commands.literal("herd")
                .then(Commands.literal("create-test")
                        .then(Commands.argument("species", StringArgumentType.word())
                                .then(Commands.argument("count", IntegerArgumentType.integer(1, 2048))
                                        .executes(context -> createTest(
                                                context.getSource(),
                                                StringArgumentType.getString(context, "species"),
                                                IntegerArgumentType.getInteger(context, "count")
                                        )))))
                .then(Commands.literal("list").executes(context -> list(context.getSource())))
                .then(Commands.literal("ecology").executes(context -> ecology(context.getSource())));
    }

    private static int createTest(CommandSourceStack source, String species, int count) {
        if (!DrewCraftConfig.STRATEGIC_HERDS.get()) {
            source.sendFailure(Component.literal("Strategic herds are disabled; existing herd records are preserved and ordinary animals are unaffected."));
            return 0;
        }
        if (EntityType.byString(species).isEmpty()) {
            source.sendFailure(Component.literal("Unknown entity type: " + species));
            return 0;
        }
        String dimension = source.getLevel().dimension().location().toString();
        int x = (int) Math.floor(source.getPosition().x);
        int z = (int) Math.floor(source.getPosition().z);
        WildHerdDescriptor descriptor = new WildHerdDescriptor(
                dimension, species, x, z, x + 2048, z, count, 1.25
        );
        WildHerdRegistration.RegistrationResult result = WildHerdRegistration.register(
                DrewCraftSavedData.get(source.getServer()), descriptor, source.getLevel().getGameTime()
        );
        if (!result.success()) {
            source.sendFailure(Component.literal("Herd registration failed: " + result.status()));
            return 0;
        }
        StrategicGroup herd = result.group();
        source.sendSuccess(() -> Component.literal(
                (result.created() ? "Created" : "Found existing") + " strategic herd " + herd.groupId()
                        + " species=" + species
                        + " strength=" + herd.totalStrength()
                        + " target=" + herd.destination().dimension() + "@"
                        + String.format(java.util.Locale.ROOT, "%.1f,%.1f", herd.destination().x(), herd.destination().z())
        ), true);
        return 1;
    }

    private static int list(CommandSourceStack source) {
        List<StrategicGroup> herds = DrewCraftSavedData.get(source.getServer()).strategicGroups().stream()
                .filter(group -> group.groupType() == StrategicGroupType.HERD)
                .toList();
        source.sendSuccess(() -> Component.literal("Strategic wild herds: " + herds.size()
                + " | runtime=" + (DrewCraftConfig.STRATEGIC_HERDS.get() ? "enabled" : "disabled/preserved")), false);
        for (StrategicGroup herd : herds.stream().limit(20).toList()) {
            source.sendSuccess(() -> Component.literal(
                    herd.groupId() + " strength=" + herd.totalStrength()
                            + " state=" + herd.state()
                            + " composition=" + herd.composition()
                            + " target=" + herd.destination().dimension() + "@"
                            + String.format(java.util.Locale.ROOT, "%.1f,%.1f", herd.destination().x(), herd.destination().z())
            ), false);
        }
        return herds.size();
    }

    private static int ecology(CommandSourceStack source) {
        source.sendSuccess(() -> Component.literal(
                "BP7 ecology isolation: strategicHerds=" + DrewCraftConfig.STRATEGIC_HERDS.get()
                        + "; explicit strategic herds only; existing/natural/bred/named/leashed/tamed/penned/spawner animals are never absorbed; vanilla spawning and spawners are not quota-managed by DrewCraft."
        ), false);
        return 1;
    }
}
