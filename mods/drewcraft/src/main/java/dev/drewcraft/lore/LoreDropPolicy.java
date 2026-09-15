package dev.drewcraft.lore;

import java.util.List;
import java.util.Map;

/**
 * Pure lore-drop mechanics mirroring {@code pack/content/lore/config.json}.
 * Rates and the coordinate-mode distribution are frozen pre-playtest data;
 * balance tuning belongs to V1.1+.
 */
public final class LoreDropPolicy {
    public static final String COVENANT_FACTION = "drewcraft:covenant";

    private static final Map<String, Double> KILL_RATES = Map.ofEntries(
            Map.entry("illagerinvasion:basher", 0.0125),
            Map.entry("illagerinvasion:marauder", 0.0125),
            Map.entry("illagerinvasion:provoker", 0.0125),
            Map.entry("illagerinvasion:archivist", 0.04),
            Map.entry("illagerinvasion:sorcerer", 0.06),
            Map.entry("illagerinvasion:firecaller", 0.06),
            Map.entry("illagerinvasion:necromancer", 0.06),
            Map.entry("illagerinvasion:alchemist", 0.06),
            Map.entry("minecraft:illusioner", 0.06),
            Map.entry("illagerinvasion:inquisitor", 0.08),
            Map.entry("illagerinvasion:invoker", 0.12)
    );

    /** Cumulative mode thresholds matching the frozen distribution. */
    private static final List<Map.Entry<String, Double>> MODES = List.of(
            Map.entry("x_only", 0.38),
            Map.entry("z_only", 0.76),
            Map.entry("x_y", 0.85),
            Map.entry("z_y", 0.94),
            Map.entry("x_z", 0.985),
            Map.entry("x_y_z_full", 1.0)
    );

    private LoreDropPolicy() {
    }

    public static double killRate(String entityTypeId) {
        return KILL_RATES.getOrDefault(entityTypeId, 0.0);
    }

    public static boolean rollDrop(String entityTypeId, net.minecraft.util.RandomSource rng) {
        return rng.nextDouble() < killRate(entityTypeId);
    }

    public static String rollMode(net.minecraft.util.RandomSource rng) {
        double roll = rng.nextDouble();
        for (Map.Entry<String, Double> mode : MODES) {
            if (roll < mode.getValue()) {
                return mode.getKey();
            }
        }
        return "x_y_z_full";
    }

    /**
     * Field-book targeting: 75% home site, else a random uncleared site.
     * Cleared sites are the caller's responsibility to filter (residue rule).
     */
    public static String chooseSite(net.minecraft.util.RandomSource rng, String homeSiteId,
                                    List<String> unclearedSiteIds) {
        if (homeSiteId != null && rng.nextDouble() < 0.75) {
            return homeSiteId;
        }
        if (unclearedSiteIds != null && !unclearedSiteIds.isEmpty()) {
            return unclearedSiteIds.get(rng.nextInt(unclearedSiteIds.size()));
        }
        if (homeSiteId != null) {
            return homeSiteId;
        }
        throw new IllegalArgumentException("no site to target");
    }
}
