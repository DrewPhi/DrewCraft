package dev.drewcraft.adapter.create;

import dev.drewcraft.service.power.PowerSample;
import dev.drewcraft.service.power.PowerService;
import java.lang.reflect.Method;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.entity.BlockEntity;

/** Read-only Create kinetic adapter for DrewCraft machinery. */
public final class CreatePowerService implements PowerService {
    public static final String PROVIDER_ID = "create.kinetic";
    private static final String KINETIC_CLASS = "com.simibubi.create.content.kinetics.base.KineticBlockEntity";

    private final Bindings bindings;

    public CreatePowerService() {
        this.bindings = Bindings.tryBind();
    }

    @Override
    public String providerId() {
        return PROVIDER_ID;
    }

    @Override
    public PowerSample sample(ServerLevel level, BlockPos position) {
        if (level == null || position == null) {
            return PowerSample.unavailable(providerId(), position == null ? BlockPos.ZERO : position, "invalid_request");
        }
        if (bindings == null) {
            return PowerSample.unavailable(providerId(), position, "create_kinetic_api_unavailable");
        }

        PowerSample exact = sampleCandidate(level, position, position);
        if (exact != null) {
            return exact;
        }
        for (Direction direction : Direction.values()) {
            BlockPos candidate = position.relative(direction);
            PowerSample adjacent = sampleCandidate(level, position, candidate);
            if (adjacent != null) {
                return adjacent;
            }
        }
        return PowerSample.noInput(providerId(), position);
    }

    private PowerSample sampleCandidate(ServerLevel level, BlockPos requestedPosition, BlockPos candidate) {
        if (!level.hasChunkAt(candidate)) {
            return null;
        }
        BlockEntity blockEntity = level.getBlockEntity(candidate);
        if (blockEntity == null || !bindings.kineticClass.isInstance(blockEntity)) {
            return null;
        }
        return CreateKineticDecoder.decode(
                providerId(),
                blockEntity,
                requestedPosition,
                candidate,
                bindings.getSpeed,
                bindings.getTheoreticalSpeed,
                bindings.isOverStressed,
                bindings.hasNetwork
        );
    }

    private record Bindings(
            Class<?> kineticClass,
            Method getSpeed,
            Method getTheoreticalSpeed,
            Method isOverStressed,
            Method hasNetwork
    ) {
        private static Bindings tryBind() {
            try {
                Class<?> kineticClass = Class.forName(KINETIC_CLASS, false, CreatePowerService.class.getClassLoader());
                return new Bindings(
                        kineticClass,
                        kineticClass.getMethod("getSpeed"),
                        kineticClass.getMethod("getTheoreticalSpeed"),
                        kineticClass.getMethod("isOverStressed"),
                        kineticClass.getMethod("hasNetwork")
                );
            } catch (ReflectiveOperationException | LinkageError exception) {
                return null;
            }
        }
    }
}
