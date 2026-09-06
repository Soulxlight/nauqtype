#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

version="$(tr -d '[:space:]' < "$repo_root/VERSION")"
release_id="nauqtype-$version"
driver="$repo_root/selfhost/build/nauqc"
scripts/stage1_cache.sh require

identity_actual="$(mktemp)"
identity_expected="$(mktemp)"
trap 'rm -f "$identity_actual" "$identity_expected"' EXIT
printf 'nauqc %s\n' "$version" > "$identity_expected"
if ! (cd "$repo_root" && "$driver" version) > "$identity_actual"; then
    printf 'make_linux_release: stage1 version command failed\n' >&2
    exit 1
fi
if ! cmp -s "$identity_expected" "$identity_actual"; then
    printf 'make_linux_release: stage1 version identity does not match VERSION\n' >&2
    exit 1
fi
rm -f "$identity_actual" "$identity_expected"
trap - EXIT

release_root="$repo_root/build/linux-release/nauqtype"
rm -rf "$release_root"
mkdir -p "$release_root/bin"
mkdir -p "$release_root/lib/nauqtype/stdlib"
mkdir -p "$release_root/share/nauqtype"
mkdir -p "$release_root/share/doc/nauqtype"

cp "$repo_root/VERSION" "$release_root/share/nauqtype/VERSION"
cp "$repo_root/bin/nauqc" "$release_root/bin/nauqc"
cp "$driver" "$release_root/lib/nauqtype/nauqc-stage1"
cp "$repo_root/stdlib/runtime.h" "$release_root/lib/nauqtype/stdlib/runtime.h"
cp "$repo_root/stdlib/runtime.c" "$release_root/lib/nauqtype/stdlib/runtime.c"
mkdir -p "$release_root/share/nauqtype/schemas"
while IFS= read -r schema_file; do
    target="$release_root/share/nauqtype/$schema_file"
    mkdir -p "$(dirname -- "$target")"
    cp "$repo_root/$schema_file" "$target"
done < <(git ls-files 'schemas/*')
mkdir -p "$release_root/share/nauqtype/examples"
while IFS= read -r example_file; do
    target="$release_root/share/nauqtype/$example_file"
    mkdir -p "$(dirname -- "$target")"
    cp "$repo_root/$example_file" "$target"
done < <(git ls-files 'examples/*')
cp "$repo_root/README.md" "$release_root/share/doc/nauqtype/README.md"
cp "$repo_root/LINUX.md" "$release_root/share/doc/nauqtype/LINUX.md"
cp "$repo_root/LINUX_RELEASE_MANIFEST.md" "$release_root/share/doc/nauqtype/LINUX_RELEASE_MANIFEST.md"
cp "$repo_root/M55_CONTRACTS.md" "$release_root/share/doc/nauqtype/M55_CONTRACTS.md"

cat > "$release_root/share/nauqtype/release.json" <<JSON
{
  "version": "$version",
  "release_id": "$release_id",
  "layout": "linux-alpha-rc1",
  "public_driver": "bin/nauqc",
  "stage1_driver": "lib/nauqtype/nauqc-stage1",
  "stdlib": "lib/nauqtype/stdlib",
  "schemas": "share/nauqtype/schemas",
  "examples": "share/nauqtype/examples"
}
JSON

chmod +x "$release_root/bin/nauqc"
chmod +x "$release_root/lib/nauqtype/nauqc-stage1"

printf 'Created Linux release layout %s at %s\n' "$release_id" "$release_root"
