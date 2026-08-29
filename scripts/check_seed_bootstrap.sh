#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
work_dir="$(mktemp -d -t nauqtype-seed-proof-XXXXXX)"
trap 'rm -rf "$work_dir"' EXIT

seed_exe="$work_dir/nauqc-seed"
stage1_c="$work_dir/stage1.c"
stage1_exe="$work_dir/nauqc-stage1"
stage2_c="$work_dir/stage2.c"

"$repo_root/scripts/bootstrap_seed.sh" "$seed_exe" >/dev/null
(
    cd "$repo_root"
    "$seed_exe" emit-c selfhost/main.nq -o "$stage1_c"
)
"${CC:-cc}" -std=c11 -D_POSIX_C_SOURCE=200809L -I"$repo_root/bootstrap/seed" "$stage1_c" "$repo_root/bootstrap/seed/runtime.c" -o "$stage1_exe"
(
    cd "$repo_root"
    "$stage1_exe" emit-c selfhost/main.nq -o "$stage2_c"
    "$stage1_exe" prove-seed "$stage1_c" "$stage2_c"
)
printf 'seed bootstrap proof ok\n'
