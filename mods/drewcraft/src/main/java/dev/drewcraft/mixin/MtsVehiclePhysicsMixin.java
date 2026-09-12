package dev.drewcraft.mixin;

import dev.drewcraft.adapter.mts.MtsWeatherPhysicsBridge;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Optional, narrowly-scoped hook into MTS's aerodynamic force calculation. */
@Pseudo
@Mixin(targets = "minecrafttransportsimulator.entities.instances.EntityVehicleF_Physics", remap = false)
public abstract class MtsVehiclePhysicsMixin {
    @Unique
    private MtsWeatherPhysicsBridge.Frame drewcraft$airflowFrame;

    @Inject(method = "getForcesAndMotions", at = @At("HEAD"), remap = false, require = 0)
    private void drewcraft$enterAirRelativeFrame(CallbackInfo ci) {
        drewcraft$airflowFrame = MtsWeatherPhysicsBridge.beforeForces(this);
    }

    @Inject(method = "getForcesAndMotions", at = @At("RETURN"), remap = false, require = 0)
    private void drewcraft$restoreGroundRelativeFrame(CallbackInfo ci) {
        MtsWeatherPhysicsBridge.afterForces(this, drewcraft$airflowFrame);
        drewcraft$airflowFrame = null;
    }
}
