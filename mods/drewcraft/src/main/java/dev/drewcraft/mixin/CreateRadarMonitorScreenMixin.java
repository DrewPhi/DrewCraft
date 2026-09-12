package dev.drewcraft.mixin;

import dev.drewcraft.radar.client.CreateRadarWeatherOverlayRenderer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Adds the same cached weather product and station readout to Create: Radars' full-screen monitor UI. */
@Pseudo
@Mixin(targets = "com.happysg.radar.block.monitor.MonitorScreen", remap = false)
public abstract class CreateRadarMonitorScreenMixin {
    @Shadow @Final private BlockPos controllerPos;
    @Shadow private int left;
    @Shadow private int top;
    @Shadow private int uiSize;

    @Inject(
            method = "render",
            at = @At(
                    value = "INVOKE",
                    target = "Lcom/happysg/radar/block/monitor/MonitorScreen;renderSweep(Lnet/minecraft/client/gui/GuiGraphics;Lcom/happysg/radar/block/monitor/MonitorBlockEntity;Lcom/happysg/radar/block/radar/behavior/IRadar;F)V",
                    shift = At.Shift.BEFORE
            ),
            remap = false,
            require = 0
    )
    private void drewcraft$renderWeather(GuiGraphics graphics, int mouseX, int mouseY, float partialTicks, CallbackInfo ci) {
        if (Minecraft.getInstance().level == null) return;
        BlockEntity monitor = Minecraft.getInstance().level.getBlockEntity(controllerPos);
        if (monitor != null) {
            CreateRadarWeatherOverlayRenderer.renderScreen(graphics, monitor, left, top, uiSize);
        }
    }
}
