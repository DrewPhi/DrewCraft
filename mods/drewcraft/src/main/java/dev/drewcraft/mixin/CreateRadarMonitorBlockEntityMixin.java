package dev.drewcraft.mixin;

import dev.drewcraft.adapter.create.CreateRadarWeatherBridge;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Piggybacks the compact weather product on Create: Radars' existing monitor block-entity sync. */
@Pseudo
@Mixin(targets = "com.happysg.radar.block.monitor.MonitorBlockEntity", remap = false)
public abstract class CreateRadarMonitorBlockEntityMixin {
    @Inject(method = "write", at = @At("RETURN"), remap = false, require = 0)
    private void drewcraft$writeWeather(CompoundTag tag, HolderLookup.Provider registries, boolean clientPacket, CallbackInfo ci) {
        CreateRadarWeatherBridge.writeServerPayload(this, tag, clientPacket);
    }

    @Inject(method = "read", at = @At("RETURN"), remap = false, require = 0)
    private void drewcraft$readWeather(CompoundTag tag, HolderLookup.Provider registries, boolean clientPacket, CallbackInfo ci) {
        CreateRadarWeatherBridge.readClientPayload(this, tag, clientPacket);
    }
}
