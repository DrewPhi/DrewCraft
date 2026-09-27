package dev.drewcraft.mixin;

import dev.drewcraft.DrewCraft;
import dev.drewcraft.aot.AotIsolation;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Keep DH from running an unsupported generator for Paradis/Paths. */
@Pseudo
@Mixin(targets = "com.seibel.distanthorizons.core.level.AbstractDhServerLevel", remap = false)
public abstract class AotDistantGenerationMixin {
    @Unique private Boolean drewcraft$aotDimension;

    @Inject(method = "shouldDoWorldGen()Z", at = @At("HEAD"), cancellable = true, require = 1)
    private void drewcraft$visitedChunksOnly(CallbackInfoReturnable<Boolean> cir) {
        if (!AotIsolation.automaticDocksSuppressed) return;
        if (drewcraft$aotDimension == null) {
            try {
                Object wrapper = getClass().getMethod("getServerLevelWrapper").invoke(this);
                Class<?> wrapperApi = Class.forName(
                        "com.seibel.distanthorizons.core.wrapperInterfaces.world.IServerLevelWrapper");
                String dimension = (String) wrapperApi.getMethod("getKeyedLevelDimensionName").invoke(wrapper);
                drewcraft$aotDimension = dimension.startsWith("dannys-aot:");
                if (drewcraft$aotDimension) {
                    DrewCraft.LOGGER.info("AOT DH policy: distant generation disabled for {}; normal loaded-chunk LOD updates remain enabled", dimension);
                }
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException("Cannot enforce AOT Distant Horizons generation restriction", e);
            }
        }
        if (drewcraft$aotDimension) cir.setReturnValue(false);
    }
}
