package dev.drewcraft.aot;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.builder.RequiredArgumentBuilder;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AotCommandPolicyTest {
    private static LiteralArgumentBuilder<String> literal(String name) {
        return LiteralArgumentBuilder.literal(name);
    }

    private static CommandDispatcher<String> dispatcher() {
        CommandDispatcher<String> dispatcher = new CommandDispatcher<>();
        var daot = dispatcher.register(literal("daot")
                .then(literal("danny").then(literal("vanish").executes(c -> 1))
                        .then(literal("power").then(literal("homelander").executes(c -> 1)))
                        .then(literal("shifter").then(literal("attack").executes(c -> 1))))
                .then(literal("shifter").then(literal("check").executes(c -> 1)))
                .then(literal("bloodline").then(literal("check").executes(c -> 1))));
        dispatcher.register(literal("dannys-aot:daot").redirect(daot));
        dispatcher.register(literal("shortcut").redirect(daot.getChild("danny")));
        dispatcher.register(literal("execute").then(literal("run").redirect(dispatcher.getRoot())));
        dispatcher.register(literal("say").then(RequiredArgumentBuilder
                .<String, String>argument("message", StringArgumentType.greedyString()).executes(c -> 1)));
        return dispatcher;
    }

    @Test void blocksPrivilegesIncludingRedirectedExecution() {
        var dispatcher = dispatcher();
        for (String command : new String[]{"daot danny vanish", "daot danny power homelander",
                "daot danny shifter attack", "dannys-aot:daot danny vanish",
                "shortcut vanish", "execute run daot danny vanish",
                "execute run execute run shortcut vanish"}) {
            var parse = dispatcher.parse(command, "player");
            assertFalse(parse.getReader().canRead(), command);
            assertTrue(AotCommandPolicy.blocks(parse), command);
        }
    }

    @Test void leavesOrdinaryCommandsAndChatAlone() {
        var dispatcher = dispatcher();
        for (String command : new String[]{"daot shifter check", "daot bloodline check",
                "execute run daot shifter check", "say /daot danny vanish"}) {
            assertFalse(AotCommandPolicy.blocks(dispatcher.parse(command, "operator")), command);
        }
    }

    @Test void harmlessWhenAotAbsent() {
        var dispatcher = new CommandDispatcher<String>();
        dispatcher.register(literal("help").executes(c -> 1));
        assertFalse(AotCommandPolicy.blocks(dispatcher.parse("help", "console")));
    }

    @Test void blocksFlattenedExecutionContextUsedByQueuedCommands() {
        var dispatcher = dispatcher();
        String input = "execute run shortcut vanish";
        var context = dispatcher.parse(input, "function").getContext().build(input);
        while (context.getChild() != null) context = context.getChild();
        assertTrue(AotCommandPolicy.blocks(dispatcher.getRoot(), context));
    }
}
