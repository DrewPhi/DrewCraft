package dev.drewcraft.net;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class DrewCraftProtocolTest {
    @Test
    void parsesCanonicalVersion() {
        assertEquals(new DrewCraftProtocol.Version(1, 7), DrewCraftProtocol.Version.parse("1.7"));
    }

    @Test
    void acceptsSameMajorVersion() {
        assertTrue(DrewCraftProtocol.isCompatible("1.0"));
        assertTrue(DrewCraftProtocol.isCompatible("1.99"));
    }

    @Test
    void rejectsDifferentMajorVersion() {
        assertFalse(DrewCraftProtocol.isCompatible("2.0"));
        assertFalse(DrewCraftProtocol.isCompatible("0.99"));
    }

    @Test
    void rejectsMalformedVersions() {
        assertFalse(DrewCraftProtocol.isCompatible("1"));
        assertFalse(DrewCraftProtocol.isCompatible("1.x"));
        assertFalse(DrewCraftProtocol.isCompatible(null));
        assertThrows(IllegalArgumentException.class, () -> DrewCraftProtocol.Version.parse("1.2.3"));
    }
}
