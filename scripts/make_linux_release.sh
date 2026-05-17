#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

driver="$repo_root/selfhost/build/nauqc"
if [[ ! -x "$driver" ]]; then
    printf 'make_linux_release: missing stage1 driver at %s\n' "$driver" >&2
    printf 'make_linux_release: run python3 -m compiler.main build selfhost/main.nq -o selfhost/build/nauqc\n' >&2
    exit 1
fi

release_root="$repo_root/build/linux-release/nauqtype"
rm -rf "$release_root"
mkdir -p "$release_root/bin"
mkdir -p "$release_root/lib/nauqtype/stdlib"
mkdir -p "$release_root/share/nauqtype"
mkdir -p "$release_root/share/doc/nauqtype"

cp "$repo_root/bin/nauqc" "$release_root/bin/nauqc"
cp "$driver" "$release_root/lib/nauqtype/nauqc-stage1"
cp "$repo_root/stdlib/runtime.h" "$release_root/lib/nauqtype/stdlib/runtime.h"
cp "$repo_root/stdlib/runtime.c" "$release_root/lib/nauqtype/stdlib/runtime.c"
cp -R "$repo_root/schemas" "$release_root/share/nauqtype/schemas"
mkdir -p "$release_root/share/nauqtype/examples"
while IFS= read -r example_file; do
    target="$release_root/share/nauqtype/$example_file"
    mkdir -p "$(dirname -- "$target")"
    cp "$repo_root/$example_file" "$target"
done < <(git ls-files 'examples/*')
cp "$repo_root/README.md" "$release_root/share/doc/nauqtype/README.md"
cp "$repo_root/LINUX.md" "$release_root/share/doc/nauqtype/LINUX.md"
cp "$repo_root/LINUX_RELEASE_MANIFEST.md" "$release_root/share/doc/nauqtype/LINUX_RELEASE_MANIFEST.md"

chmod +x "$release_root/bin/nauqc"
chmod +x "$release_root/lib/nauqtype/nauqc-stage1"

printf 'Created Linux release layout at %s\n' "$release_root"
