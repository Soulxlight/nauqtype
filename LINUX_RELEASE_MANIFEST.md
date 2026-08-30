# Nauqtype Linux Release Manifest

This is the M30 Linux Alpha RC1 release layout contract, reused by M46's v0.3 organizational-alpha proof. It is a copied development artifact, not a distro package.

The repository version is stored in `VERSION`. The stage1 compiler owns its `help` and `version` behavior, and release assembly fails if the compiled `nauqc <version>` identity differs from `VERSION`. The copied layout carries the same version in `share/nauqtype/VERSION` and a deterministic release identity in `share/nauqtype/release.json`.

`scripts/make_linux_release.sh` creates:

- `build/linux-release/nauqtype/bin/nauqc`
- `build/linux-release/nauqtype/lib/nauqtype/nauqc-stage1`
- `build/linux-release/nauqtype/lib/nauqtype/stdlib/runtime.h`
- `build/linux-release/nauqtype/lib/nauqtype/stdlib/runtime.c`
- `build/linux-release/nauqtype/share/nauqtype/VERSION`
- `build/linux-release/nauqtype/share/nauqtype/release.json`
- `build/linux-release/nauqtype/share/nauqtype/schemas/`
- `build/linux-release/nauqtype/share/nauqtype/examples/` with tracked example source files only
- `build/linux-release/nauqtype/share/doc/nauqtype/README.md`
- `build/linux-release/nauqtype/share/doc/nauqtype/LINUX.md`
- `build/linux-release/nauqtype/share/doc/nauqtype/LINUX_RELEASE_MANIFEST.md`

The launcher runs from `lib/nauqtype` so `build` and `run` can find `stdlib/runtime.c` without relying on a source checkout. The stage1 driver binary is named `nauqc-stage1`; the public executable remains `nauqc`.

Generated artifacts under `examples/build/` and copied executable outputs such as `*.exe` are intentionally excluded from the release layout.

`scripts/verify_linux_release.sh` validates the copied layout against this manifest. It also checks all public help/version aliases against locked goldens, checks the copied stage1 executable directly, and confirms the version golden still matches repository `VERSION`. `scripts/check_linux_alpha.sh` also copies the generated layout into a temporary directory and runs `nauqc check` / `nauqc run` from a separate project directory, so the alpha gate proves the copied launcher works outside the source checkout root. `scripts/check_organizational_alpha.sh` extends that check with the locked two-workspace organizational tool, its facts v3 snapshot, policy sidecar, and checked cross-workspace impact report.

Still out of scope:

- `.deb` packaging
- package-manager metadata
- shell completion
- system-wide install ownership
- bundled Zig or C compiler
