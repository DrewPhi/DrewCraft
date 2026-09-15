package dev.drewcraft.command;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.suggestion.SuggestionProvider;
import java.util.Map;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;

/**
 * Debug/convenience summoning for the six retextured Covenant roles.
 *
 * <p>Usage: {@code /drewcraft summon <role> [count]}. Spawned mobs are
 * deliberately <em>ordinary</em> entities: they carry no strategic tags, so
 * they never touch group strength, casualties, lore drops, or source
 * accounting. Strategic testing must go through encounters, not this command.
 */
public final class SummonCommands {
    /** Covenant role -> tactical entity backing the retextured skin. */
    static final Map<String, String> ROLE_TO_ENTITY = Map.of(
            "footman", "illagerinvasion:basher",
            "cleric", "illagerinvasion:archivist",
            "crusader", "illagerinvasion:inquisitor",
            "prelate", "illagerinvasion:firecaller",
            "priest", "illagerinvasion:necromancer",
            "high_inquisitor", "illagerinvasion:invoker"
    );

    private static final SuggestionProvider<CommandSourceStack> ROLES =
            (context, builder) -> SharedSuggestionProvider.suggest(ROLE_TO_ENTITY.keySet(), builder);

    private SummonCommands() {
    }

    public static LiteralArgumentBuilder<CommandSourceStack> node() {
        return Commands.literal("summon").then(summonRole());
    }

    private static com.mojang.brigadier.builder.RequiredArgumentBuilder<CommandSourceStack, String> summonRole() {
        return Commands.argument("role", StringArgumentType.word()).suggests(ROLES)
                .executes(context -> summon(context.getSource(), StringArgumentType.getString(context, "role"), 1))
                .then(Commands.argument("count", com.mojang.brigadier.arguments.IntegerArgumentType.integer(1, 12))
                        .executes(context -> summon(context.getSource(),
                                StringArgumentType.getString(context, "role"),
                                com.mojang.brigadier.arguments.IntegerArgumentType.getInteger(context, "count"))));
    }

    static int summon(CommandSourceStack source, String role, int count) {
        String entityId = ROLE_TO_ENTITY.get(role);
        if (entityId == null) {
            source.sendFailure(Component.literal("Unknown Covenant role '" + role
                    + "'. Expecting one of " + String.join(", ", ROLE_TO_ENTITY.keySet())));
            return 0;
        }
        if (!(source.getLevel() instanceof ServerLevel level)) {
            source.sendFailure(Component.literal("Covenant summoning requires a server level"));
            return 0;
        }
        EntityType<?> rawType = EntityType.byString(entityId).orElse(null);
        if (rawType == null) {
            source.sendFailure(Component.literal("Entity type not present (is Illager Invasion installed?): " + entityId));
            return 0;
        }
        BlockPos origin = BlockPos.containing(source.getPosition());
        int spawned = 0;
        for (int i = 0; i < count; i++) {
            BlockPos pos = origin.offset(i % 3, 0, i / 3);
            Entity entity = rawType.create(level);
            if (entity == null) continue;
            entity.moveTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5,
                    level.random.nextFloat() * 360.0f, 0.0f);
            if (!level.noCollision(entity)) {
                entity.discard();
                continue;
            }
            level.addFreshEntityWithPassengers(entity);
            if (entity instanceof net.minecraft.world.entity.Mob mob) {
                mob.setPersistenceRequired();
            }
            // Intentionally untagged: convenience summons are ordinary mobs.
            entity.setCustomName(Component.literal("Covenant " + role));
            spawned++;
        }
        int total = spawned;
        source.sendSuccess(() -> Component.literal(
                "Summoned " + total + " Covenant " + role + " (" + entityId + ") as ordinary mobs"), true);
        return total > 0 ? 1 : 0;
    }
}
