#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
work_dir="$(mktemp -d -t nauqtype-seed-proof-XXXXXX)"
trap 'rm -rf "$work_dir"' EXIT

usage() {
    cat <<'EOF'
Usage: scripts/check_seed_bootstrap.sh [--reuse-stage1]

Prove the seed-to-stage1 fixed point. With --reuse-stage1, consume the stage1 C
and executable freshly produced by scripts/build_stage1_from_seed.sh instead of
repeating the expensive seed emission.
EOF
}

reuse_stage1=false
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi
if [[ "${1:-}" == "--reuse-stage1" ]]; then
    reuse_stage1=true
    shift
fi
if (( $# > 0 )); then
    usage >&2
    exit 2
fi

seed_exe="$work_dir/nauqc-seed"
stage1_c="$work_dir/stage1.c"
stage1_exe="$work_dir/nauqc-stage1"
stage2_c="$work_dir/stage2.c"

if [[ "$reuse_stage1" == true ]]; then
    stage1_c="$repo_root/build/seed/stage1.c"
    stage1_exe="$repo_root/selfhost/build/nauqc"
    if [[ ! -s "$stage1_c" || ! -x "$stage1_exe" ]]; then
        printf 'reused stage1 artifacts are missing; run scripts/build_stage1_from_seed.sh first\n' >&2
        exit 1
    fi
else
    "$repo_root/scripts/bootstrap_seed.sh" "$seed_exe" >/dev/null
    (
        cd "$repo_root"
        "$seed_exe" emit-c selfhost/main.nq -o "$stage1_c"
    )
    "${CC:-cc}" -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -I"$repo_root/bootstrap/seed" "$stage1_c" "$repo_root/bootstrap/seed/runtime.c" -o "$stage1_exe"
fi
(
    cd "$repo_root"
    "$stage1_exe" emit-c selfhost/main.nq -o "$stage2_c"
    "$stage1_exe" prove-seed "$stage1_c" "$stage2_c"
)
printf 'seed bootstrap proof ok\n'
