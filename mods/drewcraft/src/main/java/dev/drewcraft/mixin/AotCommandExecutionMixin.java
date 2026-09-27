package dev.drewcraft.mixin;

import com.mojang.brigadier.context.CommandContext;
import dev.drewcraft.aot.AotCommandPolicy;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.ExecutionCommandSource;
import net.minecraft.commands.execution.ExecutionContext;
import net.minecraft.commands.execution.Frame;
import net.minecraft.commands.execution.tasks.ExecuteCommand;
import net.minecraft.network.chat.Component;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Covers queued/function execution as well as ordinary CommandEvent dispatch. */
@Mixin(ExecuteCommand.class)
public abstract class AotCommandExecutionMixin {
    @Shadow @Final private CommandContext<?> executionContext;

    @SuppressWarnings("unchecked")
    @Inject(method = "execute(Lnet/minecraft/commands/ExecutionCommandSource;Lnet/minecraft/commands/execution/ExecutionContext;Lnet/minecraft/commands/execution/Frame;)V",
            at = @At("HEAD"), cancellable = true, require = 1)
    private void drewcraft$denySpecialPrivileges(ExecutionCommandSource<?> source,
            ExecutionContext<?> context, Frame frame, CallbackInfo ci) {
        if (source instanceof CommandSourceStack stack && AotCommandPolicy.blocks(
                stack.dispatcher().getRoot(), (CommandContext<CommandSourceStack>) executionContext)) {
            stack.sendFailure(Component.literal("Special AOT privileges are disabled on DrewCraft."));
            stack.callback().onFailure();
            ci.cancel();
        }
    }
}
