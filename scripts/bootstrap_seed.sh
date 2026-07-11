#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
seed_dir="$repo_root/bootstrap/seed"
output_path="${1:-$repo_root/build/seed/nauqc-seed}"
cc_bin="${CC:-cc}"

if [[ ! -f "$seed_dir/nauqc-seed.c" || ! -f "$seed_dir/runtime.c" || ! -f "$seed_dir/runtime.h" ]]; then
    printf 'bootstrap_seed: checked-in seed artifacts are incomplete\n' >&2
    exit 1
fi

if [[ -f "$seed_dir/SHA256SUMS" ]]; then
    (
        cd "$repo_root"
        sha256sum -c bootstrap/seed/SHA256SUMS
    )
fi

mkdir -p "$(dirname -- "$output_path")"
"$cc_bin" -std=c11 -D_POSIX_C_SOURCE=200809L -I"$seed_dir" "$seed_dir/nauqc-seed.c" "$seed_dir/runtime.c" -o "$output_path"
printf '%s\n' "$output_path"
