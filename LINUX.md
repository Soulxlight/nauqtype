# Nauqtype Linux Alpha

Nauqtype is ready for Linux alpha development from this repository checkout. It is not yet a distro package or system compiler.

## Current Contract

- The active compiler driver is the self-hosted stage1 binary at `selfhost/build/main.exe`.
- The repo-local Linux launcher is `bin/nauqc`.
- `bin/nauqc` runs the stage1 driver from the repository root so `stdlib/runtime.c`, `.deps/ziglang/zig`, and the Linux `cc` fallback are found consistently.
- Source and output paths passed through `bin/nauqc` are normalized from the caller's current directory before the stage1 driver runs.
- `scripts/install_nauqtype.sh` installs a symlink to the launcher, defaulting to `$HOME/.local/bin/nauqc`.

## Bootstrap

From the repository root:

```bash
python3 scripts/setup_deps.py
python3 -m compiler.main run selfhost/main.nq
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

## Linux Alpha Gate

Run:

```bash
scripts/check_linux_alpha.sh
```

The gate rebuilds the stage1 driver with the frozen bootstrap, checks and runs a small example through `bin/nauqc`, and runs the stage1-owned `prove` gate.

## Not Distro-Ready Yet

Before Nauqtype is comfortable as a Linux distribution component, the project still needs:

- a copied install layout instead of a symlink into a development checkout
- a stable public binary name without the historical `main.exe` artifact leaking into user docs
- a release manifest for runtime files, schemas, examples, and docs
- a Linux CI/release gate that runs outside one local checkout
- packaging decisions for `.deb`, tarball, or source-first distro integration
