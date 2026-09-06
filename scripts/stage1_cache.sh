#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
source "$script_dir/provenance.sh"
source "$script_dir/seed_manifest.sh"

cache_is_current() (
    local scratch key value current
    local -A cache=() receipt=() cc=()
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    seed_verify "$repo_root" || exit 1
    prov_read_record "$repo_root/build/seed/stage1-cache-v2.txt" stage1-cache/v2 "$scratch/cache" \
        inputs_sha256:hash derivation_sha256:hash stage1_c_sha256:hash stage1_exe_sha256:hash || exit 1
    prov_read_record "$repo_root/build/seed/stage1-derivation-v1.txt" stage1-derivation/v1 "$scratch/receipt" \
        inputs_sha256:hash seed_manifest_sha256:hash seed_exe_sha256:hash stage1_c_sha256:hash stage1_exe_sha256:hash \
        cc_path:path cc_sha256:hash cc_version_sha256:hash cc_target:atom flags_sha256:hash || exit 1
    while IFS='=' read -r key value; do cache[$key]=$value; done < "$scratch/cache"
    while IFS='=' read -r key value; do receipt[$key]=$value; done < "$scratch/receipt"
    # Execute toolchain identity probes before reading current inputs/artifacts.
    prov_cc_identity "${CC:-cc}" "$scratch/cc" || exit 1
    while IFS='=' read -r key value; do cc[$key]=$value; done < "$scratch/cc"
    for key in cc_path cc_sha256 cc_version_sha256 cc_target; do
        [[ "${cc[$key]}" == "${receipt[$key]}" ]] || exit 1
    done
    current=$(prov_sha256 "$scratch/receipt") || exit 1
    [[ "$current" == "${cache[derivation_sha256]}" ]] || exit 1
    current=$(prov_inputs_sha256 "$repo_root") || exit 1
    [[ "$current" == "${cache[inputs_sha256]}" && "$current" == "${receipt[inputs_sha256]}" ]] || exit 1
    current=$(prov_sha256 "$repo_root/bootstrap/seed/manifest.json") || exit 1
    [[ "$current" == "${receipt[seed_manifest_sha256]}" ]] || exit 1
    current=$(prov_sha256 "$repo_root/build/seed/nauqc-seed") || exit 1
    [[ "$current" == "${receipt[seed_exe_sha256]}" && -x "$repo_root/build/seed/nauqc-seed" ]] || exit 1
    current=$(prov_sha256 "$repo_root/build/seed/stage1.c") || exit 1
    [[ "$current" == "${cache[stage1_c_sha256]}" && "$current" == "${receipt[stage1_c_sha256]}" ]] || exit 1
    current=$(prov_sha256 "$repo_root/selfhost/build/nauqc") || exit 1
    [[ "$current" == "${cache[stage1_exe_sha256]}" && "$current" == "${receipt[stage1_exe_sha256]}" && -x "$repo_root/selfhost/build/nauqc" ]] || exit 1
    current=$(prov_bootstrap_flags_sha256) || exit 1
    [[ "$current" == "${receipt[flags_sha256]}" ]] || exit 1
)

usage() { printf 'Usage: scripts/stage1_cache.sh <fingerprint|check|require>\n'; }
(( $# == 1 )) || { usage >&2; exit 2; }
case "$1" in
    fingerprint) prov_inputs_sha256 "$repo_root";;
    check) cache_is_current >/dev/null 2>&1;;
    require)
        if ! cache_is_current; then
            printf 'stage1 artifacts are missing, stale, or modified; run scripts/build_stage1_from_seed.sh\n' >&2
            exit 1
        fi;;
    -h|--help) usage;;
    *) usage >&2; exit 2;;
esac
