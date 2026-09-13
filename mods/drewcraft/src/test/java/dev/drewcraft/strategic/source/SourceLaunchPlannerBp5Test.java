package dev.drewcraft.strategic.source;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicTargetKnowledge;
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
        SourceLaunchPlanner.PlanResult result = SourceLaunchPlanner.plan(source, source.nextActionGameTime());
        assertTrue(result.success(), result.status());

        StrategicGroup group = result.group();
        assertEquals(StrategicGroupType.ARMY, group.groupType());
        assertEquals(256, group.totalStrength());
        assertEquals(StrategicTargetKnowledge.SCOUTED_REGION, group.mission().targetKnowledge());
        assertTrue(group.mission().knowledgeDetail().contains("no player position queried"));
        assertEquals(group.destination(), group.mission().target());
        assertNotEquals(group.position(), group.destination());
    }
}
