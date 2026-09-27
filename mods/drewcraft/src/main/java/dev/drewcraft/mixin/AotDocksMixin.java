package dev.drewcraft.mixin;

import dev.drewcraft.aot.AotIsolation;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "daot.world.OverworldDocksGenerator", remap = false)
public abstract class AotDocksMixin {
    @Inject(method = "register()V", at = @At("HEAD"), cancellable = true, require = 1)
    private static void drewcraft$manualDockOnly(CallbackInfo ci) {
        AotIsolation.automaticDocksSuppressed = true;
        ci.cancel();
    }
}
