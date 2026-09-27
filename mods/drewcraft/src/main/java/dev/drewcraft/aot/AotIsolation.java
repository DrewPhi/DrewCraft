package dev.drewcraft.aot;

import net.minecraft.world.level.Level;

/** The owner-approved fixed policy; never derived from a client packet. */
public final class AotIsolation {
    public static volatile boolean automaticDocksSuppressed;

    private AotIsolation() {}

    public static boolean isParadis(String dimension) {
        return "dannys-aot:paradis".equals(dimension);
    }

    public static boolean isParadis(Level level) {
        return isParadis(level.dimension().location().toString());
    }
}
