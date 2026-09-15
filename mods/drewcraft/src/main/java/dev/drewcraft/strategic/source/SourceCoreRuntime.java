package dev.drewcraft.strategic.source;

import dev.drewcraft.lore.CovenantBooks;
import dev.drewcraft.persistence.DrewCraftSavedData;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

public final class SourceCoreRuntime {
    private SourceCoreRuntime() {
    }

    public static ClearResult clearAt(ServerLevel level, BlockPos pos, String cause, String actor) {
        DrewCraftSavedData data = DrewCraftSavedData.get(level.getServer());
        SourceCorePosition core = new SourceCorePosition(
                level.dimension().location().toString(), pos.getX(), pos.getY(), pos.getZ()
        );
        Optional<SourceRecord> source = data.sourceAtCore(core);
        if (source.isEmpty()) return new ClearResult(false, false, null);
        boolean changed = data.clearSource(source.get().sourceId(), level.getGameTime(), cause, actor);
        if (changed) {
            // Core destruction is a rare, irreversible progression event. Persist it immediately
            // rather than waiting for the next autosave so a crash cannot resurrect the source.
            level.getServer().overworld().getDataStorage().save();
            // Guaranteed campaign clue: the site's sealed archive always drops
            // where its Core fell, so progression can never deadlock on RNG.
            SourceRecord cleared = source.get();
            String siteKey = cleared.structureId();
            String archiveTitle = "Seal of " + siteKey;
            if (data.applyCovenantClear(siteKey, archiveTitle)) {
                ItemStack archive = CovenantBooks.sealedArchive(siteKey, archiveTitle,
                        pos.getX(), pos.getY(), pos.getZ());
                Vec3 at = new Vec3(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5);
                ItemEntity drop = new ItemEntity(level, at.x, at.y, at.z, archive);
                drop.setDefaultPickUpDelay();
                level.addFreshEntity(drop);
            }
        }
        return new ClearResult(true, changed, source.get().sourceId());
    }

    public record ClearResult(boolean bound, boolean newlyCleared, java.util.UUID sourceId) {
    }
}
