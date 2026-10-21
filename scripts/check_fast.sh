#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

usage() {
    cat <<'EOF'
Usage: scripts/check_fast.sh [--suite <compiler-suite> | --host-suite provenance|attestation|budget]

Run the active Nauqtype-owned fixture and tooling confidence tier.

This command verifies the stage1 input/artifact cache and rebuilds stale
artifacts before delegating to the driver. Historical Python tests are no
longer an active milestone or release gate. Copied-selfhost and corpus proof
claims remain owned by `nauqc prove` so composed gates do not run them twice.

An explicit suite is partial feedback, not the complete confidence tier.
Compiler suites validate/rebuild the stage1 cache. Host suites run only the
named synthetic/unit fixture and do not validate a compiler.

Local fixture C reuse defaults to NQ_TEST_REUSE_C=1. Only verified compile
artifacts may be reused; all probes still execute. Set zero for fresh fixture
compiles. The complete milestone gate always forces zero.

NQ_FAST_CONCURRENT=1 explicitly opts into the local complete warm tier only.
It requires NQ_TEST_REUSE_C=1 and supported user-scope containment. Default
and zero remain serial; partial routes and fresh compiles reject concurrency.
Concurrent groups join all and replay combined output in fixed source order.
EOF
}

if (( $# == 1 )) && { [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; }; then
    usage
    exit 0
fi

case "${NQ_FAST_CONCURRENT-0}" in
    0|1) ;;
    *) printf 'check_fast: NQ_FAST_CONCURRENT must be 0 or 1\n' >&2; exit 2 ;;
esac
if [[ "${NQ_FAST_CONCURRENT-0}" == 1 ]] && (( $# != 0 )); then
    printf 'check_fast: concurrency requires the complete no-argument warm tier\n' >&2
    exit 2
fi
if [[ "${NQ_FAST_CONCURRENT-0}" == 1 && "${NQ_TEST_REUSE_C-1}" != 1 ]]; then
    printf 'check_fast: concurrency requires NQ_TEST_REUSE_C=1\n' >&2
    exit 2
fi

mode="full"
selection=""
if (( $# > 0 )); then
    if (( $# != 2 )) || { [[ "$1" != "--suite" ]] && [[ "$1" != "--host-suite" ]]; } || [[ -z "$2" ]]; then
        printf 'check_fast: expected exactly --suite <compiler-suite> or --host-suite provenance|attestation|budget\n' >&2
        exit 2
    fi
    mode=${1#--}
    selection=$2
    if [[ "$mode" == "suite" ]]; then
        case "$selection" in
            compiler-index|proof-artifacts|workspace-capture|workspace-evidence|integer-policy|allocation-policy|str-join|process-time|schema-profile|driver-fixtures|formatter) ;;
            *) printf 'check_fast: unknown compiler suite: %s\n' "$selection" >&2; exit 2 ;;
        esac
    else
        case "$selection" in
            provenance|attestation|budget) ;;
            *) printf 'check_fast: unknown host suite: %s\n' "$selection" >&2; exit 2 ;;
        esac
        printf 'check_fast: host-unit suite %s only; compiler/cache not checked\n' "$selection"
        case "$selection" in
            provenance)
                scripts/check_seed_capture.sh
                exec scripts/check_m54_10_provenance.sh ;;
            attestation)
                scripts/check_attestation_batch.sh
                exec scripts/check_m54_10_attestation.sh ;;
            budget) exec scripts/check_run_budgeted.sh ;;
        esac
    fi
fi

if [[ "$mode" != "full" && "$mode" != "suite" ]]; then
    printf 'check_fast: invalid selection\n' >&2
    exit 2
fi

case "${NQ_TEST_REUSE_C-1}" in
    0|1) export NQ_TEST_REUSE_C="${NQ_TEST_REUSE_C-1}" ;;
    *) printf 'check_fast: NQ_TEST_REUSE_C must be 0 or 1\n' >&2; exit 2 ;;
esac

_nqfc_release_tier_lock() {
    rmdir -- "$repo_root/build/verification/.check-fast-lock"
}
_nqfc_tier_exit() {
    set -- "$?"
    trap - EXIT
    printf 'check_fast: unverified tier completion; lock retained for inspection\n' >&2
    if [[ "$1" == 0 ]]; then set -- 125; fi
    exit "$1"
}
if [[ "$mode" == full ]]; then
    if [[ -L build || -L build/verification ]]; then
        printf 'check_fast: tier lock parents must not be symlinks\n' >&2
        exit 1
    fi
    mkdir -p -- build/verification
    if ! mkdir -- build/verification/.check-fast-lock; then
        printf 'check_fast: complete tier lock refused; no automatic stale-lock recovery\n' >&2
        exit 1
    fi
    trap _nqfc_tier_exit EXIT
fi

if ! scripts/stage1_cache.sh check; then
    printf 'check_fast: rebuilding stale stage1 artifacts\n' >&2
    scripts/build_stage1_from_seed.sh >/dev/null
fi
if [[ "$mode" == "suite" ]]; then
    bin/nauqc test --suite "$selection"
    exit $?
fi
if [[ "${NQ_FAST_CONCURRENT-0}" == 1 ]]; then
    source "$script_dir/fast_concurrent.sh"
    nq_fast_concurrent_run "$repo_root"
    exit $?
fi
bin/nauqc test
scripts/check_seed_capture.sh
scripts/check_m54_10_provenance.sh
scripts/check_attestation_batch.sh
scripts/check_m54_10_attestation.sh
scripts/check_run_budgeted.sh
_nqfc_release_tier_lock
trap - EXIT
