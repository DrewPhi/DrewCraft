# Flightstone Standard Visual Specification

## Status

Canonical visual/art-direction plan for the DrewCraft Flightstone Standard.

This document complements `docs/FLIGHTSTONE_STANDARD_AND_SIEGE_PROTECTION.md`, which defines the Standard's gameplay, protection, discovery, targeting, and recovery rules.

---

## 1. Core visual identity

The Flightstone Standard is the primary civic and military symbol of the DrewCraft civilization.

It should look immediately distinct from the Covenant of the Closed Sky and communicate:

- aviation;
- optimism;
- engineering;
- sacred civic purpose;
- visibility rather than concealment.

The object should read as something a settlement is proud to raise in an exposed courtyard, airfield, tower platform, or civic plaza.

It is not supposed to look like an ordinary vanilla banner with a gameplay effect attached. It should feel like a unique enchanted civilization artifact.

---

## 2. Palette

Primary palette:

- **aviation yellow** — dominant emblem/accent color;
- **warm white / ivory** — dominant cloth/background color;
- **pale gold / brass** — small structural and trim accents;
- optional very small neutral metallic details where needed for readability.

The palette should be bright and highly legible against the Covenant's blackened charcoal, slate, warm stone, oxblood, aged ivory, and old-gold visual language.

The intended contrast is deliberate:

- Covenant: grounded, dark, stone-heavy, oxblood religious militarism;
- DrewCraft Standard: open sky, warm white, aviation yellow, light, engineering, ascent.

Avoid saturated fantasy-neon yellow. The yellow should feel closer to practical aviation/safety paint or golden aircraft markings than magical fluorescent dye.

---

## 3. Banner / artifact form

The Standard should be a custom banner-like block or banner-derived block with enough visual distinction that players can recognize it immediately.

Preferred qualities:

- warm-white/ivory cloth field;
- large aviation-yellow civilization emblem;
- pale brass/gold trim or fittings;
- subtle enchanted glint/shimmer;
- readable silhouette from a distance;
- visually attractive enough to serve as the centerpiece of a town square or fortress courtyard.

The final emblem can be refined later, but it should communicate flight/ascent rather than copying the Covenant's downward/broken-wing symbolism.

A stylized upward wing, propeller, rising star, or wing-and-sun motif would all fit the civilization's established aviation theology.

---

## 4. The beam is the actual Minecraft beacon beam

This is a hard visual requirement:

> **An active Flightstone Standard emits the actual vanilla Minecraft beacon beam visual. It is not merely "beacon-like" and should not use a separately designed custom light-column effect.**

Implementation should reuse Minecraft's existing beacon-beam rendering behavior/renderer as directly as is practical for NeoForge 1.21.1.

Reasons:

- it is immediately recognizable to every Minecraft player;
- it is already optimized and visually coherent with the game;
- it gives the Standard monumental presence without introducing another bespoke rendering system;
- it reinforces the true-sky-visibility placement rule;
- it provides an obvious visual indication that protection is active;
- when the Standard falls or deactivates, the disappearance of the beam instantly communicates loss of protection.

The Standard does **not** need to be built on a vanilla beacon pyramid. Its own gameplay rules determine whether it is active.

---

## 5. Beam color

The beam should use the vanilla beacon beam rendering system but with a DrewCraft-appropriate color treatment.

Preferred default:

- warm white / very pale golden-white core;
- subtle aviation-yellow tint or segmentation where supported cleanly by the reused vanilla system.

The goal is to preserve the unmistakable Minecraft beacon appearance while visually tying it to the Standard's white/yellow palette.

Do not replace the vanilla beam with volumetric custom lighting merely to achieve more elaborate coloring.

If exact custom tinting requires fragile renderer replacement, prefer a vanilla-supported beacon-beam color that is visually close to warm white/yellow rather than creating a bespoke renderer.

---

## 6. Beam activation rules

The beam renders only while the Standard is **active**.

An active Standard must satisfy the canonical gameplay rules, including:

- placed in the ordinary world rather than carried/stored;
- true unobstructed line of sight to the sky;
- not active as part of a moving Create contraption, train, Sable/Aeronautics craft, High Seas ship, airship, or other moving sub-level;
- not captured/destroyed/deactivated.

The beam therefore doubles as a visual status indicator.

### Active

- vanilla beacon beam visible upward;
- 300-block protection sphere active;
- Standard may be discovered by Covenant scouts within the configured 800-block horizontal discovery radius.

### Inactive / removed / captured

- beam disappears;
- no protection sphere from that Standard;
- strategic behavior follows the canonical Standard/siege rules.

---

## 7. Sky visibility and visual logic

The Standard already requires true sky visibility for gameplay reasons. The beacon beam makes that rule visually intuitive.

A player should be able to look at the object and understand why it cannot be placed beneath a roof: the Standard is literally projecting its civilization's signal vertically into the sky.

Glass still counts as a roof under the current design. The beam should not be used as a reason to weaken that placement rule merely because vanilla beacons can visually pass through some blocks.

Gameplay validity remains controlled by DrewCraft's explicit Standard validator.

---

## 8. Relationship to gameplay

The visual design should make the Standard's gameplay function readable without additional UI.

A settlement with a visible beam communicates:

- this is protected territory;
- this is an active player settlement;
- this is the objective strategic enemies ultimately care about;
- this location has true sky exposure;
- losing this object has consequences.

During a siege, the beam becomes an obvious rallying point for defenders and an obvious final objective for attackers.

When the Standard is destroyed, the instant disappearance of the beam should make the loss legible even before the player reads any message or notices structural-protection changes.

---

## 9. Performance and implementation preference

Prefer reuse over invention.

Implementation order:

1. reuse vanilla beacon beam rendering/API behavior directly if accessible;
2. use a narrow accessor/mixin only if needed to invoke the existing renderer cleanly;
3. avoid copying/reimplementing the entire beacon renderer;
4. do not create a separate shader/volumetric-beam system for V1.

The Standard's custom work should focus on:

- block/model/texture;
- active-state validation;
- the protection/strategic systems;
- invoking the existing vanilla beam visual.

This keeps the effect Minecraft-native, stable, and inexpensive to maintain.

---

## 10. Canon summary

The canonical Flightstone Standard should therefore be understood as:

> **A beautiful enchanted warm-white and aviation-yellow civic banner/artifact, raised under open sky, that literally projects Minecraft's vanilla beacon beam upward while active.**

It is the visual opposite of the Covenant's ideology: the Covenant fears human severance from the earth, while the DrewCraft civilization deliberately raises a brilliant signal into the open sky from the center of the settlement it has chosen to defend.
