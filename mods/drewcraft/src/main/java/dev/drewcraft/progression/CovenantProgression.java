package dev.drewcraft.progression;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Covenant campaign progression: Source Core clears -> archived clues ->
 * Flightstone markers -> capital reveal.
 *
 * <p>Pure state with idempotent transitions so restart/race/duplicates are
 * safe: clearing an already-cleared site returns {@code false} and changes
 * nothing. Already-deployed strategic forces are untouched here by design;
 * that rule lives in the strategic source authority.
 */
public final class CovenantProgression {
    public static final int REQUIRED_SITES = 8;

    private final Set<String> clearedSites = new LinkedHashSet<>();
    private final Map<String, String> archivedClues = new LinkedHashMap<>();

    /** @return true when this call newly cleared the site. */
    public synchronized boolean applyClear(String siteId, String archiveText) {
        if (siteId == null || siteId.isEmpty()) {
            throw new IllegalArgumentException("siteId required");
        }
        if (clearedSites.contains(siteId)) {
            return false;
        }
        clearedSites.add(siteId);
        if (archiveText != null) {
            archivedClues.put(siteId, archiveText);
        }
        return true;
    }

    public synchronized boolean isCleared(String siteId) {
        return clearedSites.contains(siteId);
    }

    public synchronized int clearedCount() {
        return clearedSites.size();
    }

    /** Flightstone markers mirror cleared required sites. */
    public synchronized int flightstoneMarkers() {
        return clearedSites.size();
    }

    public synchronized boolean isCapitalRevealed() {
        return clearedSites.size() >= REQUIRED_SITES;
    }

    public synchronized List<String> clearedSites() {
        return new ArrayList<>(clearedSites);
    }

    public synchronized Map<String, String> archivedClues() {
        return new LinkedHashMap<>(archivedClues);
    }

    public synchronized Map<String, Object> toMap() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("schemaVersion", 1);
        out.put("clearedSites", new ArrayList<>(clearedSites));
        out.put("archivedClues", new LinkedHashMap<>(archivedClues));
        return out;
    }

    @SuppressWarnings("unchecked")
    public synchronized void loadMap(Map<String, Object> data) {
        clearedSites.clear();
        archivedClues.clear();
        Object sites = data.get("clearedSites");
        if (sites instanceof List<?> list) {
            for (Object s : list) {
                clearedSites.add(String.valueOf(s));
            }
        }
        Object clues = data.get("archivedClues");
        if (clues instanceof Map<?, ?> map) {
            for (Map.Entry<?, ?> e : map.entrySet()) {
                archivedClues.put(String.valueOf(e.getKey()), String.valueOf(e.getValue()));
            }
        }
    }
}
