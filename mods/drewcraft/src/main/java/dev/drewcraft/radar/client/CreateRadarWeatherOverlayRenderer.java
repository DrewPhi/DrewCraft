package dev.drewcraft.radar.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.drewcraft.adapter.create.CreateRadarWeatherBridge;
import dev.drewcraft.radar.WeatherRadarProduct;
import java.util.Locale;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.core.Direction;
import org.joml.Matrix4f;

/** Client-only renderer layered underneath Create: Radars' native contact sprites. */
public final class CreateRadarWeatherOverlayRenderer {
    private static final float TRACK_POSITION_SCALE = 0.75f;
    private static final float WORLD_DEPTH = 0.9485f;

    private CreateRadarWeatherOverlayRenderer() {
    }

    public static void renderWorld(Object monitor, PoseStack poseStack, MultiBufferSource bufferSource) {
        WeatherRadarProduct product = CreateRadarWeatherBridge.clientProduct(monitor);
        if (product == null || !product.available() || product.gridSize() < 2) return;

        int monitorSize = CreateRadarWeatherBridge.monitorSize(monitor);
        Direction facing = CreateRadarWeatherBridge.monitorFacing(monitor);
        VertexConsumer buffer = bufferSource.getBuffer(RenderType.lines());
        Matrix4f matrix = poseStack.last().pose();
        float halfCell = Math.max(0.008f, monitorSize * TRACK_POSITION_SCALE / (product.gridSize() - 1) * 0.22f);

        for (int z = 0; z < product.gridSize(); z++) {
            for (int x = 0; x < product.gridSize(); x++) {
                int intensity = product.intensityUnsigned(x, z);
                byte visibility = product.visibilityAt(x, z);
                if (intensity <= 5 || visibility == WeatherRadarProduct.VIS_OUTSIDE
                        || visibility == WeatherRadarProduct.VIS_BLOCKED
                        || visibility == WeatherRadarProduct.VIS_UNAVAILABLE) {
                    continue;
                }

                double dx = normalized(x, product.gridSize()) * product.rangeBlocks();
                double dz = normalized(z, product.gridSize()) * product.rangeBlocks();
                float xOff = offset(dx, dz, facing, product.rangeBlocks(), true) * TRACK_POSITION_SCALE;
                float zOff = offset(dx, dz, facing, product.rangeBlocks(), false) * TRACK_POSITION_SCALE;
                float cx = 1.0f - monitorSize / 2.0f + xOff * monitorSize;
                float cz = 1.0f - monitorSize / 2.0f + zOff * monitorSize;
                int rgb = rgbForIntensity(intensity);
                float alpha = visibility == WeatherRadarProduct.VIS_UNKNOWN ? 0.40f : 0.72f;
                lineSquare(buffer, matrix, cx, cz, halfCell, rgb, alpha);
            }
        }
    }

    public static void renderScreen(GuiGraphics graphics, Object monitor, int left, int top, int uiSize) {
        WeatherRadarProduct product = CreateRadarWeatherBridge.clientProduct(monitor);
        if (product == null) return;

        if (product.available() && product.gridSize() >= 2) {
            Direction facing = CreateRadarWeatherBridge.monitorFacing(monitor);
            int radius = Math.max(2, uiSize / Math.max(24, product.gridSize() * 5));
            for (int z = 0; z < product.gridSize(); z++) {
                for (int x = 0; x < product.gridSize(); x++) {
                    int intensity = product.intensityUnsigned(x, z);
                    byte visibility = product.visibilityAt(x, z);
                    if (intensity <= 5 || visibility == WeatherRadarProduct.VIS_OUTSIDE
                            || visibility == WeatherRadarProduct.VIS_BLOCKED
                            || visibility == WeatherRadarProduct.VIS_UNAVAILABLE) {
                        continue;
                    }
                    double dx = normalized(x, product.gridSize()) * product.rangeBlocks();
                    double dz = normalized(z, product.gridSize()) * product.rangeBlocks();
                    float xOff = offset(dx, dz, facing, product.rangeBlocks(), true) * TRACK_POSITION_SCALE;
                    float zOff = offset(dx, dz, facing, product.rangeBlocks(), false) * TRACK_POSITION_SCALE;
                    int px = (int) (left + (0.5f + xOff) * uiSize);
                    int py = (int) (top + (0.5f + zOff) * uiSize);
                    int alpha = visibility == WeatherRadarProduct.VIS_UNKNOWN ? 92 : 150;
                    int argb = (alpha << 24) | rgbForIntensity(intensity);
                    graphics.fill(px - radius, py - radius, px + radius + 1, py + radius + 1, argb);
                }
            }
        }

        String readout = readout(product);
        graphics.drawString(Minecraft.getInstance().font, readout, left + 8, top + 8, 0xE6FFFFFF, false);
    }

    static String readout(WeatherRadarProduct product) {
        if (!product.available()) return "WX OFFLINE";
        StringBuilder out = new StringBuilder("WX");
        if (product.windSpeedMps().isPresent() && product.windAngleRad().isPresent()) {
            double degrees = (Math.toDegrees(product.windAngleRad().getAsDouble()) + 360.0) % 360.0;
            double knots = product.windSpeedMps().getAsDouble() * 1.9438444924;
            out.append(String.format(Locale.ROOT, "  WIND %03.0f° %.1f kt", degrees, knots));
        }
        if (product.temperatureC().isPresent()) {
            out.append(String.format(Locale.ROOT, "  TEMP %.1f C", product.temperatureC().getAsDouble()));
        }
        return out.toString();
    }

    private static void lineSquare(VertexConsumer buffer, Matrix4f matrix, float cx, float cz, float half, int rgb, float alpha) {
        float r = ((rgb >> 16) & 0xFF) / 255.0f;
        float g = ((rgb >> 8) & 0xFF) / 255.0f;
        float b = (rgb & 0xFF) / 255.0f;
        vertex(buffer, matrix, cx - half, cz - half, r, g, b, alpha);
        vertex(buffer, matrix, cx + half, cz - half, r, g, b, alpha);
        vertex(buffer, matrix, cx + half, cz - half, r, g, b, alpha);
        vertex(buffer, matrix, cx + half, cz + half, r, g, b, alpha);
        vertex(buffer, matrix, cx + half, cz + half, r, g, b, alpha);
        vertex(buffer, matrix, cx - half, cz + half, r, g, b, alpha);
        vertex(buffer, matrix, cx - half, cz + half, r, g, b, alpha);
        vertex(buffer, matrix, cx - half, cz - half, r, g, b, alpha);
    }

    private static void vertex(VertexConsumer buffer, Matrix4f matrix, float x, float z, float r, float g, float b, float alpha) {
        buffer.addVertex(matrix, x, WORLD_DEPTH, z).setColor(r, g, b, alpha).setNormal(0, 1, 0);
    }

    private static int rgbForIntensity(int intensity) {
        if (intensity < 64) return 0x36D16F;
        if (intensity < 128) return 0xE6D94C;
        if (intensity < 192) return 0xF39C35;
        return 0xEF4444;
    }

    private static double normalized(int index, int gridSize) {
        return ((double) index / (gridSize - 1)) * 2.0 - 1.0;
    }

    private static float offset(double dx, double dz, Direction facing, double range, boolean xOffset) {
        if (!(range > 0.0)) return 0.0f;
        double coordinate;
        if (xOffset) {
            coordinate = facing.getAxis() == Direction.Axis.Z ? dx : dz;
            if (facing == Direction.NORTH || facing == Direction.EAST) coordinate = -coordinate;
        } else {
            coordinate = facing.getAxis() == Direction.Axis.Z ? dz : dx;
            if (facing == Direction.NORTH || facing == Direction.WEST) coordinate = -coordinate;
        }
        return (float) (coordinate / range / 2.0);
    }
}
