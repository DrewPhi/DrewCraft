package dev.drewcraft.mixin;

import dev.drewcraft.adapter.mts.MtsFuelCapacityPolicy;
import java.util.List;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Hook after MTS legacy normalization, before shared vehicle items are created. */
@Pseudo
@Mixin(targets = "minecrafttransportsimulator.packloading.PackParser", remap = false)
public abstract class MtsFuelCapacityMixin {
    @Inject(method = "parseAllDefinitions", at = @At("HEAD"), remap = false, require = 1)
    private static void drewcraft$doubleVehicleFuelCapacity(@Coerce Object definition,
            List<?> subDefinitions, String sourcePackID, CallbackInfo ci) {
        MtsFuelCapacityPolicy.applyVehicleDefinition(definition);
    }
}
