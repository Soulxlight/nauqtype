#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
work_dir="$repo_root/build/seed"
seed_exe="$work_dir/nauqc-seed"
stage1_c="$work_dir/stage1.c"
stage1_exe="${1:-$repo_root/selfhost/build/nauqc}"
default_stage1_exe="$repo_root/selfhost/build/nauqc"

mkdir -p "$work_dir"
"$repo_root/scripts/bootstrap_seed.sh" "$seed_exe" >/dev/null
temp_build_dir="$(mktemp -d "$work_dir/.stage1-build.XXXXXX")"
temp_stage1_c="$temp_build_dir/stage1.c"
temp_stage1_exe="$temp_build_dir/nauqc"
mkdir -p "$(dirname -- "$stage1_exe")"
trap 'rm -rf "$temp_build_dir"' EXIT
(
    cd "$repo_root"
    "$seed_exe" emit-c selfhost/main.nq -o "$temp_stage1_c"
)
"${CC:-cc}" -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -I"$repo_root/bootstrap/seed" "$temp_stage1_c" "$repo_root/bootstrap/seed/runtime.c" -o "$temp_stage1_exe"
mv -f "$temp_stage1_c" "$stage1_c"
mv -f "$temp_stage1_exe" "$stage1_exe"
rm -rf "$temp_build_dir"
trap - EXIT
if [[ "$stage1_exe" == "$default_stage1_exe" ]]; then
    "$repo_root/scripts/stage1_cache.sh" record
fi
printf '%s\n' "$stage1_exe"
