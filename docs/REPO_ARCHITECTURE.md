# ServerMc Repository Architecture

ServerMc should be a **monorepo that describes, builds, tests, and releases the entire server experience**.

The repository is not itself the game installation. It is the canonical source from which client packs, server packs, custom code, launchers, infrastructure configuration, and version metadata are produced.

## 1. Target repository tree

```text
ServerMc/
├── README.md
├── AGENTS.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── PROJECT_SPEC.md
│   ├── SYSTEMS.md
│   ├── MOD_STACK.md
│   ├── REPO_ARCHITECTURE.md
│   ├── LAUNCHER_HOSTING.md
│   └── ROADMAP.md
│
├── pack/
│   ├── manifest/
│   │   ├── pack.yaml
│   │   ├── mods.yaml
│   │   ├── content-packs.yaml
│   │   └── java.yaml
│   ├── common/
│   │   ├── config/
│   │   ├── defaultconfigs/
│   │   ├── kubejs-or-datapacks-if-needed/
│   │   └── resourcepacks/
│   ├── client/
│   │   ├── config/
│   │   ├── shader-or-render-settings/
│   │   └── prism/
│   ├── server/
│   │   ├── config/
│   │   ├── defaultconfigs/
│   │   └── server.properties
│   └── overrides/
│
├── mods/
│   └── servermc/
│       ├── build.gradle(.kts)
│       ├── gradle.properties
│       ├── src/main/java/...
│       ├── src/main/resources/...
│       └── src/test/...
│
├── launcher/
│   ├── app/
│   ├── updater/
│   ├── platform/
│   │   ├── windows/
│   │   └── macos/
│   ├── assets/
│   └── tests/
│
├── server/
│   ├── scripts/
│   │   ├── install
│   │   ├── update
│   │   ├── start
│   │   ├── backup
│   │   └── restore
│   ├── systemd/
│   ├── updater/
│   └── monitoring/
│
├── infra/
│   ├── oracle/
│   │   ├── terraform-or-opentofu/
│   │   ├── cloud-init/
│   │   ├── firewall/
│   │   └── README.md
│   └── environments/
│       ├── dev/
│       └── prod/
│
├── world/
│   ├── README.md
│   ├── generation-config/
│   ├── chunky/
│   ├── checksums/
│   └── metadata/
│
├── tools/
│   ├── build-pack/
│   ├── verify-pack/
│   ├── generate-release-manifest/
│   ├── world-tools/
│   └── migration-tools/
│
├── tests/
│   ├── pack-smoke/
│   ├── multiplayer/
│   ├── compatibility/
│   └── performance/
│
└── .github/
    └── workflows/
        ├── ci.yml
        ├── build-pack.yml
        ├── launcher.yml
        ├── release.yml
        └── compatibility.yml
```

The exact build language/tooling can change. The ownership boundaries should not.

## 2. What belongs in Git

Commit:

- source code
- configs
- manifests
- scripts
- infrastructure-as-code
- documentation
- checksums
- datapacks/resourcepack source we own or can legally redistribute
- test fixtures small enough for Git
- world-generation parameters and metadata
- migration scripts

Do not commit:

- full generated world
- third-party mod jars by default
- Terrain Diffusion model files
- Java runtimes
- Prism binaries
- secrets/API keys
- server backups
- logs
- crash dumps unless reduced to a test fixture
- Distant Horizons databases
- enormous generated caches

## 3. Pack manifest is authoritative

`pack/manifest/` should be the source of truth for all release dependencies.

A build tool resolves the manifest into artifacts.

The manifest should allow fields such as:

```yaml
pack:
  id: servermc
  version: 0.1.0-dev
  minecraft: 1.21.1
  loader: neoforge

mods:
  - id: create
    version: ...
    side: common
    source: ...
    sha256: ...
```

Do not maintain separate manually curated mod lists for launcher and server.

## 4. Pack layers

### `pack/common`

Files that must be identical or semantically shared between client and dedicated server:

- gameplay config
- custom datapacks
- custom resource data required by gameplay
- ServerMc integration configuration where not server-secret

### `pack/client`

Client-only settings:

- Distant Horizons defaults
- rendering options
- keybind guidance/defaults where distributable
- launcher/Prism instance metadata
- client-only optimization mods

### `pack/server`

Dedicated-server-only settings:

- `server.properties`
- performance/server-side configs
- backup/administration config
- spawn/simulation limits
- server-only helper mods

### `pack/overrides`

Files injected verbatim into generated installations when they do not fit a more specific source directory.

Use sparingly; opaque override folders become hard to reason about.

## 5. Custom mod

`mods/servermc/` is the defining software component.

It should build one NeoForge jar containing internal feature modules documented in `SYSTEMS.md`.

Its version should normally track the ServerMc pack release closely.

Do not bury custom Java patches inside random launcher scripts or KubeJS unless a trivial data tweak is genuinely more appropriate there.

## 6. Launcher

`launcher/` owns the friend-facing bootstrap/update application.

Responsibilities:

- identify OS/architecture
- install or locate managed Prism Launcher
- provision supported Java 21
- acquire current ServerMc release manifest
- compare local file hashes
- download/update exact pack content
- import/create the managed Prism instance
- expose a simple Play/Update flow
- display useful errors rather than raw stack traces
- verify server pack compatibility/readiness before launch where possible

The launcher must never contain Oracle administrative credentials.

## 7. Server operations

`server/` owns scripts/configuration that execute *inside* the host.

Responsibilities:

- install server release
- validate hashes
- atomic update/swap
- start/stop through systemd
- controlled restart when pack updates are available
- backup world + custom persistence
- restore
- health/version reporting
- log retention

Keep operational scripts idempotent where possible.

## 8. Infrastructure

`infra/` describes the cloud resources, not the game itself.

Initial target: Oracle Cloud Infrastructure Ampere A1 ARM.

Infrastructure-as-code should define only what is required:

- instance shape
- boot/block volume
- network/firewall
- SSH/admin access
- Minecraft port
- monitoring/backups where applicable

The production environment must not allow a casual code path to resize/provision paid resources automatically.

## 9. World artifacts

`world/` contains the **recipe and identity** of the production world, not its chunks.

Keep:

- Terrain Diffusion configuration
- world seed/identity metadata where applicable
- World Scale value
- border/pregeneration parameters
- Chunky commands/config
- source-structure indexing metadata format
- expected hashes for packaged world snapshots
- world schema/version notes

Store actual world archives externally, such as release/object storage, with checksums referenced here.

## 10. Release artifacts

A release can contain or reference:

```text
ServerMc-<version>-client-pack.zip
ServerMc-<version>-server-pack.tar.zst
ServerMc-<version>-windows-installer.exe
ServerMc-<version>-macos-universal.dmg (or signed app archive)
servermc-<version>.jar
release-manifest.json
checksums.txt
```

The large world snapshot should normally have its own artifact lifecycle because it changes less frequently and may be much larger than a pack release.

## 11. `release-manifest.json`

The release manifest is the contract among CI, launcher, and server updater.

Conceptual structure:

```json
{
  "packVersion": "0.1.0",
  "minecraftVersion": "1.21.1",
  "loader": {"type": "neoforge", "version": "..."},
  "minimumLauncherVersion": "...",
  "protocolVersion": 1,
  "artifacts": {
    "client": {"url": "...", "sha256": "..."},
    "server": {"url": "...", "sha256": "..."}
  },
  "files": [
    {"path": "mods/...jar", "sha256": "...", "side": "common"}
  ]
}
```

The actual schema should be versioned from the first implementation.

## 12. Versioning

Use semantic-ish ServerMc release versions:

- `0.x` during development/playtesting
- `1.0` only after the acceptance criteria in `PROJECT_SPEC.md` pass

World format changes and custom persistence migrations must be called out explicitly in release notes.

## 13. CI expectations

Every change to pack/custom code should be able to run some subset of:

- manifest schema validation
- duplicate/mod-side validation
- download/hash verification
- custom mod compile/test
- generated client pack sanity check
- generated server pack sanity check
- dedicated server boot smoke test
- launcher unit/integration tests
- release manifest validation

Scheduled compatibility checks may detect upstream releases, but they should open/update information—not silently change production versions.

## 14. Secrets

Secrets belong in GitHub Actions secrets, Oracle secret storage, or administrator machines as appropriate.

Never commit:

- OCI private keys
- API tokens
- SSH private keys
- Microsoft auth tokens
- server RCON credentials
- signing/notarization credentials

The launcher distributed to friends must operate without privileged infrastructure credentials.

## 15. Why a monorepo

The launcher, server pack, integration mod, and deployment are tightly coupled by version.

A monorepo makes it possible to say:

> commit X produced ServerMc release Y, containing custom mod Z, client manifest A, server manifest B, and launcher compatibility C.

That reproducibility is more important than artificially separating components into many repositories.
