#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cache_version="stage1-cache/v1"
stage1_c="$repo_root/build/seed/stage1.c"
stage1_exe="$repo_root/selfhost/build/nauqc"
manifest="$repo_root/build/seed/stage1-cache-v1.txt"

usage() {
    cat <<'EOF'
Usage: scripts/stage1_cache.sh <fingerprint|record|check|require>

Track whether the default stage1 C and executable match every seed-to-stage1
input. `check` is quiet and returns nonzero for missing, stale, or modified
artifacts; `require` reports an actionable error for fail-closed reuse gates.
EOF
}

input_paths() {
    local selfhost_paths
    if ! selfhost_paths="$(
        cd "$repo_root"
        find selfhost -type f -name '*.nq' -print | LC_ALL=C sort
    )"; then
        printf 'stage1 cache could not enumerate selfhost inputs\n' >&2
        return 1
    fi
    if [[ -z "$selfhost_paths" ]]; then
        printf 'stage1 cache found no selfhost inputs\n' >&2
        return 1
    fi
    printf '%s\n' \
        VERSION \
        bootstrap/seed/SHA256SUMS \
        bootstrap/seed/manifest.json \
        bootstrap/seed/nauqc-seed.c \
        bootstrap/seed/runtime.c \
        bootstrap/seed/runtime.h \
        stdlib/runtime.c \
        stdlib/runtime.h \
        scripts/bootstrap_seed.sh \
        scripts/build_stage1_from_seed.sh \
        scripts/stage1_cache.sh
    printf '%s\n' "$selfhost_paths"
}

file_sha256() {
    sha256sum "$1" | awk '{print $1}'
}

input_fingerprint() {
    local relative
    local absolute
    local file_hash
    local paths
    paths="$(input_paths)" || return 1
    while IFS= read -r relative; do
        absolute="$repo_root/$relative"
        if [[ ! -f "$absolute" ]]; then
            printf 'stage1 cache input is missing: %s\n' "$relative" >&2
            return 1
        fi
        file_hash="$(file_sha256 "$absolute")" || return 1
        printf '%s\0%s\0' "$relative" "$file_hash"
    done <<< "$paths"
}

current_fingerprint() {
    local fingerprint
    if ! fingerprint="$(
        {
            printf '%s\0' "$cache_version"
            input_fingerprint
        } | sha256sum | awk '{print $1}'
    )"; then
        return 1
    fi
    [[ "$fingerprint" =~ ^[0-9a-f]{64}$ ]] || return 1
    printf '%s\n' "$fingerprint"
}

manifest_field() {
    local field="$1"
    sed -n "s/^${field}=//p" "$manifest"
}

cache_is_current() {
    [[ -s "$stage1_c" && -x "$stage1_exe" && -f "$manifest" ]] || return 1
    [[ "$(sed -n '1p' "$manifest")" == "$cache_version" ]] || return 1

    local expected_inputs
    local expected_c
    local expected_exe
    local actual_inputs
    local actual_c
    local actual_exe
    expected_inputs="$(manifest_field inputs_sha256)"
    expected_c="$(manifest_field stage1_c_sha256)"
    expected_exe="$(manifest_field stage1_exe_sha256)"
    [[ "$expected_inputs" =~ ^[0-9a-f]{64}$ ]] || return 1
    [[ "$expected_c" =~ ^[0-9a-f]{64}$ ]] || return 1
    [[ "$expected_exe" =~ ^[0-9a-f]{64}$ ]] || return 1
    actual_inputs="$(current_fingerprint)" || return 1
    actual_c="$(file_sha256 "$stage1_c")" || return 1
    actual_exe="$(file_sha256 "$stage1_exe")" || return 1
    [[ "$expected_inputs" == "$actual_inputs" ]] || return 1
    [[ "$expected_c" == "$actual_c" ]] || return 1
    [[ "$expected_exe" == "$actual_exe" ]] || return 1
}

record_cache() {
    if [[ ! -s "$stage1_c" || ! -x "$stage1_exe" ]]; then
        printf 'stage1 cache cannot record incomplete artifacts\n' >&2
        return 1
    fi
    local inputs_hash
    local c_hash
    local exe_hash
    inputs_hash="$(current_fingerprint)" || return 1
    c_hash="$(file_sha256 "$stage1_c")" || return 1
    exe_hash="$(file_sha256 "$stage1_exe")" || return 1
    mkdir -p "$(dirname -- "$manifest")"
    local temp_manifest
    temp_manifest="$(mktemp "${manifest}.tmp.XXXXXX")"
    trap 'rm -f "$temp_manifest"' RETURN
    {
        printf '%s\n' "$cache_version"
        printf 'inputs_sha256=%s\n' "$inputs_hash"
        printf 'stage1_c_sha256=%s\n' "$c_hash"
        printf 'stage1_exe_sha256=%s\n' "$exe_hash"
    } > "$temp_manifest"
    mv -f "$temp_manifest" "$manifest"
    trap - RETURN
}

command="${1:-}"
case "$command" in
    fingerprint)
        current_fingerprint
        ;;
    record)
        record_cache
        ;;
    check)
        cache_is_current
        ;;
    require)
        if ! cache_is_current; then
            printf 'stage1 artifacts are missing, stale, or modified; run scripts/build_stage1_from_seed.sh\n' >&2
            exit 1
        fi
        ;;
    --help|-h)
        usage
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac
