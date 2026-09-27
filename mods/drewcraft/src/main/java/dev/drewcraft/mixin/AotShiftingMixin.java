package dev.drewcraft.mixin;

import dev.drewcraft.aot.AotIsolation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "daot.network.ModNetworking", remap = false)
public abstract class AotShiftingMixin {
    @Inject(method = {"handleTitanShift", "handleTeaseShift",
            "initiatePureTitanShift(Lnet/minecraft/server/level/ServerPlayer;Lnet/minecraft/server/level/ServerLevel;)V"},
            at = @At("HEAD"), cancellable = true, require = 3)
    private static void drewcraft$denyShift(ServerPlayer player, ServerLevel level, CallbackInfo ci) {
        if (!AotIsolation.isParadis(player.level()) || !AotIsolation.isParadis(level)) ci.cancel();
    }

    @Inject(method = "initiatePureTitanShift(Lnet/minecraft/server/level/ServerPlayer;Lnet/minecraft/server/level/ServerLevel;Ljava/lang/String;)V",
            at = @At("HEAD"), cancellable = true, require = 1)
    private static void drewcraft$denyOwnedShift(ServerPlayer player, ServerLevel level, String owner, CallbackInfo ci) {
        if (!AotIsolation.isParadis(player.level()) || !AotIsolation.isParadis(level)) ci.cancel();
    }

    @Inject(method = "forceShiftPlayer", at = @At("HEAD"), cancellable = true, require = 1)
    private static void drewcraft$denyForcedShift(ServerPlayer player, CallbackInfo ci) {
        if (player == null || !AotIsolation.isParadis(player.level())) ci.cancel();
    }

    @Inject(method = {"firePreshiftAndQueueSpawn", "firePreshiftOnly"},
            at = @At("HEAD"), cancellable = true, require = 2)
    private static void drewcraft$denyDelayedBite(ServerPlayer player, @Coerce Object type, CallbackInfo ci) {
        if (!AotIsolation.isParadis(player.level())) ci.cancel();
    }

    @Inject(method = {"spawnColossalTitan", "spawnFoundingTitan", "spawnAttackTitan", "spawnTripleTTitan",
            "spawnTestShifterTitan", "spawnCartShifterTitan", "spawnOgreShifterTitan", "spawnArmoredTitan",
            "spawnFemaleTitan", "spawnBeastTitan", "spawnWarhammerTitan", "spawnPureTitan"},
            at = @At("HEAD"), cancellable = true, require = 12)
    private static void drewcraft$denyDelayedSpawn(ServerPlayer player, ServerLevel level,
            double x, double y, double z, float yaw, CallbackInfo ci) {
        if (!AotIsolation.isParadis(player.level()) || !AotIsolation.isParadis(level)) ci.cancel();
    }

    @Inject(method = "triggerTransformationExplosion", at = @At("HEAD"), cancellable = true, require = 1)
    private static void drewcraft$denyExplosion(ServerLevel level, double x, double y, double z,
            ServerPlayer player, double radius, float damage, double knockback, CallbackInfo ci) {
        if (!AotIsolation.isParadis(level)) ci.cancel();
    }
}
