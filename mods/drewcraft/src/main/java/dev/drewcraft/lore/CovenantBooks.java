package dev.drewcraft.lore;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.network.chat.Component;
import net.minecraft.server.network.Filterable;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.WrittenBookContent;

/** Builds Covenant scripture books: field fragments and sealed archives. */
public final class CovenantBooks {
    private CovenantBooks() {
    }

    public static ItemStack fieldBook(String siteDisplayName, int x, int y, int z, String mode) {
        List<String> pages = WaymarkRenderer.render(siteDisplayName, x, y, z, mode);
        return writtenBook("Divided Waymark: " + siteDisplayName, "Covenant Press", pages);
    }

    public static ItemStack sealedArchive(String siteKey, String archiveTitle, int x, int y, int z) {
        return writtenBook(archiveTitle, "Covenant Press", sealedArchivePages(siteKey, archiveTitle, x, y, z));
    }

    /** Pure page text, unit-tested without booting Minecraft registries. */
    public static List<String> sealedArchivePages(String siteKey, String archiveTitle, int x, int y, int z) {
        List<String> pages = new ArrayList<>();
        pages.add("SEALED ARCHIVE\n" + archiveTitle + "\n\n"
                + "Recovered where its Source Core fell.\n\n"
                + "X: " + x + "\nY: " + y + "\nZ: " + z + "\n\n"
                + "Site key: " + siteKey);
        return pages;
    }

    public static ItemStack writtenBook(String title, String author, List<String> pages) {
        ItemStack stack = new ItemStack(Items.WRITTEN_BOOK);
        List<Filterable<Component>> filtered = new ArrayList<>();
        for (String page : pages) {
            filtered.add(Filterable.passThrough(Component.literal(page)));
        }
        stack.set(net.minecraft.core.component.DataComponents.WRITTEN_BOOK_CONTENT,
                new WrittenBookContent(Filterable.passThrough(title), author, 0, filtered, false));
        return stack;
    }
}
