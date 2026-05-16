#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
prefix="${PREFIX:-$HOME/.local}"
bindir="$prefix/bin"
launcher="$repo_root/bin/nauqc"
target="$bindir/nauqc"

if [[ ! -x "$launcher" ]]; then
    printf 'install_nauqtype: missing executable launcher at %s\n' "$launcher" >&2
    exit 1
fi

mkdir -p "$bindir"
ln -sf "$launcher" "$target"

printf 'Installed nauqc launcher: %s -> %s\n' "$target" "$launcher"
printf 'If needed, add this to PATH: export PATH="%s:$PATH"\n' "$bindir"
