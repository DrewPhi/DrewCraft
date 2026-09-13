package dev.drewcraft.strategic.source;

import java.util.UUID;
import net.minecraft.nbt.CompoundTag;

public final class SourceRecordNbt {
    private static final String TAG_SCHEMA = "SchemaVersion";

    private SourceRecordNbt() {
    }

    public static CompoundTag save(SourceRecord source) {
        CompoundTag tag = new CompoundTag();
        tag.putInt(TAG_SCHEMA, SourceRecord.CURRENT_SCHEMA_VERSION);
        tag.putUUID("SourceId", source.sourceId());
        tag.putString("Dimension", source.dimension());
        tag.putString("StructureId", source.structureId());
        tag.putInt("AnchorX", source.anchorX());
        tag.putInt("AnchorY", source.anchorY());
        tag.putInt("AnchorZ", source.anchorZ());
        tag.putInt("CoreX", source.corePosition().x());
        tag.putInt("CoreY", source.corePosition().y());
        tag.putInt("CoreZ", source.corePosition().z());
        tag.putString("SourceClass", source.sourceClass().name());
        tag.putString("FactionId", source.factionId());
        tag.putString("State", source.state().name());
        tag.putInt("PopulationBudget", source.populationBudget());
        tag.putInt("LaunchStrength", source.launchStrength());
        tag.putLong("LaunchCooldownTicks", source.launchCooldownTicks());
        tag.putDouble("MovementSpeed", source.movementSpeedBlocksPerSecond());
        tag.putLong("NextActionGameTime", source.nextActionGameTime());
        tag.putLong("LaunchSerial", source.launchSerial());
        tag.putLong("Generation", source.generation());
        source.clearedAtGameTime().ifPresent(value -> tag.putLong("ClearedAtGameTime", value));
        source.clearCause().ifPresent(value -> tag.putString("ClearCause", value));
        source.clearedBy().ifPresent(value -> tag.putString("ClearedBy", value));
        return tag;
    }

    public static SourceRecord load(CompoundTag tag) {
        int schema = tag.getInt(TAG_SCHEMA);
        if (schema > SourceRecord.CURRENT_SCHEMA_VERSION) {
            throw new IllegalStateException("SourceRecord schema " + schema + " is newer than supported schema " + SourceRecord.CURRENT_SCHEMA_VERSION);
        }
        if (schema < 1) throw new IllegalStateException("Unsupported SourceRecord schema " + schema);

        UUID sourceId = tag.getUUID("SourceId");
        String dimension = tag.getString("Dimension");
        SourceCorePosition core = new SourceCorePosition(
                dimension, tag.getInt("CoreX"), tag.getInt("CoreY"), tag.getInt("CoreZ")
        );
        Long clearedAt = tag.contains("ClearedAtGameTime") ? tag.getLong("ClearedAtGameTime") : null;
        String clearCause = tag.contains("ClearCause") ? tag.getString("ClearCause") : null;
        String clearedBy = tag.contains("ClearedBy") ? tag.getString("ClearedBy") : null;

        return new SourceRecord(
                sourceId,
                dimension,
                tag.getString("StructureId"),
                tag.getInt("AnchorX"), tag.getInt("AnchorY"), tag.getInt("AnchorZ"),
                core,
                SourceClass.valueOf(tag.getString("SourceClass")),
                tag.getString("FactionId"),
                SourceState.valueOf(tag.getString("State")),
                tag.getInt("PopulationBudget"),
                tag.getInt("LaunchStrength"),
                tag.getLong("LaunchCooldownTicks"),
                tag.getDouble("MovementSpeed"),
                tag.getLong("NextActionGameTime"),
                tag.getLong("LaunchSerial"),
                tag.getLong("Generation"),
                clearedAt, clearCause, clearedBy
        );
    }
}
