package dev.drewcraft.strategic.source;

import dev.drewcraft.persistence.DrewCraftSavedData;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;

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
        }
        return new ClearResult(true, changed, source.get().sourceId());
    }

    public record ClearResult(boolean bound, boolean newlyCleared, java.util.UUID sourceId) {
    }
}
