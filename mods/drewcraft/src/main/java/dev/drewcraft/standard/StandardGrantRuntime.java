package dev.drewcraft.standard;

import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

/**
 * Grants every player exactly one Flightstone Standard on first login.
 *
 * <p>Idempotency lives in the player's own persistent data
 * ({@code drewcraft_standard_granted}), so relogs, deaths, restarts, and
 * restores can never duplicate it. Dropping, losing, or copying the banner
 * is ordinary Minecraft behavior; strategic identity (which Standard belongs
 * to which player) is resolved by possession + UUID at the encounter layer,
 * never by this grant.
 */
public final class StandardGrantRuntime {
    public static final String GRANT_FLAG = "drewcraft_standard_granted";

    private StandardGrantRuntime() {
    }

    /** Pure gate, unit-tested without booting Minecraft. */
    public static boolean shouldGrant(CompoundTag persistentData) {
        return persistentData == null || !persistentData.getBoolean(GRANT_FLAG);
    }

    /** Pure marker, unit-tested without booting Minecraft. */
    public static void markGranted(CompoundTag persistentData) {
        persistentData.putBoolean(GRANT_FLAG, true);
    }

    public static void onPlayerLoggedIn(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        CompoundTag data = player.getPersistentData();
        if (!shouldGrant(data)) {
            return;
        }
        if (!(player.level() instanceof ServerLevel level)) {
            return;
        }
        ItemStack standard = FlightstoneStandardDesign.create(
                level.registryAccess().lookupOrThrow(Registries.BANNER_PATTERN));
        markGranted(data);
        if (!player.getInventory().add(standard)) {
            player.drop(standard, false);
        }
    }
}
