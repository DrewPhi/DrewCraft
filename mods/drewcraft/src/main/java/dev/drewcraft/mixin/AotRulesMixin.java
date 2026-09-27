package dev.drewcraft.mixin;

import dev.drewcraft.aot.AotIsolation;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets = "daot.DannysAot", remap = false)
public abstract class AotRulesMixin {
    @Inject(method = {"isShiftingAllowed", "isSelfInjectAllowed", "canInjectOtherPlayers",
            "doVillagersSpawnWithPowers"}, at = @At("HEAD"), cancellable = true, require = 4)
    private static void drewcraft$restrictTitanRules(Level level, CallbackInfoReturnable<Boolean> cir) {
        if (!AotIsolation.isParadis(level)) cir.setReturnValue(false);
    }
}
