package dev.drewcraft.aot;

import com.mojang.brigadier.ParseResults;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.tree.CommandNode;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Server policy, not a modification of AOT's protected command/power classes. */
public final class AotCommandPolicy {
    private AotCommandPolicy() {}

    public static <S> boolean blocks(ParseResults<S> parse) {
        return blocks(parse.getContext().getDispatcher().getRoot(),
                parse.getContext().build(parse.getReader().getString()));
    }

    public static <S> boolean blocks(CommandNode<S> dispatcherRoot, CommandContext<S> context) {
        Set<CommandNode<S>> denied = Collections.newSetFromMap(new IdentityHashMap<>());
        for (CommandNode<S> root : dispatcherRoot.getChildren()) {
            String name = root.getName();
            if (name.equals("daot") || name.endsWith(":daot")) {
                collect(root.getChild("danny"), denied);
            }
        }
        // Inspect actual parsed nodes, not input text: handles execute/run and
        // redirected aliases without blocking chat containing command examples.
        for (; context != null; context = context.getChild()) {
            if (denied.contains(context.getRootNode())) return true;
            for (var parsed : context.getNodes()) {
                if (denied.contains(parsed.getNode())) return true;
            }
        }
        return false;
    }

    private static <S> void collect(CommandNode<S> node, Set<CommandNode<S>> denied) {
        if (node == null || !denied.add(node)) return;
        for (CommandNode<S> child : node.getChildren()) collect(child, denied);
        // Do not follow redirects out of the denied subtree into ordinary commands.
    }
}
