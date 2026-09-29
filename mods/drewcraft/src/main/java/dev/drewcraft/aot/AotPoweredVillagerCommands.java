package dev.drewcraft.aot;

import dev.drewcraft.DrewCraft;
import java.lang.reflect.Method;
import java.util.Collection;
import java.util.UUID;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.npc.Villager;

/** Operator-only test helper; the AOT power lives in SavedData, not an entity tag. */
public final class AotPoweredVillagerCommands {
    private AotPoweredVillagerCommands() {}

    public static com.mojang.brigadier.builder.LiteralArgumentBuilder<CommandSourceStack> node() {
        return Commands.literal("test-warhammer-villager")
                .then(Commands.argument("player", EntityArgument.player())
                        .executes(ctx -> spawn(ctx.getSource(), EntityArgument.getPlayer(ctx, "player"))));
    }

    private static int spawn(CommandSourceStack source, ServerPlayer player) {
        ServerLevel level = player.serverLevel();
        if (!level.dimension().location().toString().equals("dannys-aot:paradis")) {
            source.sendFailure(Component.literal("The test villager can only be spawned in Paradis."));
            return 0;
        }

        Villager villager = null;
        Object powerData = null;
        Object warhammer = null;
        Method removePower = null;
        boolean registered = false;
        try {
            Class<?> powerType = Class.forName("daot.TitanPowerType");
            for (Object candidate : powerType.getEnumConstants()) {
                if (((Enum<?>) candidate).name().equals("WARHAMMER")) warhammer = candidate;
            }
            if (warhammer == null) throw new IllegalStateException("Warhammer power is unavailable");

            Class<?> dataType = Class.forName("daot.TitanPowerData");
            powerData = dataType.getMethod("get", ServerLevel.class).invoke(null, level);
            Object playerHolder = dataType.getMethod("getPlayerWithPower", powerType)
                    .invoke(powerData, warhammer);
            Collection<?> villagerHolders = (Collection<?>) dataType
                    .getMethod("getVillagersWithPower", powerType).invoke(powerData, warhammer);
            if (playerHolder != null || !villagerHolders.isEmpty()) {
                source.sendFailure(Component.literal("Warhammer power already has a holder; no villager spawned."));
                return 0;
            }

            Method setPower = dataType.getMethod("setPower", UUID.class, powerType);
            Method getPower = dataType.getMethod("getPower", UUID.class);
            removePower = dataType.getMethod("removePower", UUID.class);
            Method broadcast = Class.forName("daot.TitanPowerHelper")
                    .getMethod("broadcastPowerAdd", ServerLevel.class, int.class, powerType);

            double yaw = Math.toRadians(player.getYRot());
            double x = player.getX() - Math.sin(yaw) * 2.5;
            double y = player.getY();
            double z = player.getZ() + Math.cos(yaw) * 2.5;
            BlockPos pos = BlockPos.containing(x, y, z);
            if (!level.isInWorldBounds(pos) || !level.getWorldBorder().isWithinBounds(pos)) {
                source.sendFailure(Component.literal("The position in front of the player is outside world bounds."));
                return 0;
            }

            villager = EntityType.VILLAGER.create(level);
            if (villager == null) throw new IllegalStateException("Villager entity type is unavailable");
            villager.moveTo(x, y, z, player.getYRot() + 180, 0);
            villager.setNoAi(true);
            villager.setPersistenceRequired();
            villager.setCustomName(Component.literal("Warhammer Test Villager"));
            villager.setCustomNameVisible(true);
            if (!level.addFreshEntity(villager)) {
                throw new IllegalStateException("Server refused to spawn the villager");
            }

            setPower.invoke(powerData, villager.getUUID(), warhammer);
            registered = true;
            if (getPower.invoke(powerData, villager.getUUID()) != warhammer) {
                throw new IllegalStateException("AOT did not retain the villager's Warhammer power");
            }
            broadcast.invoke(null, level, villager.getId(), warhammer);
            UUID id = villager.getUUID();
            source.sendSuccess(() -> Component.literal("Spawned Warhammer powered villager " + id
                    + " beside " + player.getGameProfile().getName()), true);
            return 1;
        } catch (ReflectiveOperationException | RuntimeException e) {
            if (registered && powerData != null && removePower != null && villager != null) {
                try {
                    removePower.invoke(powerData, villager.getUUID());
                } catch (ReflectiveOperationException cleanup) {
                    DrewCraft.LOGGER.error("Could not clear failed Warhammer test power", cleanup);
                }
            }
            if (villager != null) villager.discard();
            DrewCraft.LOGGER.error("Could not spawn powered test villager", e);
            source.sendFailure(Component.literal("Could not spawn a powered villager; see server log."));
            return 0;
        }
    }
}
