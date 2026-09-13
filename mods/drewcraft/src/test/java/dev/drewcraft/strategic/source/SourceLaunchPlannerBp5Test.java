package dev.drewcraft.strategic.source;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.faction.StrategicFactionCatalog;
import dev.drewcraft.strategic.faction.StrategicForceTemplate;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicTargetKnowledge;
import dev.drewcraft.strategic.objective.StrategicObjectiveCatalog;
import org.junit.jupiter.api.Test;

class SourceLaunchPlannerBp5Test {
    @Test
    void strongholdArmyUsesScoutedObjectiveWithoutPlayerLookup() {
        SourceDescriptor descriptor = new SourceDescriptor(
                "minecraft:overworld", "drewcraft:undead_stronghold", 100, 64, 200,
                new SourceCorePosition("minecraft:overworld", 101, 65, 201),
                SourceClass.STRONGHOLD, "drewcraft:undead"
        );
        SourceRecord source = SourceRecord.discovered(descriptor, 0L);
        StrategicForceTemplate army = StrategicFactionCatalog.defaultCatalog()
                .byRole("drewcraft:undead", SourceClass.STRONGHOLD, StrategicGroupType.ARMY)
                .orElseThrow();

        StrategicObjectiveCatalog.replace(java.util.List.of(new StrategicObjectiveCatalog.StrategicObjective(
                "spawn-settlement", "settlement", new StrategicPosition("minecraft:overworld", 500, 600)
        )));
        SourceLaunchPlanner.TargetSelection target;
        try {
            target = SourceLaunchPlanner.chooseTarget(null, source, army);
        } finally {
            StrategicObjectiveCatalog.clear();
        }
        StrategicPosition sourcePosition = new StrategicPosition(source.dimension(), source.anchorX() + 0.5, source.anchorZ() + 0.5);

        assertEquals(256, army.desiredStrength(source.launchStrength()));
        assertEquals(StrategicTargetKnowledge.SCOUTED_REGION, target.knowledge());
        assertTrue(target.detail().contains("spawn-settlement"));
        assertEquals(source.dimension(), target.position().dimension());
        assertNotEquals(sourcePosition, target.position());
    }
}
