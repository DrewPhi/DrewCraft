package dev.drewcraft.standard;

import net.minecraft.ChatFormatting;
import net.minecraft.core.HolderGetter;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.block.entity.BannerPattern;
import net.minecraft.world.level.block.entity.BannerPatternLayers;
import net.minecraft.world.level.block.entity.BannerPatterns;

/**
 * Canonical visual recipe for the Flightstone Standard.
 *
 * <p>The Standard deliberately remains a vanilla white banner with vanilla banner
 * pattern layers. That means the heraldry renders through Minecraft's normal banner
 * renderer and can be copied to a shield using the ordinary banner + shield recipe.
 * Gameplay identity must never be inferred from the heraldry alone.</p>
 */
public final class FlightstoneStandardDesign {
    public static final int DESIGN_VERSION = 1;
    public static final String STANDARD_MARKER_KEY = "drewcraft_flightstone_standard";
    public static final String DESIGN_VERSION_KEY = "drewcraft_flightstone_standard_design";

    private FlightstoneStandardDesign() {
    }

    /**
     * Creates the current canonical Flightstone Standard item.
     *
     * <p>Heraldry, in draw order:</p>
     * <ol>
     *     <li>white banner base;</li>
     *     <li>yellow border;</li>
     *     <li>yellow horizontal center stripe (wings);</li>
     *     <li>yellow vertical center stripe (propeller / ascent axis);</li>
     *     <li>white center diamond (negative-space spinner fairing);</li>
     *     <li>yellow center roundel (propeller hub).</li>
     * </ol>
     */
    public static ItemStack create(HolderGetter<BannerPattern> patternRegistry) {
        ItemStack stack = new ItemStack(Items.WHITE_BANNER);

        BannerPatternLayers layers = new BannerPatternLayers.Builder()
                .add(patternRegistry.getOrThrow(BannerPatterns.BORDER), DyeColor.YELLOW)
                .add(patternRegistry.getOrThrow(BannerPatterns.STRIPE_MIDDLE), DyeColor.YELLOW)
                .add(patternRegistry.getOrThrow(BannerPatterns.STRIPE_CENTER), DyeColor.YELLOW)
                .add(patternRegistry.getOrThrow(BannerPatterns.RHOMBUS_MIDDLE), DyeColor.WHITE)
                .add(patternRegistry.getOrThrow(BannerPatterns.CIRCLE_MIDDLE), DyeColor.YELLOW)
                .build();

        stack.set(DataComponents.BANNER_PATTERNS, layers);
        stack.set(
                DataComponents.ITEM_NAME,
                Component.translatable("item.drewcraft.flightstone_standard").withStyle(ChatFormatting.GOLD)
        );
        stack.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);

        // This marker is only a convenient item-side hint. The future StandardRecord
        // remains authoritative because vanilla banner duplication can copy item data.
        CompoundTag marker = new CompoundTag();
        marker.putBoolean(STANDARD_MARKER_KEY, true);
        marker.putInt(DESIGN_VERSION_KEY, DESIGN_VERSION);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(marker));

        return stack;
    }

    public static boolean isMarkedStandard(ItemStack stack) {
        if (!stack.is(Items.WHITE_BANNER)) return false;
        return stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY)
                .copyTag()
                .getBoolean(STANDARD_MARKER_KEY);
    }
}
