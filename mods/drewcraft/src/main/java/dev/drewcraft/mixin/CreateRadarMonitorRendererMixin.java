package dev.drewcraft.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.drewcraft.radar.client.CreateRadarWeatherOverlayRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Inserts weather immediately below Create: Radars' sweep/contact rendering on physical monitors. */
@Pseudo
@Mixin(targets = "com.happysg.radar.block.monitor.MonitorRenderer", remap = false)
public abstract class CreateRadarMonitorRendererMixin {
    @Inject(
            method = "renderRadarDisplay",
            at = @At(
                    value = "INVOKE",
                    target = "Lcom/happysg/radar/block/monitor/MonitorRenderer;renderSweep(Lcom/happysg/radar/block/radar/behavior/IRadar;Lcom/happysg/radar/block/monitor/MonitorBlockEntity;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;F)V",
                    shift = At.Shift.BEFORE
            ),
            remap = false,
            require = 0
    )
    private void drewcraft$renderWeather(
            @Coerce Object radar,
            @Coerce Object monitor,
            PoseStack poseStack,
            MultiBufferSource bufferSource,
            float partialTicks,
            CallbackInfo ci
    ) {
        CreateRadarWeatherOverlayRenderer.renderWorld(monitor, poseStack, bufferSource);
    }
}
