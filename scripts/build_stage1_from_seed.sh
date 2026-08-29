#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
work_dir="$repo_root/build/seed"
seed_exe="$work_dir/nauqc-seed"
stage1_c="$work_dir/stage1.c"
stage1_exe="${1:-$repo_root/selfhost/build/nauqc}"

mkdir -p "$work_dir"
"$repo_root/scripts/bootstrap_seed.sh" "$seed_exe" >/dev/null
(
    cd "$repo_root"
    "$seed_exe" emit-c selfhost/main.nq -o "$stage1_c"
)
mkdir -p "$(dirname -- "$stage1_exe")"
"${CC:-cc}" -std=c11 -D_POSIX_C_SOURCE=200809L -I"$repo_root/bootstrap/seed" "$stage1_c" "$repo_root/bootstrap/seed/runtime.c" -o "$stage1_exe"
printf '%s\n' "$stage1_exe"
