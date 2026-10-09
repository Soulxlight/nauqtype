#!/usr/bin/env bash
# Capture a bounded non-instrumented selfhost baseline; this is not a proof gate.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
source "$script_dir/provenance.sh"
source "$script_dir/performance_budgets.sh"

usage() {
    cat <<'EOF'
Usage: scripts/profile_selfhost.sh [--preflight]

Record two serial, non-instrumented baseline runs of:
  selfhost/build/nauqc check selfhost/main.nq

The default Linux-only mode verifies (but never builds or blesses) the current
stage1 cache, captures the measured inputs, and writes a new directory under
build/verification/performance-baseline/. It is neither an optimization claim
nor a replacement for a proof or release gate.

--preflight  Read-only check for Linux, GNU time/timeout, production CC, host
             inventory prerequisites, and the current stage1 cache.
EOF
}

profile_error() { printf 'profile_selfhost: %s\n' "$*" >&2; }
profile_linux_host_ok() { [[ "$(uname -s)" == Linux && -r /proc/version && "$(< /proc/version)" == *Linux* ]]; }
profile_host_cpu_available() { command -v lscpu >/dev/null 2>&1 || [[ -r /proc/cpuinfo ]]; }
profile_gnu_tools_ok() {
    [[ -x /usr/bin/time && "$(/usr/bin/time --version 2>/dev/null | sed -n '1p')" == *"GNU Time"* ]] || return 1
    command -v timeout >/dev/null 2>&1 && [[ "$(timeout --version 2>/dev/null | sed -n '1p')" == *"GNU coreutils"* ]]
}
profile_cc_available() {
    local path
    path=$(command -v -- "${CC:-cc}" 2>/dev/null || true)
    [[ -n "$path" ]] && path=$(realpath -e -- "$path") && [[ -x "$path" ]] && "$path" --version >/dev/null && "$path" -dumpmachine >/dev/null
}

profile_fs_probe() {
    local path=$1 fs_type magic device
    command -v findmnt >/dev/null 2>&1 || return 1
    fs_type=$(findmnt --noheadings --output FSTYPE --target "$path") || return 1
    magic=$(stat -f -c %t -- "$path") || return 1
    device=$(stat -c %d -- "$path") || return 1
    printf '%s %s %s\n' "$fs_type" "$magic" "$device"
}
profile_native_fs_identity() {
    local path probe fs_type magic device
    path=$(realpath -e -- "$1") || return 1
    [[ -d "$path" ]] || return 1
    probe=$(profile_fs_probe "$path") || return 1
    [[ "$probe" =~ ^ext4[[:space:]]ef53[[:space:]][0-9]+$ ]] || return 1
    read -r fs_type magic device <<< "$probe"
    printf 'profile-selfhost-filesystem/v1\npath=%s\nfs_type=%s\nfs_magic=%s\ndevice=%s\n' "$path" "$fs_type" "$magic" "$device"
}

profile_read_cache_records() {
    local target=$1
    mkdir -p -- "$target" || return 1
    prov_read_record "$repo_root/build/seed/stage1-cache-v2.txt" stage1-cache/v2 "$target/cache.txt" \
        inputs_sha256:hash derivation_sha256:hash stage1_c_sha256:hash stage1_exe_sha256:hash || return 1
    prov_read_record "$repo_root/build/seed/stage1-derivation-v1.txt" stage1-derivation/v1 "$target/receipt.txt" \
        inputs_sha256:hash seed_manifest_sha256:hash seed_exe_sha256:hash stage1_c_sha256:hash stage1_exe_sha256:hash \
        cc_path:path cc_sha256:hash cc_version_sha256:hash cc_target:atom flags_sha256:hash
}
profile_record_value() { sed -n "s/^$2=//p" "$1"; }
profile_cache_matches() (
    local pin=$1 cache="$1/cache.txt" receipt="$1/receipt.txt" scratch key expected actual
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    profile_read_cache_records "$scratch/current" || exit 1
    cmp -s "$cache" "$scratch/current/cache.txt" && cmp -s "$receipt" "$scratch/current/receipt.txt" || exit 1
    actual=$(profile_require_digest "$receipt") || exit 1
    expected=$(profile_record_value "$cache" derivation_sha256) || exit 1
    [[ "$actual" == "$expected" ]] || exit 1
    for key in inputs_sha256 stage1_c_sha256; do
        [[ "$(profile_record_value "$cache" "$key")" == "$(profile_record_value "$receipt" "$key")" ]] || exit 1
    done
    [[ "$(profile_record_value "$cache" stage1_exe_sha256)" == "$(profile_record_value "$receipt" stage1_exe_sha256)" ]] || exit 1
    actual=$(prov_inputs_sha256 "$repo_root") || exit 1
    [[ "$actual" == "$(profile_record_value "$receipt" inputs_sha256)" ]] || exit 1
    for key in seed_manifest_sha256 seed_exe_sha256 stage1_c_sha256 stage1_exe_sha256; do
        case "$key" in
            seed_manifest_sha256) expected="$repo_root/bootstrap/seed/manifest.json";;
            seed_exe_sha256) expected="$repo_root/build/seed/nauqc-seed";;
            stage1_c_sha256) expected="$repo_root/build/seed/stage1.c";;
            stage1_exe_sha256) expected="$repo_root/selfhost/build/nauqc";;
        esac
        actual=$(profile_require_digest "$expected") || exit 1
        [[ "$actual" == "$(profile_record_value "$receipt" "$key")" ]] || exit 1
    done
    [[ -x "$repo_root/build/seed/nauqc-seed" && -x "$repo_root/selfhost/build/nauqc" ]] || exit 1
    actual=$(prov_bootstrap_flags_sha256) || exit 1
    prov_hex "$actual" && [[ "$actual" == "$(profile_record_value "$receipt" flags_sha256)" ]] || exit 1
    prov_cc_identity "${CC:-cc}" "$scratch/cc" || exit 1
    for key in cc_path cc_sha256 cc_version_sha256 cc_target; do
        [[ "$(profile_record_value "$scratch/cc" "$key")" == "$(profile_record_value "$receipt" "$key")" ]] || exit 1
    done
)

profile_identity_matches_pin() {
    local identity=$1 pin=$2 copied_runner_hash=$3 key expected
    for key in inputs_sha256 seed_manifest_sha256 seed_exe_sha256 stage1_c_sha256 bootstrap_flags_sha256 driver_sha256 derivation_sha256; do
        case "$key" in
            bootstrap_flags_sha256) expected=$(profile_record_value "$pin/receipt.txt" flags_sha256);;
            driver_sha256) expected=$(profile_record_value "$pin/receipt.txt" stage1_exe_sha256);;
            derivation_sha256) expected=$(profile_require_digest "$pin/receipt.txt") || return 1;;
            *) expected=$(profile_record_value "$pin/receipt.txt" "$key");;
        esac
        [[ -n "$expected" ]] && grep -Fqx -- "$key=$expected" "$identity" || return 1
    done
    for key in cc_path cc_sha256 cc_version_sha256 cc_target; do
        expected=$(profile_record_value "$pin/receipt.txt" "$key")
        [[ -n "$expected" ]] && grep -Fqx -- "$key=$expected" "$identity" || return 1
    done
    [[ "$copied_runner_hash" =~ ^[0-9a-f]{64}$ ]] &&
        grep -Fqx -- "copied_runner_sha256=$copied_runner_hash" "$identity"
}

profile_preflight() (
    local pin=${1:-} failed=0 budget scratch fs_before fs_after
    profile_linux_host_ok || { profile_error 'Linux (for example the configured WSL2 distro after reboot) is required'; failed=1; }
    profile_native_fs_identity "$repo_root" >/dev/null || { profile_error 'checkout must be on a verified native ext4 filesystem'; failed=1; }
    profile_gnu_tools_ok || { profile_error 'GNU /usr/bin/time and GNU timeout are required'; failed=1; }
    command -v sha256sum >/dev/null 2>&1 && command -v realpath >/dev/null 2>&1 && command -v awk >/dev/null 2>&1 || { profile_error 'provenance tools are required'; failed=1; }
    budget=$(performance_budget_for stage1.driver) || { profile_error 'the stage1.driver performance budget is unavailable'; failed=1; }
    profile_cc_available || { profile_error 'the configured production CC cannot answer identity probes'; failed=1; }
    profile_host_cpu_available || { profile_error 'lscpu or readable /proc/cpuinfo is required'; failed=1; }
    (( failed == 0 )) || exit 1
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    profile_read_cache_records "$scratch/before" || { profile_error 'stage1 cache records are missing or malformed'; exit 1; }
    "$script_dir/stage1_cache.sh" check || { profile_error 'stage1 cache is missing, stale, or modified; build it separately'; exit 1; }
    profile_read_cache_records "$scratch/after" || exit 1
    cmp -s "$scratch/before/cache.txt" "$scratch/after/cache.txt" && cmp -s "$scratch/before/receipt.txt" "$scratch/after/receipt.txt" || { profile_error 'stage1 cache changed during preflight'; exit 1; }
    profile_cache_matches "$scratch/before" || { profile_error 'stage1 cache inputs changed after validation'; exit 1; }
    if [[ -n "$pin" ]]; then
        mkdir -p -- "$pin" || exit 1
        cp -- "$scratch/before/cache.txt" "$pin/cache.txt" || exit 1
        cp -- "$scratch/before/receipt.txt" "$pin/receipt.txt" || exit 1
    fi
)

profile_require_digest() {
    local digest
    digest=$(prov_sha256 "$1") || return 1
    prov_hex "$digest" || return 1
    printf '%s\n' "$digest"
}
profile_check_copied_runner() {
    local actual
    actual=$(profile_require_digest "$1") || return 1
    [[ "$actual" == "$2" ]]
}
profile_runner_identity_record() {
    local actual
    actual=$(profile_require_digest "$1") || return 1
    [[ "$actual" == "$2" ]] || return 1
    printf 'copied_runner_sha256=%s\n' "$actual"
}

profile_now_ns() {
    local now
    now=$(date +%s%N) || return 1
    [[ "$now" =~ ^[0-9]{19}$ ]] || return 1
    printf '%s\n' "$now"
}
profile_elapsed_ns() {
    [[ "$1" =~ ^[0-9]{19}$ && "$2" =~ ^[0-9]{19}$ ]] || return 1
    (( $2 >= $1 )) || return 1
    printf '%s\n' "$(($2 - $1))"
}
profile_snapshot_bytes() {
    local root=$1 paths=$2 path size total=0
    while IFS= read -r path; do
        [[ -n "$path" ]] || continue
        size=$(stat -c %s -- "$root/$path") || return 1
        [[ "$size" =~ ^[0-9]+$ ]] || return 1
        total=$((total + size))
    done < "$paths"
    printf '%s\n' "$total"
}
profile_append_workflow_time() {
    local summary=$1 elapsed_ns=$2 tmp
    tmp=$(mktemp "${summary%/*}/.summary-final.XXXXXX") || return 1
    profile_summary_costs_valid "$summary" --partial || { rm -f -- "$tmp"; return 1; }
    awk -v ns="$elapsed_ns" '
        /^}$/ {
            printf "  \"total_workflow_ns\": %s,\n", ns
            printf "  \"total_workflow_seconds\": %.9f,\n", ns / 1000000000
            print "  \"workflow_includes_cleanup\": true"
            print "}"
            next
        }
        { print }
    ' "$summary" > "$tmp" && profile_summary_costs_valid "$tmp" && profile_summary_json_shape_valid "$tmp" && mv -- "$tmp" "$summary" || { rm -f -- "$tmp"; return 1; }
}
profile_summary_costs_valid() {
    local summary=$1 mode=${2:-complete} key
    local keys=(setup_ns source_capture_ns source_capture_bytes pre_measurement_copy_ns pre_measurement_copy_bytes pre_run_hash_validation_ns post_run_hash_validation_ns)
    if [[ "$mode" != --partial ]]; then keys+=(total_workflow_ns total_workflow_seconds); fi
    for key in "${keys[@]}"; do
        if [[ "$key" == total_workflow_seconds ]]; then
            grep -Eq "^  \"$key\": [0-9]+([.][0-9]{9})?,$" "$summary" || return 1
        else
            grep -Eq "^  \"$key\": [0-9]+,$" "$summary" || return 1
        fi
    done
    [[ "$mode" == --partial ]] || grep -Fqx '  "workflow_includes_cleanup": true' "$summary"
}
profile_summary_json_shape_valid() {
    local summary=$1
    [[ "$(sed -n '1p' "$summary")" == '{' && "$(tail -n 1 "$summary")" == '}' ]] || return 1
    grep -Fqx '  "version": 2,' "$summary" &&
        grep -Eq '^  "runs": \[.*\],$' "$summary" &&
        grep -Eq '^  "total_workflow_ns": [0-9]+,$' "$summary" &&
        grep -Eq '^  "total_workflow_seconds": [0-9]+([.][0-9]{9})?,$' "$summary" &&
        grep -Fqx '  "workflow_includes_cleanup": true' "$summary" || return 1
    awk '
        /^  "/ {
            if ($0 ~ /"workflow_includes_cleanup": true$/) { cleanup=NR; next }
            if ($0 !~ /,$/) exit 1
        }
        END { if (cleanup != NR-1) exit 1 }
    ' "$summary"
}

profile_write_identity() (
    local output=$1 copied_runner=$2 expected_runner_hash=$3 scratch tmp head inputs seed_manifest seed_c seed_exe stage1_c driver flags derivation path digest copied_runner_hash copied_runner_record
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    head=$(git -C "$repo_root" rev-parse --verify HEAD) || exit 1
    [[ "$head" =~ ^[0-9a-f]{40}$ ]] || exit 1
    inputs=$(prov_inputs_sha256 "$repo_root") || exit 1; prov_hex "$inputs" || exit 1
    seed_manifest=$(profile_require_digest "$repo_root/bootstrap/seed/manifest.json") || exit 1
    seed_c=$(profile_require_digest "$repo_root/bootstrap/seed/nauqc-seed.c") || exit 1
    seed_exe=$(profile_require_digest "$repo_root/build/seed/nauqc-seed") || exit 1
    stage1_c=$(profile_require_digest "$repo_root/build/seed/stage1.c") || exit 1
    driver=$(profile_require_digest "$repo_root/selfhost/build/nauqc") || exit 1
    flags=$(prov_bootstrap_flags_sha256) || exit 1; prov_hex "$flags" || exit 1
    derivation=$(profile_require_digest "$repo_root/build/seed/stage1-derivation-v1.txt") || exit 1
    copied_runner_record=$(profile_runner_identity_record "$copied_runner" "$expected_runner_hash") || exit 1
    copied_runner_hash=${copied_runner_record#copied_runner_sha256=}
    prov_cc_identity "${CC:-cc}" "$scratch/cc" || exit 1
    tmp=$(mktemp "${output%/*}/.identity.XXXXXX") || exit 1
    {
        printf 'profile-selfhost-identity/v2\ngit_head=%s\ninputs_sha256=%s\nseed_manifest_sha256=%s\nseed_c_sha256=%s\nseed_exe_sha256=%s\nstage1_c_sha256=%s\ndriver_sha256=%s\ncopied_runner_sha256=%s\nbootstrap_flags_sha256=%s\nderivation_sha256=%s\n' "$head" "$inputs" "$seed_manifest" "$seed_c" "$seed_exe" "$stage1_c" "$driver" "$copied_runner_hash" "$flags" "$derivation"
        for path in profile_selfhost.sh provenance.sh stage1_cache.sh performance_budgets.sh run_budgeted.sh; do
            digest=$(profile_require_digest "$script_dir/$path") || exit 1
            printf '%s_sha256=%s\n' "${path%.sh}" "$digest"
        done
        cat "$scratch/cc"
    } > "$tmp" || { rm -f -- "$tmp"; exit 1; }
    mv -- "$tmp" "$output"
)

profile_read_budget_result() {
    local path=$1 status failure exit_code wall rss
    [[ -f "$path" ]] || return 1
    status=$(sed -n 's/^  "status": "\([a-z]*\)",$/\1/p' "$path"); failure=$(sed -n 's/^  "failure": "\([a-z_]*\)",$/\1/p' "$path")
    exit_code=$(sed -n 's/^  "command_exit_code": \(-\{0,1\}[0-9]*\),$/\1/p' "$path"); wall=$(sed -n 's/^  "wall_seconds": \([0-9.]*\),$/\1/p' "$path"); rss=$(sed -n 's/^  "peak_rss_kib": \([0-9]*\),$/\1/p' "$path")
    [[ "$status" =~ ^(ok|failed)$ && "$failure" =~ ^(none|wall_time|command|peak_rss)$ && "$exit_code" =~ ^-?[0-9]+$ && "$wall" =~ ^[0-9]+([.][0-9]+)?$ && "$rss" =~ ^[0-9]+$ ]] || return 1
    awk -v wall="$wall" -v rss="$rss" 'BEGIN { exit (wall > 0 && rss > 0) ? 0 : 1 }' || return 1
    printf '%s %s %s %s %s\n' "$status" "$failure" "$exit_code" "$wall" "$rss"
}
profile_budget_result_ok() {
    local status failure exit_code wall rss result
    result=$(profile_read_budget_result "$1") || return 1
    read -r status failure exit_code wall rss <<< "$result"
    [[ "$status" == ok && "$failure" == none && "$exit_code" == 0 ]]
}
profile_relative_spread_pass() {
    local first=$1 second=$2 low high
    [[ "$first" =~ ^[0-9]+([.][0-9]+)?$ && "$second" =~ ^[0-9]+([.][0-9]+)?$ ]] || return 1
    low=$(awk -v a="$first" -v b="$second" 'BEGIN { print (a < b ? a : b) }'); high=$(awk -v a="$first" -v b="$second" 'BEGIN { print (a > b ? a : b) }')
    awk -v low="$low" -v high="$high" 'BEGIN { exit (low > 0 && (high-low)/low <= .10) ? 0 : 1 }'
}
profile_spread() { awk -v a="$1" -v b="$2" 'BEGIN { low=(a < b ? a : b); high=(a > b ? a : b); printf "%.6f", (high-low)/low }'; }
profile_write_command() { local output=$1; shift; printf '%q ' "$@" > "$output"; printf '\n' >> "$output"; }
profile_record_host() { { printf 'host-profile/v1\n'; uname -a; if command -v lscpu >/dev/null 2>&1; then lscpu || cat /proc/cpuinfo; else cat /proc/cpuinfo; fi; } > "$1"; }
profile_write_stage1_flags() (
    local output=$1 arg flags scratch
    flags=$(prov_bootstrap_flags_sha256) || exit 1
    prov_hex "$flags" || exit 1
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    prov_stage1_args > "$scratch" || exit 1
    {
        printf 'profile-selfhost-stage1-flags/v1\n'
        while IFS= read -r -d '' arg; do printf '%q\n' "$arg"; done < "$scratch"
        printf 'bootstrap_flags_sha256=%s\n' "$flags"
    } > "$output"
)
profile_verify_snapshot() {
    local root=$1 inputs_hash=$2 driver_hash=$3 current
    current=$(prov_inputs_sha256 "$root") || return 1; [[ "$current" == "$inputs_hash" ]] || return 1
    current=$(profile_require_digest "$root/selfhost/build/nauqc") || return 1; [[ "$current" == "$driver_hash" ]]
}

profile_result_dir=""; profile_pin_dir=""; profile_active=setup; profile_success=false
profile_workflow_start_ns= profile_setup_ns= profile_source_capture_ns= profile_pre_copy_ns= profile_pre_copy_bytes= profile_pre_hash_validation_ns= profile_post_hash_validation_ns=
profile_on_exit() {
    local code=$? finished_ns elapsed_ns
    if [[ -n "$profile_pin_dir" ]]; then rm -rf -- "$profile_pin_dir"; fi
    if [[ -n "$profile_result_dir" && "$profile_success" == true ]]; then
        finished_ns=$(profile_now_ns) || code=1
        if (( code == 0 )); then elapsed_ns=$(profile_elapsed_ns "$profile_workflow_start_ns" "$finished_ns") || code=1; fi
        if (( code == 0 )); then profile_append_workflow_time "$profile_result_dir/summary.pending.json" "$elapsed_ns" || code=1; fi
        if (( code == 0 )); then mv -- "$profile_result_dir/summary.pending.json" "$profile_result_dir/summary.json" || code=1; fi
        if (( code != 0 )); then
            rm -f -- "$profile_result_dir/summary.json" "$profile_result_dir/summary.pending.json"
            printf 'profile-selfhost failure\nactive=summary finalization\nexit_code=%s\n' "$code" > "$profile_result_dir/failure.txt"
            profile_error "failed during summary finalization; logs retained in $profile_result_dir"
            exit "$code"
        fi
        printf 'selfhost baseline recorded: %s\n' "$profile_result_dir"
    elif [[ -n "$profile_result_dir" ]]; then
        rm -f -- "$profile_result_dir/summary.json" "$profile_result_dir/summary.pending.json"
        printf 'profile-selfhost failure\nactive=%s\nexit_code=%s\n' "$profile_active" "$code" > "$profile_result_dir/failure.txt"
        profile_error "failed during $profile_active; logs retained in $profile_result_dir"
    fi
}

profile_baseline() {
    local wall_limit rss_limit budget input_hash driver_hash runner_hash flags_record_hash run exit_code status failure ignored wall_one wall_two rss_one rss_two wall_spread rss_spread snapshot summary_tmp first second now_ns setup_start_ns capture_start_ns copy_start_ns hash_start_ns source_capture_bytes driver_bytes runner_bytes
    profile_workflow_start_ns=$(profile_now_ns) || return 1
    setup_start_ns=$profile_workflow_start_ns
    profile_pin_dir=$(mktemp -d) || return 1
    trap profile_on_exit EXIT
    profile_preflight "$profile_pin_dir" || return 1
    budget=$(performance_budget_for stage1.driver) || return 1
    read -r wall_limit rss_limit <<< "$budget"
    mkdir -p -- "$repo_root/build/verification/performance-baseline"
    profile_result_dir=$(mktemp -d "$repo_root/build/verification/performance-baseline/selfhost-baseline-$(date -u +%Y%m%dT%H%M%SZ).XXXXXX")
    profile_active='input snapshot'; snapshot="$profile_result_dir/inputs"
    cp -- "$profile_pin_dir/cache.txt" "$profile_result_dir/stage1-cache-v2.txt" || return 1
    cp -- "$profile_pin_dir/receipt.txt" "$profile_result_dir/stage1-derivation-v1.txt" || return 1
    cmp -s "$profile_pin_dir/cache.txt" "$profile_result_dir/stage1-cache-v2.txt" && cmp -s "$profile_pin_dir/receipt.txt" "$profile_result_dir/stage1-derivation-v1.txt" || return 1
    profile_native_fs_identity "$repo_root" > "$profile_result_dir/checkout-filesystem.txt" || { profile_error 'checkout filesystem changed after preflight'; return 1; }
    profile_cache_matches "$profile_pin_dir" || { profile_error 'stage1 identity changed after preflight'; return 1; }
    prov_input_paths "$repo_root" > "$profile_result_dir/input-paths.txt" || return 1
    input_hash=$(profile_record_value "$profile_pin_dir/receipt.txt" inputs_sha256)
    driver_hash=$(profile_record_value "$profile_pin_dir/receipt.txt" stage1_exe_sha256)
    runner_hash=$(profile_require_digest "$script_dir/run_budgeted.sh") || return 1
    profile_cache_matches "$profile_pin_dir" || { profile_error 'stage1 identity changed before capture'; return 1; }
    now_ns=$(profile_now_ns) || return 1
    profile_setup_ns=$(profile_elapsed_ns "$setup_start_ns" "$now_ns") || return 1
    capture_start_ns=$now_ns
    prov_capture_inputs "$repo_root" "$snapshot" "$profile_result_dir/input-paths.txt" "$input_hash" || return 1
    now_ns=$(profile_now_ns) || return 1
    profile_source_capture_ns=$(profile_elapsed_ns "$capture_start_ns" "$now_ns") || return 1
    source_capture_bytes=$(profile_snapshot_bytes "$snapshot" "$profile_result_dir/input-paths.txt") || return 1
    mkdir -p -- "$snapshot/selfhost/build" "$profile_result_dir/tools"
    profile_native_fs_identity "$snapshot" > "$profile_result_dir/snapshot-filesystem.txt" || { profile_error 'snapshot must be on a verified native ext4 filesystem'; return 1; }
    first=$(profile_record_value "$profile_result_dir/checkout-filesystem.txt" device)
    second=$(profile_record_value "$profile_result_dir/snapshot-filesystem.txt" device)
    [[ -n "$first" && "$first" == "$second" ]] || { profile_error 'snapshot and checkout are on different filesystems'; return 1; }
    copy_start_ns=$(profile_now_ns) || return 1
    cp --preserve=mode -- "$repo_root/selfhost/build/nauqc" "$snapshot/selfhost/build/nauqc" || return 1
    cp --preserve=mode -- "$script_dir/run_budgeted.sh" "$profile_result_dir/tools/run_budgeted.sh" || return 1
    now_ns=$(profile_now_ns) || return 1
    profile_pre_copy_ns=$(profile_elapsed_ns "$copy_start_ns" "$now_ns") || return 1
    driver_bytes=$(stat -c %s -- "$snapshot/selfhost/build/nauqc") || return 1
    runner_bytes=$(stat -c %s -- "$profile_result_dir/tools/run_budgeted.sh") || return 1
    profile_pre_copy_bytes=$((driver_bytes + runner_bytes))
    hash_start_ns=$(profile_now_ns) || return 1
    profile_check_copied_runner "$profile_result_dir/tools/run_budgeted.sh" "$runner_hash" || { profile_error 'copied budget runner differs before identity'; return 1; }
    profile_cache_matches "$profile_pin_dir" || { profile_error 'stage1 identity changed during capture'; return 1; }
    profile_verify_snapshot "$snapshot" "$input_hash" "$driver_hash" || { profile_error 'captured inputs or copied driver differ before measurement'; return 1; }
    [[ "$(profile_require_digest "$profile_result_dir/tools/run_budgeted.sh")" == "$runner_hash" ]] || { profile_error 'copied budget runner differs before measurement'; return 1; }
    profile_write_identity "$profile_result_dir/identity-before.txt" "$profile_result_dir/tools/run_budgeted.sh" "$runner_hash" || { profile_error 'could not record complete pre-run identity'; return 1; }
    profile_check_copied_runner "$profile_result_dir/tools/run_budgeted.sh" "$runner_hash" || { profile_error 'copied budget runner changed during identity capture'; return 1; }
    profile_identity_matches_pin "$profile_result_dir/identity-before.txt" "$profile_pin_dir" "$runner_hash" || { profile_error 'pre-run identity differs from checked cache or copied runner'; return 1; }
    profile_cache_matches "$profile_pin_dir" || { profile_error 'stage1 identity changed before measurement'; return 1; }
    profile_write_stage1_flags "$profile_result_dir/stage1-cc-flags.txt" || { profile_error 'could not record complete stage1 flags'; return 1; }
    grep -Fqx -- "bootstrap_flags_sha256=$(profile_record_value "$profile_pin_dir/receipt.txt" flags_sha256)" "$profile_result_dir/stage1-cc-flags.txt" || { profile_error 'recorded flags differ from checked cache'; return 1; }
    flags_record_hash=$(profile_require_digest "$profile_result_dir/stage1-cc-flags.txt") || return 1
    profile_record_host "$profile_result_dir/host.txt" || return 1
    now_ns=$(profile_now_ns) || return 1
    profile_pre_hash_validation_ns=$(profile_elapsed_ns "$hash_start_ns" "$now_ns") || return 1
    for run in 1 2; do
        profile_active="baseline run $run"; mkdir -p -- "$profile_result_dir/run-$run"
        printf '%s\n' "$snapshot" > "$profile_result_dir/run-$run/cwd.txt"
        profile_write_command "$profile_result_dir/run-$run/command.txt" "$snapshot/selfhost/build/nauqc" check selfhost/main.nq
        set +e
        ( cd "$snapshot" && "$profile_result_dir/tools/run_budgeted.sh" --id "performance-baseline.selfhost-check-$run" --wall-seconds "$wall_limit" --rss-kib "$rss_limit" --result "$profile_result_dir/run-$run/metrics.json" -- "$snapshot/selfhost/build/nauqc" check selfhost/main.nq ) > "$profile_result_dir/run-$run/stdout.log" 2> "$profile_result_dir/run-$run/stderr.log"
        exit_code=$?
        set -e
        if (( exit_code != 0 )) || ! profile_budget_result_ok "$profile_result_dir/run-$run/metrics.json"; then profile_error "baseline run $run failed"; return 1; fi
    done
    profile_active='post-run identity'
    hash_start_ns=$(profile_now_ns) || return 1
    profile_cache_matches "$profile_pin_dir" || { profile_error 'stage1 identity changed during the runs'; return 1; }
    profile_verify_snapshot "$snapshot" "$input_hash" "$driver_hash" || { profile_error 'captured measurement inputs changed during the runs'; return 1; }
    [[ "$(profile_require_digest "$profile_result_dir/tools/run_budgeted.sh")" == "$runner_hash" ]] || { profile_error 'copied budget runner changed during the runs'; return 1; }
    profile_write_identity "$profile_result_dir/identity-after.txt" "$profile_result_dir/tools/run_budgeted.sh" "$runner_hash" || { profile_error 'could not record complete post-run identity'; return 1; }
    profile_check_copied_runner "$profile_result_dir/tools/run_budgeted.sh" "$runner_hash" || { profile_error 'copied budget runner changed during post-run identity capture'; return 1; }
    profile_identity_matches_pin "$profile_result_dir/identity-after.txt" "$profile_pin_dir" "$runner_hash" || { profile_error 'post-run identity differs from checked cache or copied runner'; return 1; }
    cmp -s "$profile_result_dir/identity-before.txt" "$profile_result_dir/identity-after.txt" || { profile_error 'original source, seed, binary, helper, compiler, flags, or HEAD identity changed'; return 1; }
    cmp -s "$profile_pin_dir/cache.txt" "$profile_result_dir/stage1-cache-v2.txt" && cmp -s "$profile_pin_dir/receipt.txt" "$profile_result_dir/stage1-derivation-v1.txt" || { profile_error 'captured cache receipt changed during measurement'; return 1; }
    profile_native_fs_identity "$repo_root" > "$profile_result_dir/checkout-filesystem-after.txt" || return 1
    profile_native_fs_identity "$snapshot" > "$profile_result_dir/snapshot-filesystem-after.txt" || return 1
    cmp -s "$profile_result_dir/checkout-filesystem.txt" "$profile_result_dir/checkout-filesystem-after.txt" && cmp -s "$profile_result_dir/snapshot-filesystem.txt" "$profile_result_dir/snapshot-filesystem-after.txt" || { profile_error 'checkout or snapshot filesystem changed during measurement'; return 1; }
    now_ns=$(profile_now_ns) || return 1
    profile_post_hash_validation_ns=$(profile_elapsed_ns "$hash_start_ns" "$now_ns") || return 1
    first=$(profile_read_budget_result "$profile_result_dir/run-1/metrics.json") || return 1
    second=$(profile_read_budget_result "$profile_result_dir/run-2/metrics.json") || return 1
    read -r status failure ignored wall_one rss_one <<< "$first"
    read -r status failure ignored wall_two rss_two <<< "$second"
    profile_relative_spread_pass "$wall_one" "$wall_two" || { profile_error 'wall-time repeatability is inconclusive (>10%)'; return 1; }
    profile_relative_spread_pass "$rss_one" "$rss_two" || { profile_error 'peak-RSS repeatability is inconclusive (>10%)'; return 1; }
    wall_spread=$(profile_spread "$wall_one" "$wall_two"); rss_spread=$(profile_spread "$rss_one" "$rss_two")
    profile_active=summary; summary_tmp=$(mktemp "$profile_result_dir/.summary.XXXXXX")
    profile_cache_matches "$profile_pin_dir" && profile_verify_snapshot "$snapshot" "$input_hash" "$driver_hash" || { profile_error 'checked inputs changed before summary publication'; return 1; }
    [[ "$(profile_require_digest "$profile_result_dir/stage1-cc-flags.txt")" == "$flags_record_hash" ]] || { profile_error 'recorded flags changed before summary publication'; return 1; }
    {
        printf '{\n  "version": 2,\n  "kind": "performance-baseline",\n  "mode": "baseline",\n  "instrumented": false,\n  "budget_source_phase": "stage1.driver",\n'
        printf '  "setup_ns": %s,\n  "source_capture_ns": %s,\n  "source_capture_bytes": %s,\n' "$profile_setup_ns" "$profile_source_capture_ns" "$source_capture_bytes"
        printf '  "pre_measurement_copy_ns": %s,\n  "pre_measurement_copy_bytes": %s,\n  "pre_run_hash_validation_ns": %s,\n  "post_run_hash_validation_ns": %s,\n' "$profile_pre_copy_ns" "$profile_pre_copy_bytes" "$profile_pre_hash_validation_ns" "$profile_post_hash_validation_ns"
        printf '  "wall_limit_seconds": %s,\n  "peak_rss_limit_kib": %s,\n' "$wall_limit" "$rss_limit"
        printf '  "repeatability": {"status": "pass", "limit": 0.10, "wall_max_min_over_min": %s, "rss_max_min_over_min": %s},\n' "$wall_spread" "$rss_spread"
        printf '  "runs": [{"id": "performance-baseline.selfhost-check-1", "wall_seconds": %s, "peak_rss_kib": %s}, {"id": "performance-baseline.selfhost-check-2", "wall_seconds": %s, "peak_rss_kib": %s}],\n}\n' "$wall_one" "$rss_one" "$wall_two" "$rss_two"
    } > "$summary_tmp" || return 1
    mv -- "$summary_tmp" "$profile_result_dir/summary.pending.json"
    profile_success=true
}

main() {
    cd "$repo_root"
    case "${1:-}" in '') profile_baseline;; --preflight) (( $# == 1 )) || { usage >&2; return 2; }; profile_preflight;; --help|-h) (( $# == 1 )) || { usage >&2; return 2; }; usage;; *) profile_error "unknown option $1"; usage >&2; return 2;; esac
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
