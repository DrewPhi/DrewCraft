package dev.drewcraft.adapter.create;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.service.power.PowerSample;
import java.lang.reflect.Method;
import net.minecraft.core.BlockPos;
import org.junit.jupiter.api.Test;

final class CreateKineticDecoderTest {
    @Test
    void decodesHealthyKineticState() throws Exception {
        FakeKinetic fake = new FakeKinetic(96.0f, 128.0f, false, true);
        PowerSample sample = decode(fake);

        assertTrue(sample.available());
        assertTrue(sample.kineticallyPowered().orElseThrow());
        assertEquals(96.0, sample.speedRpm().orElseThrow(), 1.0e-6);
        assertEquals(128.0, sample.theoreticalSpeedRpm().orElseThrow(), 1.0e-6);
        assertFalse(sample.overstressed().orElseThrow());
        assertTrue(sample.networkPresent().orElseThrow());
        assertEquals(new BlockPos(2, 64, 3), sample.sourcePosition().orElseThrow());
    }

    @Test
    void overstressedNetworkIsNotPoweredEvenIfTheoreticalSpeedExists() throws Exception {
        FakeKinetic fake = new FakeKinetic(0.0f, 128.0f, true, true);
        PowerSample sample = decode(fake);

        assertFalse(sample.kineticallyPowered().orElseThrow());
        assertTrue(sample.overstressed().orElseThrow());
    }

    private static PowerSample decode(FakeKinetic fake) throws Exception {
        Method getSpeed = FakeKinetic.class.getMethod("getSpeed");
        Method getTheoreticalSpeed = FakeKinetic.class.getMethod("getTheoreticalSpeed");
        Method isOverStressed = FakeKinetic.class.getMethod("isOverStressed");
        Method hasNetwork = FakeKinetic.class.getMethod("hasNetwork");
        return CreateKineticDecoder.decode(
                "create.kinetic",
                fake,
                new BlockPos(1, 64, 3),
                new BlockPos(2, 64, 3),
                getSpeed,
                getTheoreticalSpeed,
                isOverStressed,
                hasNetwork
        );
    }

    public record FakeKinetic(float speed, float theoreticalSpeed, boolean overstressed, boolean network) {
        public float getSpeed() {
            return speed;
        }

        public float getTheoreticalSpeed() {
            return theoreticalSpeed;
        }

        public boolean isOverStressed() {
            return overstressed;
        }

        public boolean hasNetwork() {
            return network;
        }
    }
}
