package dev.drewcraft.strategic.faction;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.source.SourceClass;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/**
 * Packaged JSON-backed V1 faction/force catalog. Gameplay logic consumes this immutable catalog;
 * adding/changing force composition does not require another scheduler implementation.
 */
public final class StrategicFactionCatalog {
    public static final String DEFAULT_RESOURCE = "/data/drewcraft/strategic/factions.json";
    public static final int CURRENT_SCHEMA_VERSION = 1;

    private static volatile StrategicFactionCatalog DEFAULT;

    private final Map<String, List<StrategicForceTemplate>> byFaction;

    private StrategicFactionCatalog(Map<String, List<StrategicForceTemplate>> byFaction) {
        this.byFaction = Map.copyOf(byFaction);
    }

    public static StrategicFactionCatalog defaultCatalog() {
        StrategicFactionCatalog local = DEFAULT;
        if (local != null) return local;
        synchronized (StrategicFactionCatalog.class) {
            if (DEFAULT == null) {
                InputStream stream = StrategicFactionCatalog.class.getResourceAsStream(DEFAULT_RESOURCE);
                if (stream == null) throw new IllegalStateException("Missing DrewCraft strategic faction data: " + DEFAULT_RESOURCE);
                try (Reader reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
                    DEFAULT = load(reader);
                } catch (IOException ex) {
                    throw new IllegalStateException("Failed closing strategic faction data", ex);
                }
            }
            return DEFAULT;
        }
    }

    public static StrategicFactionCatalog load(Reader reader) {
        Objects.requireNonNull(reader, "reader");
        JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
        int schema = root.get("schemaVersion").getAsInt();
        if (schema != CURRENT_SCHEMA_VERSION) {
            throw new IllegalStateException("Unsupported strategic faction catalog schema " + schema);
        }
        LinkedHashMap<String, List<StrategicForceTemplate>> factions = new LinkedHashMap<>();
        for (JsonElement factionElement : root.getAsJsonArray("factions")) {
            JsonObject faction = factionElement.getAsJsonObject();
            String factionId = requireNonBlank(faction.get("id").getAsString(), "faction id");
            if (factions.containsKey(factionId)) throw new IllegalStateException("Duplicate faction id: " + factionId);
            ArrayList<StrategicForceTemplate> templates = new ArrayList<>();
            for (JsonElement templateElement : faction.getAsJsonArray("templates")) {
                templates.add(parseTemplate(templateElement.getAsJsonObject()));
            }
            if (templates.isEmpty()) throw new IllegalStateException("Faction has no force templates: " + factionId);
            factions.put(factionId, List.copyOf(templates));
        }
        if (factions.isEmpty()) throw new IllegalStateException("Strategic faction catalog is empty");
        return new StrategicFactionCatalog(factions);
    }

    public List<StrategicForceTemplate> templates(String factionId) {
        return byFaction.getOrDefault(factionId, List.of());
    }

    /** Deterministic serial rotation over templates that the source can actually afford. */
    public Optional<StrategicForceTemplate> select(String factionId, SourceClass sourceClass, long launchSerial,
                                                    int populationBudget, int baseStrength) {
        List<StrategicForceTemplate> eligible = templates(factionId).stream()
                .filter(template -> template.supports(sourceClass))
                .filter(template -> template.desiredStrength(baseStrength) <= populationBudget)
                .toList();
        if (eligible.isEmpty()) return Optional.empty();
        return Optional.of(eligible.get(Math.floorMod(launchSerial, eligible.size())));
    }

    public Optional<StrategicForceTemplate> byRole(String factionId, SourceClass sourceClass,
                                                   StrategicGroupType groupType) {
        return templates(factionId).stream()
                .filter(template -> template.supports(sourceClass))
                .filter(template -> template.groupType() == groupType)
                .findFirst();
    }

    private static StrategicForceTemplate parseTemplate(JsonObject object) {
        EnumSet<SourceClass> sourceClasses = EnumSet.noneOf(SourceClass.class);
        for (JsonElement element : object.getAsJsonArray("sourceClasses")) {
            sourceClasses.add(SourceClass.valueOf(element.getAsString()));
        }
        LinkedHashMap<String, Double> weights = new LinkedHashMap<>();
        JsonObject composition = object.getAsJsonObject("composition");
        for (Map.Entry<String, JsonElement> entry : composition.entrySet()) {
            weights.put(entry.getKey(), entry.getValue().getAsDouble());
        }
        return new StrategicForceTemplate(
                object.get("id").getAsString(),
                StrategicGroupType.valueOf(object.get("groupType").getAsString()),
                sourceClasses,
                object.get("strengthMultiplier").getAsInt(),
                StrategicTargetPolicy.valueOf(object.get("targetPolicy").getAsString()),
                object.get("minDistanceBlocks").getAsDouble(),
                object.get("maxDistanceBlocks").getAsDouble(),
                weights
        );
    }

    private static String requireNonBlank(String value, String name) {
        Objects.requireNonNull(value, name);
        if (value.isBlank()) throw new IllegalArgumentException(name + " must not be blank");
        return value;
    }
}
