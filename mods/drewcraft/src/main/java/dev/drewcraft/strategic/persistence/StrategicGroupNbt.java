package dev.drewcraft.strategic.persistence;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.DoubleTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;

/** Deterministic codec for versioned strategic-group persistence. */
public final class StrategicGroupNbt {
    private static final String TAG_SCHEMA = "SchemaVersion";

    private StrategicGroupNbt() {
    }

    public static CompoundTag save(StrategicGroup group) {
        CompoundTag tag = new CompoundTag();
        tag.putInt(TAG_SCHEMA, StrategicGroup.CURRENT_SCHEMA_VERSION);
        tag.putUUID("GroupId", group.groupId());
        tag.putString("FactionId", group.factionId());
        tag.putString("GroupType", group.groupType().name());
        group.sourceId().ifPresent(id -> tag.putUUID("SourceId", id));
        tag.put("Position", savePosition(group.position()));
        tag.put("Route", saveRoute(group.route()));
        tag.putDouble("MovementSpeedBlocksPerSecond", group.movementSpeedBlocksPerSecond());
        tag.putInt("TotalStrength", group.totalStrength());
        tag.putString("State", group.state().name());
        tag.putLong("LastSimulatedGameTime", group.lastSimulatedGameTime());

        ListTag composition = new ListTag();
        group.composition().entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(entry -> {
            CompoundTag item = new CompoundTag();
            item.putString("Id", entry.getKey());
            item.putInt("Count", entry.getValue());
            composition.add(item);
        });
        tag.put("Composition", composition);
        return tag;
    }

    public static StrategicGroup load(CompoundTag tag) {
        int schema = tag.contains(TAG_SCHEMA, Tag.TAG_INT) ? tag.getInt(TAG_SCHEMA) : 0;
        if (schema <= 0) throw new IllegalStateException("StrategicGroup is missing a supported schema version");
        if (schema > StrategicGroup.CURRENT_SCHEMA_VERSION) {
            throw new IllegalStateException("StrategicGroup schema " + schema + " is newer than supported schema " + StrategicGroup.CURRENT_SCHEMA_VERSION);
        }

        UUID groupId = tag.getUUID("GroupId");
        UUID sourceId = tag.hasUUID("SourceId") ? tag.getUUID("SourceId") : null;
        StrategicPosition position = loadPosition(tag.getCompound("Position"));
        StrategicRoute route = loadRoute(tag.getCompound("Route"), schema);
        LinkedHashMap<String, Integer> composition = new LinkedHashMap<>();
        ListTag compositionTag = tag.getList("Composition", Tag.TAG_COMPOUND);
        for (int i = 0; i < compositionTag.size(); i++) {
            CompoundTag item = compositionTag.getCompound(i);
            composition.put(item.getString("Id"), item.getInt("Count"));
        }

        return new StrategicGroup(groupId, tag.getString("FactionId"), StrategicGroupType.valueOf(tag.getString("GroupType")),
                sourceId, position, route, tag.getDouble("MovementSpeedBlocksPerSecond"), composition,
                tag.getInt("TotalStrength"), StrategicGroupState.valueOf(tag.getString("State")),
                tag.getLong("LastSimulatedGameTime"));
    }

    private static CompoundTag savePosition(StrategicPosition position) {
        CompoundTag tag = new CompoundTag();
        tag.putString("Dimension", position.dimension());
        tag.putDouble("X", position.x());
        tag.putDouble("Z", position.z());
        return tag;
    }

    private static StrategicPosition loadPosition(CompoundTag tag) {
        return new StrategicPosition(tag.getString("Dimension"), tag.getDouble("X"), tag.getDouble("Z"));
    }

    private static CompoundTag saveRoute(StrategicRoute route) {
        CompoundTag tag = new CompoundTag();
        tag.putInt("Cursor", route.cursor());
        ListTag waypoints = new ListTag();
        for (StrategicPosition waypoint : route.waypoints()) waypoints.add(savePosition(waypoint));
        tag.put("Waypoints", waypoints);
        ListTag multipliers = new ListTag();
        for (double multiplier : route.segmentCostMultipliers()) multipliers.add(DoubleTag.valueOf(multiplier));
        tag.put("SegmentCostMultipliers", multipliers);
        return tag;
    }

    private static StrategicRoute loadRoute(CompoundTag tag, int groupSchema) {
        ListTag waypointsTag = tag.getList("Waypoints", Tag.TAG_COMPOUND);
        List<StrategicPosition> waypoints = new ArrayList<>(waypointsTag.size());
        for (int i = 0; i < waypointsTag.size(); i++) waypoints.add(loadPosition(waypointsTag.getCompound(i)));
        if (groupSchema < 2 || !tag.contains("SegmentCostMultipliers", Tag.TAG_LIST)) {
            return new StrategicRoute(waypoints, tag.getInt("Cursor"));
        }
        ListTag multiplierTags = tag.getList("SegmentCostMultipliers", Tag.TAG_DOUBLE);
        List<Double> multipliers = new ArrayList<>(multiplierTags.size());
        for (int i = 0; i < multiplierTags.size(); i++) multipliers.add(multiplierTags.getDouble(i));
        return new StrategicRoute(waypoints, multipliers, tag.getInt("Cursor"));
    }
}
