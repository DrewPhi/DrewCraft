package dev.drewcraft.lore;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/**
 * Renders DIVIDED WAYMARK book pages. Missing axes show as
 * {@code [withheld]} so fragment matching is obvious. Mirrors
 * {@code tools/covenant_lore.py} and the lore config template.
 */
public final class WaymarkRenderer {
    private static final Set<String> MODES = Set.of(
            "x_only", "z_only", "x_y", "z_y", "x_z", "x_y_z_full");

    private WaymarkRenderer() {
    }

    public static List<String> render(String targetDisplay, int x, int y, int z, String mode) {
        if (!MODES.contains(mode)) {
            throw new IllegalArgumentException("unknown coordinate mode: " + mode);
        }
        Set<String> shown = switch (mode) {
            case "x_only" -> Set.of("x");
            case "z_only" -> Set.of("z");
            case "x_y" -> Set.of("x", "y");
            case "z_y" -> Set.of("z", "y");
            case "x_z" -> Set.of("x", "z");
            default -> Set.of("x", "y", "z");
        };
        List<String> pages = new ArrayList<>();
        pages.add("DIVIDED WAYMARK\n" + targetDisplay + "\n\n"
                + "X: " + axis("x", x, shown) + "\n"
                + "Y: " + axis("y", y, shown) + "\n"
                + "Z: " + axis("z", z, shown) + "\n\n"
                + "Compare copies bearing the same destination seal.");
        return pages;
    }

    private static String axis(String name, int value, Set<String> shown) {
        return shown.contains(name) ? String.valueOf(value) : "[withheld]";
    }
}
