package dev.drewcraft.mixin;

import java.io.IOException;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.storage.RegionFileStorage;
import net.neoforged.fml.ModList;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Avoid DH 3.3.1's hardcoded Anvil fallback when Linear owns region storage. */
@Pseudo
@Mixin(targets = "com.seibel.distanthorizons.common.wrappers.worldGeneration.mimicObject.RegionFileStorageExternalCache_neoforge",
        remap = false)
public abstract class DhLinearRegionReaderMixin {
    @Shadow @Final public RegionFileStorage storage;

    @Inject(method = "read", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void drewcraft$readThroughLinearStorage(ChunkPos pos,
            CallbackInfoReturnable<CompoundTag> callback) throws IOException {
        if (ModList.get().isLoaded("linear")) {
            // Use the SAME storage object, not a second LinearRegionFile instance:
            // this sees pending writes and uses Linear's locking/cache policy.
            // IOException is propagated; corrupt data is not reported as absent.
            callback.setReturnValue(storage == null ? null : storage.read(pos));
        }
    }
}
