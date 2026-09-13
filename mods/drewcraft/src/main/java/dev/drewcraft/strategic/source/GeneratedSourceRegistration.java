package dev.drewcraft.strategic.source;

import dev.drewcraft.content.DrewCraftBlocks;
import dev.drewcraft.persistence.DrewCraftSavedData;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;

/**
 * Narrow hook for structure/template/post-generation integration. The caller supplies the exact
 * generated structure identity and deterministic core anchor; this method never searches chunks.
 */
public final class GeneratedSourceRegistration {
    private GeneratedSourceRegistration() {
    }

    public static RegistrationResult register(ServerLevel level, SourceDescriptor descriptor) {
        String dimension = level.dimension().location().toString();
        if (!dimension.equals(descriptor.dimension())) {
            throw new IllegalArgumentException("generated source descriptor dimension does not match level");
        }

        DrewCraftSavedData.DiscoverSourceResult discovery = DrewCraftSavedData.get(level.getServer())
                .discoverSource(descriptor, level.getGameTime());
        SourceRecord source = discovery.source();
        if (source.state() == SourceState.CLEARED) {
            return new RegistrationResult(source, discovery.created(), false, "already_cleared");
        }

        BlockPos corePos = new BlockPos(
                descriptor.corePosition().x(), descriptor.corePosition().y(), descriptor.corePosition().z()
        );
        if (!level.hasChunkAt(corePos)) {
            return new RegistrationResult(source, discovery.created(), false, "core_chunk_not_loaded");
        }

        boolean placed = level.setBlock(corePos, DrewCraftBlocks.SOURCE_CORE.get().defaultBlockState(), 3);
        return new RegistrationResult(source, discovery.created(), placed, placed ? "core_bound" : "core_place_failed");
    }

    public record RegistrationResult(SourceRecord source, boolean sourceCreated, boolean corePlaced, String status) {
    }
}
