package dev.drewcraft.aot;

import dev.drewcraft.DrewCraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.EntityTravelToDimensionEvent;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;

public final class AotIsolationRuntime {
    private AotIsolationRuntime() {}

    private static boolean aotMob(Entity entity) {
        return entity instanceof LivingEntity && "dannys-aot".equals(
                BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).getNamespace());
    }

    public static void onEntityJoin(EntityJoinLevelEvent event) {
        if (!event.getLevel().isClientSide() && !AotIsolation.isParadis(event.getLevel())
                && aotMob(event.getEntity())) event.setCanceled(true);
    }

    public static void onTravel(EntityTravelToDimensionEvent event) {
        if (AotIsolation.isParadis(event.getDimension().location().toString())) return;
        Entity entity = event.getEntity();
        if (aotMob(entity) || aotMob(entity.getRootVehicle())) event.setCanceled(true);
    }

    public static void beforeServerStart(ServerAboutToStartEvent event) {
        if (!ModList.get().isLoaded("dannys_aot")) return;
        // Force transformation/validation before worlds start. Required mixin
        // failures propagate; a missing dock hook must never degrade silently.
        try {
            Class.forName("daot.network.ModNetworking");
        } catch (ClassNotFoundException e) {
            throw new IllegalStateException("AOT isolation target is missing", e);
        }
        if (!AotIsolation.automaticDocksSuppressed) {
            throw new IllegalStateException("AOT automatic dock suppression did not attach; refusing world load");
        }
        DrewCraft.LOGGER.info("AOT isolation active: automatic docks disabled; Titans restricted to Paradis");
    }
}
