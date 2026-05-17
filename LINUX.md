# Nauqtype Linux Alpha

Nauqtype is ready for Linux alpha development from this repository checkout. It is not yet a distro package or system compiler.

## Current Contract

- The active compiler driver is the self-hosted stage1 binary at `selfhost/build/nauqc`.
- The repo-local Linux launcher is `bin/nauqc`.
- `bin/nauqc` runs the stage1 driver from the repository root so `stdlib/runtime.c`, `.deps/ziglang/zig`, and the Linux `cc` fallback are found consistently.
- Source and output paths passed through `bin/nauqc` are normalized from the caller's current directory before the stage1 driver runs.
- `scripts/install_nauqtype.sh` installs a symlink to the launcher, defaulting to `$HOME/.local/bin/nauqc`.

## Bootstrap

From the repository root:

```bash
python3 scripts/setup_deps.py
python3 -m compiler.main run selfhost/main.nq
python3 -m compiler.main build selfhost/main.nq -o selfhost/build/nauqc
```

After that, use the stage1-owned driver:

```bash
bin/nauqc check examples/hello.nq
bin/nauqc run examples/hello.nq
bin/nauqc prove
```

## Optional Local Install

```bash
scripts/install_nauqtype.sh
```

Or choose another prefix:

```bash
PREFIX=/opt/nauqtype scripts/install_nauqtype.sh
```

The installer only symlinks the repo-local launcher. It does not copy compiler sources, runtime files, dependency caches, or shell configuration.

## Copied Alpha Layout

Build a copied Linux alpha layout with:

```bash
scripts/make_linux_release.sh
```

The layout is written to `build/linux-release/nauqtype/` and is documented in [LINUX_RELEASE_MANIFEST.md](LINUX_RELEASE_MANIFEST.md). Its public executable is `bin/nauqc`; the internal stage1 driver is `lib/nauqtype/nauqc-stage1`.

## Linux Alpha Gate

Run:

```bash
scripts/check_linux_alpha.sh
```

The gate rebuilds the stage1 driver with the frozen bootstrap, checks and runs a small example through `bin/nauqc`, runs the stage1-owned `prove` gate, creates the copied alpha layout, and smoke-tests that copied launcher.

## Not Distro-Ready Yet

Before Nauqtype is comfortable as a Linux distribution component, the project still needs:

- install ownership and filesystem placement for system-wide packaging
- bundled compiler strategy, if relying on host `cc` is not acceptable for a target distro
- packaging decisions for `.deb`, tarball, or source-first distro integration
