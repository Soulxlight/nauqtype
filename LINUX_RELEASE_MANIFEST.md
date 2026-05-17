# Nauqtype Linux Release Manifest

This is the M26 alpha release layout contract. It is a copied development artifact, not a distro package.

`scripts/make_linux_release.sh` creates:

- `build/linux-release/nauqtype/bin/nauqc`
- `build/linux-release/nauqtype/lib/nauqtype/nauqc-stage1`
- `build/linux-release/nauqtype/lib/nauqtype/stdlib/runtime.h`
- `build/linux-release/nauqtype/lib/nauqtype/stdlib/runtime.c`
- `build/linux-release/nauqtype/share/nauqtype/schemas/`
- `build/linux-release/nauqtype/share/nauqtype/examples/`
- `build/linux-release/nauqtype/share/doc/nauqtype/README.md`
- `build/linux-release/nauqtype/share/doc/nauqtype/LINUX.md`
- `build/linux-release/nauqtype/share/doc/nauqtype/LINUX_RELEASE_MANIFEST.md`

The launcher runs from `lib/nauqtype` so `build` and `run` can find `stdlib/runtime.c` without relying on a source checkout. The stage1 driver binary is named `nauqc-stage1`; the public executable remains `nauqc`.

Still out of scope:

- `.deb` packaging
- package-manager metadata
- shell completion
- system-wide install ownership
- bundled Zig or C compiler
