# DrewCraft Lore Drop Implementation Contract

## Runtime source of coordinates

Do not bake production coordinates into the lore source files.

`cult_books.json` references `target_site` IDs. At item-drop time, DrewCraft resolves that ID against the production `cult_sites.json` registry and renders the final Divided Waymark page.

## Coordinate roll

Use exactly one categorical roll:

- X only — 38%
- Z only — 38%
- X + Y — 9%
- Z + Y — 9%
- X + Z — 4.5%
- X + Y + Z — 1.5%

Always print the destination name.

Hidden axes render as `[withheld]`.

Every physical copy rolls separately, even when two mobs drop the same title.

## Field books

The 32 `field_lore` records target one of the eight regional cult sites.

Suggested routing:

- if the mob belongs to a strategic group with `home_source_id`, 75% target its home source;
- 25% target another uncleared cult source;
- mobs without a home source choose an uncleared cult source;
- cleared sites retain only a very small clue weight (suggested 5%).

The actual title can be selected from the four field books assigned to that target site.

## Sealed capital fragments

The eight `sealed_capital_fragment` records target Vespera.

They are associated with one origin site each.

They remain enemy drops, but should be restricted to enemies belonging to that origin site's source/bounds.

Recommended rule:

- very low random chance on that site's elite defenders;
- first acquisition guaranteed as part of the site's Source Core clear sequence through an enemy drop;
- once acquired, duplicates can still appear but at reduced weight.

The world border/frontier opening should still require the intended Source Core clears, not merely possession of a lucky early capital book.

## Flightstone

On Source Core clear:

- activate that Chain's sigil;
- record the site as cleared;
- archive any recovered sealed text;
- display the next sparse aviation-spirit message.

The Flightstone is a persistent campaign record, not a replacement for collecting/reading the books.

## Written-book rendering

Each book should render:

1. title/author;
2. the three authored lore pages;
3. one generated Divided Waymark page.

The data is intentionally content-first. Convert the page strings into the Minecraft 1.21.1 written-book item component in the DrewCraft integration layer.
