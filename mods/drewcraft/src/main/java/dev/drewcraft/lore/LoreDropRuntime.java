package dev.drewcraft.lore;

import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.encounter.StrategicEntityTags;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.source.SourceRecord;
import java.util.List;
import java.util.Optional;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * Field-book drops for Covenant strategic kills. Runs only after an
 * idempotent casualty is confirmed, so duplicate death callbacks can never
 * duplicate books. Coordinates come from the killer's home source core, so
 * every fragment names a real place.
 */
public final class LoreDropRuntime {
    private LoreDropRuntime() {
    }

    public static void maybeDrop(ServerLevel level, net.minecraft.world.entity.Entity entity,
                                 StrategicEntityTags.TaggedEntity tag) {
        DrewCraftSavedData data = DrewCraftSavedData.get(level.getServer());
        Optional<StrategicGroup> group = data.strategicGroup(tag.groupId());
        if (group.isEmpty() || !LoreDropPolicy.COVENANT_FACTION.equals(group.get().factionId())) {
            return;
        }
        if (!LoreDropPolicy.rollDrop(tag.entityTypeId(), level.random)) {
            return;
        }
        String homeSite = siteKeyFor(data, group.get());
        String mode = LoreDropPolicy.rollMode(level.random);
        // Site display falls back to the site key until the authored site
        // registry (pack/content/sites/sites.json) is imported at runtime.
        String display = homeSite == null ? "an unknown Covenant site" : homeSite;
        int x = (int) Math.floor(entity.getX());
        int y = (int) Math.floor(entity.getY());
        int z = (int) Math.floor(entity.getZ());
        if (homeSite != null) {
            Optional<SourceRecord> source = group.get().sourceId().flatMap(data::sourceRecord);
            if (source.isPresent()) {
                x = source.get().corePosition().x();
                y = source.get().corePosition().y();
                z = source.get().corePosition().z();
            }
        }
        ItemStack book = CovenantBooks.fieldBook(display, x, y, z, mode);
        Vec3 pos = entity.position();
        ItemEntity drop = new ItemEntity(level, pos.x, pos.y + 0.5, pos.z, book);
        drop.setDefaultPickUpDelay();
        level.addFreshEntity(drop);
    }

    static String siteKeyFor(DrewCraftSavedData data, StrategicGroup group) {
        return group.sourceId()
                .flatMap(data::sourceRecord)
                .map(source -> source.structureId())
                .orElse(null);
    }

    /** Guarantee path used by Source Core clearing (item 8). */
    public static List<String> archivePages(String siteKey, String archiveTitle, int x, int y, int z) {
        return List.of("SEALED ARCHIVE\n" + archiveTitle + "\nX: " + x + " Y: " + y + " Z: " + z
                + "\nSite key: " + siteKey);
    }
}
