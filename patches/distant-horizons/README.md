# DrewCraft DH 3.3.3 compatibility candidate

This is a source patch to upstream DH, licensed under upstream's LGPL-3.0.
Copyright notices and both original license files remain in the resulting jar
and complete upstream source archive. No model weights or Minecraft world are
committed. The compiled candidate is **not** a published production update.

Source pins:

- Main: https://gitlab.com/distant-horizons-team/distant-horizons at
  `a54dd3eb1df0078e63a71266d042c10d9cda4493` (3.3.3 tag).
- Core submodule: `b02c66d778beea11a931291815d652cd8abaa7ad`.
- Base release: Modrinth `uCdwusMi / 9w34y8ai`, whose exact SHA-512 is checked
  by `tools/build_dh_compat.py`.

The fix changes only `AbstractChunkyAccessor`: synchronize listener setup,
defer specifically `IllegalStateException("Chunky is not loaded")`, and set
listenerBound only after success. Subsequent chunk updates retry setup.
All other exceptions still propagate. Chunky's generation event and DH's
generation suppression/re-enable logic remain unchanged. This fixes the observed
startup lifecycle failure; it does not claim to fix aircraft throughput.

Build from the pinned upstream tree, plus the official base jar:

```sh
python3 tools/build_dh_compat.py --source build/dh-upstream-3.3.3 --jar /path/to/DistantHorizons-3.3.3-1.21.1-fabric-neoforge.jar --dependency-jar /path/to/log4j-api-2.22.1.jar --dependency-jar /path/to/log4j-core-2.22.1.jar --output build/dh-candidate
```

The builder compiles this one source class against the pinned release, preserving
every other jar entry byte-for-byte (including native libraries, loader-specific
classes, resources and licenses). It runs the same Java regression probe against
the original and patched class: original must reproduce the failure; patched must
allow delayed initialization, register once under concurrent calls, and propagate
unrelated errors. It emits a complete source archive, build recipe, patch and
hash report alongside the candidate jar. This is a targeted source rebuild,
not a claim to have compiled the entire upstream multi-loader project.

Release gates: isolated NeoForge/Chunky boot and native DH pregen, then exact
DrewCraft stack including Linear adapter and saved production-style chunks/LODs.
DH 3.3.3 resets config version 4 to 5, so preserve and migrate server/client
settings explicitly before any upgrade. Do not mutate the production database,
swap the live jar or publish the client pointer before these gates pass. A fresh
verified backup must include DH data because database rollback is separate from
application rollback. C2ME and Krypton benchmarks remain separate changes.
