package dev.drewcraft.aviation;

import java.util.Objects;
import java.util.OptionalDouble;
import net.minecraft.world.phys.Vec3;

/** Server-authoritative air-flow sample used by the MTS physics bridge and instruments. */
public record AviationAirflowSample(
        boolean available,
        Vec3 steadyWindMps,
        Vec3 turbulenceMps,
        Vec3 totalAirVelocityMps,
        OptionalDouble aboveGroundLevelBlocks,
        double turbulenceAmplitudeMps,
        String status
) {
    public AviationAirflowSample {
        Objects.requireNonNull(steadyWindMps);
        Objects.requireNonNull(turbulenceMps);
        Objects.requireNonNull(totalAirVelocityMps);
        Objects.requireNonNull(aboveGroundLevelBlocks);
        Objects.requireNonNull(status);
    }

    public static AviationAirflowSample unavailable(String status) {
        return new AviationAirflowSample(
                false,
                Vec3.ZERO,
                Vec3.ZERO,
                Vec3.ZERO,
                OptionalDouble.empty(),
                0.0,
                status
        );
    }
}
