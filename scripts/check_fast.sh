#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

usage() {
    cat <<'EOF'
Usage: scripts/check_fast.sh

Run the active Nauqtype-owned fixture and tooling confidence tier.

This command intentionally delegates to the stage1 driver. Historical Python
tests are no longer an active milestone or release gate. Copied-selfhost and
corpus proof claims remain owned by `nauqc prove` so composed gates do not run
them twice.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

if (( $# > 0 )); then
    printf 'check_fast: no Python unittest module arguments are accepted after M40\n' >&2
    exit 2
fi

if [[ ! -x selfhost/build/nauqc ]]; then
    scripts/build_stage1_from_seed.sh >/dev/null
fi
bin/nauqc test
