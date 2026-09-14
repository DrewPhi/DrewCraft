# Flightstone Standard Visual Specification

## Status

Canonical visual and implementation specification for the DrewCraft Flightstone Standard.

This document complements `docs/FLIGHTSTONE_STANDARD_AND_SIEGE_PROTECTION.md`, which defines ownership, placement, protection, discovery, targeting, capture, and recovery.

---

## 1. It is a real vanilla Minecraft banner

The Flightstone Standard is **not** a custom cloth model and does not use a bespoke banner texture.

It is an ordinary **white Minecraft banner** carrying a fixed combination of vanilla banner-pattern layers. The goal is to make the civilization symbol feel completely native to Minecraft and to preserve all normal banner behavior:

- the cloth uses the vanilla banner model and waving renderer;
- the design can be displayed as an ordinary standing or wall banner where appropriate;
- the heraldry can be copied onto shields through Minecraft's normal banner + shield behavior;
- no custom shader, cloth renderer, or banner atlas is required.

The Standard's strategic powers come from DrewCraft's server-side Standard identity/state, **not from merely matching the visual pattern**.

Decorative copies and shields may therefore display the same civilization heraldry without becoming protection objects.

---

## 2. Canonical heraldry — Design V1

Base item:

- `minecraft:white_banner`

Pattern layers, in draw order:

1. **Yellow Border** — `minecraft:border`
2. **Yellow Horizontal Center Stripe** — `minecraft:stripe_middle`
3. **Yellow Vertical Center Stripe** — `minecraft:stripe_center`
4. **White Center Diamond / Lozenge** — `minecraft:rhombus`
5. **Yellow Center Roundel** — `minecraft:circle`

The resulting symbol is intentionally geometric and Minecraft-native. It reads as a stylized aviation mark:

- the horizontal yellow bar suggests **wings**;
- the vertical yellow bar suggests the **propeller/ascent axis**;
- the white diamond cuts negative space around the center like a **spinner/fairing**;
- the yellow roundel forms a **propeller hub / aviation roundel**;
- the yellow border gives the civilization a strong safety/aviation-color frame.

The base white field keeps the design bright and immediately distinct from the Covenant's charcoal, slate, oxblood, aged-ivory, and old-gold palette.

The design should stay deliberately simple. It needs to remain legible on both a full banner and the much smaller shield rendering.

---

## 3. Palette

The canonical V1 palette uses vanilla Minecraft dye colors:

- **White** base and center negative space;
- **Yellow** heraldry and border.

Conceptually this corresponds to DrewCraft's aviation-yellow + warm-white/ivory visual language.

Do not introduce a custom texture merely to obtain a slightly warmer white or brassier yellow. Minecraft-native readability and automatic shield compatibility are more valuable than exact RGB matching.

---

## 4. Banner versus Standard identity

The visual design and the gameplay object are deliberately separated.

### Civilization heraldry

Any ordinary banner or shield carrying the same visual layers is simply DrewCraft civilization heraldry.

Players should be free to:

- copy the design onto shields;
- use matching banners decoratively around forts, airports, ships, trains, towns, and military positions;
- reproduce the visual motif without accidentally creating protected territory.

### Flightstone Standard

A real Flightstone Standard is an issued, player-owned strategic object tracked by DrewCraft server state.

The prototype item includes a marker and design version for inspection/debugging, but the eventual authoritative implementation must use the player's persistent `StandardRecord`/ownership state rather than trusting copied item data alone.

This prevents banner duplication, NBT/component copying, commands, or shield decoration from creating additional active Standards.

---

## 5. Enchanted presentation

The issued Flightstone Standard item should have a subtle enchanted glint so it feels like an important civilization artifact in the inventory.

The placed banner itself should still use Minecraft's ordinary banner renderer. Do not replace the cloth with a glowing or custom animated model.

The monumental in-world effect comes from the beacon beam, not from making the cloth visually non-Minecraft-like.

---

## 6. The beam is literally Minecraft's vanilla beacon beam

Hard requirement:

> **An active Flightstone Standard emits the actual vanilla Minecraft beacon beam visual. It is not merely beacon-like.**

Reuse the existing vanilla beacon beam rendering implementation as directly as practical for NeoForge 1.21.1.

Do not create:

- a separate volumetric-light shader;
- a custom fake beam texture;
- a particle column intended to imitate a beacon;
- a second independent beam rendering system.

The Standard does not require a beacon pyramid. DrewCraft's Standard activation rules determine whether the vanilla beam is rendered.

---

## 7. Beam color

Preferred appearance is the closest clean vanilla-beacon treatment to the Standard's yellow/white palette:

- pale yellow / golden-white where the existing renderer permits it cleanly;
- otherwise prefer a simple vanilla-supported yellow/white result over fragile custom renderer replacement.

The important requirement is recognizably using Minecraft's beacon beam, not exact color science.

---

## 8. Beam activation

The beam renders only while the actual player-owned Standard is active under the canonical gameplay rules.

In particular it must be:

- placed in the ordinary world;
- validly owned/registered as that player's Standard;
- under true unobstructed sky according to DrewCraft's stricter sky rule;
- anchored to the normal world rather than a moving Create/Sable/Aeronautics/High Seas contraption;
- not captured, destroyed, or otherwise inactive.

### Active

- vanilla beacon beam visible upward;
- 300-block 3D protection sphere active;
- Standard is eligible for Covenant discovery at the configured 800-block horizontal radius.

### Inactive

- no beam;
- no protection sphere from that Standard;
- visual copies on banners/shields remain purely decorative.

---

## 9. True-sky rule remains stricter than vanilla beacon rules

The beacon renderer does not define Standard placement legality.

DrewCraft's gameplay validator does.

The Standard requires true open sky:

- glass above it is still invalid;
- roofs, leaves, slabs, trapdoors, terrain, or other covering blocks that obstruct the vertical column are invalid;
- an open vertical shaft is technically valid.

This is intentional even if a vanilla beacon might visually tolerate blocks that DrewCraft does not.

---

## 10. Shield use

Shield compatibility is a design requirement, not an accidental bonus.

Because the heraldry consists entirely of vanilla banner layers, players should be able to combine a decorative/canonical-pattern banner with a shield using normal Minecraft mechanics and receive the same civilization motif on the shield.

A decorated shield:

- carries the symbol;
- has no settlement-protection power;
- emits no beacon beam;
- is not discoverable as a Standard;
- does not count toward the player's one-Standard limit.

This lets the same visual language appear naturally on defenders during sieges without adding a custom shield item.

---

## 11. Current prototype implementation

`FlightstoneStandardDesign` constructs the V1 pattern directly with Minecraft data components.

For development inspection, the DrewCraft admin command:

```text
/drewcraft standard give
```

gives the executing player the canonical prototype Standard.

The prototype intentionally proves the visual/item representation first. Full first-join issuance, placement validation, persistent ownership, beacon rendering, protection, scout discovery, capture, and recovery are implemented by the broader Standard system rather than by the banner pattern itself.

---

## 12. Canon summary

The Flightstone Standard is:

> **A genuine vanilla white Minecraft banner bearing a simple yellow aviation heraldry, usable as the same heraldry on ordinary shields, distinguished as the player's unique Standard by DrewCraft server state, and projecting Minecraft's actual vanilla beacon beam while actively raised under open sky.**

The civilization should be able to put its symbol everywhere. Only the one Standard belonging to a player carries the strategic consequences.
