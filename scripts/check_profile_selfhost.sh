#!/usr/bin/env bash
# Synthetic shell contracts only. This never claims a Linux compiler baseline.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
scratch=$(mktemp -d -t nauqtype-profile-selfhost-tests-XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
passed=0
pass() { printf 'PASS %s\n' "$1"; passed=$((passed + 1)); }
reject() { local name=$1; shift; if "$@" > "$scratch/out" 2>&1; then printf 'FAIL accepted: %s\n' "$name" >&2; exit 1; fi; pass "$name"; }

bash -n "$repo_root/scripts/profile_selfhost.sh"; bash -n "$repo_root/scripts/check_profile_selfhost.sh"; pass 'shell syntax'
"$repo_root/scripts/profile_selfhost.sh" --help > "$scratch/help"; grep -q 'non-instrumented' "$scratch/help"; reject 'malformed option' "$repo_root/scripts/profile_selfhost.sh" --instrumented; pass 'CLI help and rejection'
source "$repo_root/scripts/profile_selfhost.sh"

# Exercise preflight through injected functions and a fixture cache, never host state.
mkdir -p "$scratch/preflight/scripts"; printf '#!/usr/bin/env bash\nexit "${NQ_CACHE_EXIT:-0}"\n' > "$scratch/preflight/scripts/stage1_cache.sh"; chmod 755 "$scratch/preflight/scripts/stage1_cache.sh"
(
    script_dir="$scratch/preflight/scripts"; profile_linux_host_ok(){ :; }; profile_native_fs_identity(){ :; }; profile_gnu_tools_ok(){ :; }; profile_cc_available(){ :; }; profile_host_cpu_available(){ :; }
    profile_read_cache_records(){ mkdir -p "$1"; printf 'cache\n' > "$1/cache.txt"; printf 'receipt\n' > "$1/receipt.txt"; }; profile_cache_matches(){ :; }
    NQ_CACHE_EXIT=0 profile_preflight
) || { printf 'FAIL synthetic supported preflight\n' >&2; exit 1; }
reject 'synthetic stale cache' bash -c 'source "$1"; script_dir="$2"; profile_linux_host_ok(){ :; }; profile_native_fs_identity(){ :; }; profile_gnu_tools_ok(){ :; }; profile_cc_available(){ :; }; profile_host_cpu_available(){ :; }; profile_read_cache_records(){ mkdir -p "$1"; printf "cache\n" > "$1/cache.txt"; printf "receipt\n" > "$1/receipt.txt"; }; profile_cache_matches(){ :; }; NQ_CACHE_EXIT=1 profile_preflight' _ "$repo_root/scripts/profile_selfhost.sh" "$scratch/preflight/scripts"
pass 'isolated preflight contracts'

(
    profile_fs_probe(){ printf '%s\n' "$NQ_TEST_FS"; }
    NQ_TEST_FS='ext4 ef53 123' profile_native_fs_identity "$scratch" > "$scratch/fs-ok"
    grep -q '^device=123$' "$scratch/fs-ok"
    for fs in 'drvfs 5346544e 123' 'cifs ff534d42 123' 'nfs 6969 123' 'overlay 794c7630 123' 'unknown 0000 123' 'ext4 0000 123'; do
        if NQ_TEST_FS="$fs" profile_native_fs_identity "$scratch" > /dev/null; then exit 1; fi
    done
) || { printf 'FAIL portable filesystem identity rejection\n' >&2; exit 1; }
pass 'native ext4 allowlist and Windows/network rejection'

profile_relative_spread_pass 10 11; profile_relative_spread_pass 100 110
if profile_relative_spread_pass 10 11.01 || profile_relative_spread_pass 100 110.01 || profile_relative_spread_pass 0 1; then printf 'FAIL repeatability boundary\n' >&2; exit 1; fi
pass 'wall and RSS repeatability math'
if ( prov_sha256(){ return 0; }; profile_require_digest ignored ); then printf 'FAIL accepted missing digest\n' >&2; exit 1; fi
pass 'missing digest rejection'

make_fixture() {
    local root=$1
    mkdir -p "$root/selfhost/build" "$root/build/seed" "$root/scripts" "$root/state"
    printf '#!/usr/bin/env bash\nprintf "driver cwd=%%s\\n" "$PWD"\n' > "$root/selfhost/build/nauqc"; chmod 755 "$root/selfhost/build/nauqc"
    printf 'derivation\n' > "$root/build/seed/stage1-derivation-v1.txt"
    printf '%s\n' '#!/usr/bin/env bash' 'set -eu' 'result=""' 'while [ "$#" -gt 0 ]; do case "$1" in --result) result=$2; shift 2;; --) shift; break;; *) shift 2;; esac; done' '"$@"' 'if [ -f "$NQ_PROFILE_FIXTURE_STATE/count" ]; then n=$(<"$NQ_PROFILE_FIXTURE_STATE/count"); else n=0; fi' 'n=$((n+1)); printf "%s" "$n" > "$NQ_PROFILE_FIXTURE_STATE/count"' 'case "${NQ_PROFILE_FIXTURE_MODE:-ok}" in' 'failed) status=failed; failure=command; code=7; wall=1; rss=10;;' 'spread) status=ok; failure=none; code=0; wall=$([ "$n" = 1 ] && printf 10 || printf 12); rss=100;;' 'identity) status=ok; failure=none; code=0; wall=10; rss=100; printf changed > "$NQ_PROFILE_FIXTURE_STATE/changed";;' '*) status=ok; failure=none; code=0; wall=10; rss=100;; esac' 'printf "{\n  \"status\": \"%s\",\n  \"failure\": \"%s\",\n  \"command_exit_code\": %s,\n  \"wall_seconds\": %s,\n  \"peak_rss_kib\": %s,\n  \"wall_limit_seconds\": 9\n}\n" "$status" "$failure" "$code" "$wall" "$rss" > "$result"' 'exit "$code"' > "$root/scripts/run_budgeted.sh"
    chmod 755 "$root/scripts/run_budgeted.sh"
}

(
    root="$scratch/cache-pin"; make_fixture "$root"
    mkdir -p "$root/bootstrap/seed" "$root/build/seed" "$root/pin"
    printf 'source\n' > "$root/selfhost/main.nq"
    printf 'manifest\n' > "$root/bootstrap/seed/manifest.json"
    printf '#!/usr/bin/env bash\nexit 0\n' > "$root/build/seed/nauqc-seed"; chmod 755 "$root/build/seed/nauqc-seed"
    printf 'stage1\n' > "$root/build/seed/stage1.c"
    printf 'flags\n' > "$root/state/flags"
    repo_root="$root"; script_dir="$root/scripts"
    prov_inputs_sha256(){ sha256sum "$1/selfhost/main.nq" | cut -d ' ' -f 1; }
    prov_bootstrap_flags_sha256(){ [[ "${NQ_FLAGS_ERROR:-0}" == 0 ]] || return 1; sha256sum "$repo_root/state/flags" | cut -d ' ' -f 1; }
    prov_cc_identity(){ printf 'cc_path=/usr/bin/cc\ncc_sha256=%064d\ncc_version_sha256=%064d\ncc_target=x86_64-linux-gnu\n' 0 0 > "$2"; }
    profile_linux_host_ok(){ :; }; profile_native_fs_identity(){ :; }; profile_gnu_tools_ok(){ :; }; profile_cc_available(){ :; }; profile_host_cpu_available(){ :; }
    digest(){ sha256sum "$1" | cut -d ' ' -f 1; }
    inputs=$(prov_inputs_sha256 "$root"); manifest=$(digest "$root/bootstrap/seed/manifest.json"); seed=$(digest "$root/build/seed/nauqc-seed"); stage1=$(digest "$root/build/seed/stage1.c"); driver=$(digest "$root/selfhost/build/nauqc"); flags=$(prov_bootstrap_flags_sha256)
    printf 'stage1-derivation/v1\ninputs_sha256=%s\nseed_manifest_sha256=%s\nseed_exe_sha256=%s\nstage1_c_sha256=%s\nstage1_exe_sha256=%s\ncc_path=/usr/bin/cc\ncc_sha256=%064d\ncc_version_sha256=%064d\ncc_target=x86_64-linux-gnu\nflags_sha256=%s\n' "$inputs" "$manifest" "$seed" "$stage1" "$driver" 0 0 "$flags" > "$root/build/seed/stage1-derivation-v1.txt"
    derivation=$(digest "$root/build/seed/stage1-derivation-v1.txt")
    printf 'stage1-cache/v2\ninputs_sha256=%s\nderivation_sha256=%s\nstage1_c_sha256=%s\nstage1_exe_sha256=%s\n' "$inputs" "$derivation" "$stage1" "$driver" > "$root/build/seed/stage1-cache-v2.txt"
    printf '#!/usr/bin/env bash\nif [[ "${NQ_MUTATE_ON_CACHE:-}" == source ]]; then printf changed > "$NQ_PROFILE_FIXTURE_ROOT/selfhost/main.nq"; fi\nif [[ "${NQ_MUTATE_ON_CACHE:-}" == driver ]]; then printf changed > "$NQ_PROFILE_FIXTURE_ROOT/selfhost/build/nauqc"; fi\nexit 0\n' > "$root/scripts/stage1_cache.sh"
    chmod 755 "$root/scripts/stage1_cache.sh"
    export NQ_PROFILE_FIXTURE_ROOT="$root"
    profile_preflight "$root/pin" || exit 1
    profile_cache_matches "$root/pin" || exit 1
    printf changed > "$root/selfhost/main.nq"
    if profile_cache_matches "$root/pin"; then exit 1; fi
    printf 'source\n' > "$root/selfhost/main.nq"
    printf changed > "$root/selfhost/build/nauqc"
    if profile_cache_matches "$root/pin"; then exit 1; fi
    printf '#!/usr/bin/env bash\nprintf "driver cwd=%%s\\n" "$PWD"\n' > "$root/selfhost/build/nauqc"
    chmod 755 "$root/selfhost/build/nauqc"
    profile_cache_matches "$root/pin" || exit 1
    mkdir -p "$root/snapshot/selfhost/build"
    cp "$root/selfhost/main.nq" "$root/snapshot/selfhost/main.nq"
    cp "$root/selfhost/build/nauqc" "$root/snapshot/selfhost/build/nauqc"
    profile_verify_snapshot "$root/snapshot" "$inputs" "$driver" || exit 1
    printf changed > "$root/snapshot/selfhost/build/nauqc"
    if profile_verify_snapshot "$root/snapshot" "$inputs" "$driver"; then exit 1; fi
    printf 'changed\n' > "$root/build/seed/stage1-cache-v2.txt"
    if profile_cache_matches "$root/pin"; then exit 1; fi
    printf 'stage1-cache/v2\ninputs_sha256=%s\nderivation_sha256=%s\nstage1_c_sha256=%s\nstage1_exe_sha256=%s\n' "$inputs" "$derivation" "$stage1" "$driver" > "$root/build/seed/stage1-cache-v2.txt"
    {
        for key in inputs_sha256 seed_manifest_sha256 seed_exe_sha256 stage1_c_sha256; do printf '%s=%s\n' "$key" "$(profile_record_value "$root/pin/receipt.txt" "$key")"; done
        printf 'driver_sha256=%s\ncopied_runner_sha256=%064d\nbootstrap_flags_sha256=%s\nderivation_sha256=%s\n' "$driver" 0 "$flags" "$derivation"
        for key in cc_path cc_sha256 cc_version_sha256 cc_target; do printf '%s=%s\n' "$key" "$(profile_record_value "$root/pin/receipt.txt" "$key")"; done
    } > "$root/identity.txt"
    profile_identity_matches_pin "$root/identity.txt" "$root/pin" "$(printf '%064d' 0)" || exit 1
    sed "s/^driver_sha256=.*/driver_sha256=$(printf '%064d' 0)/" "$root/identity.txt" > "$root/bad-identity.txt"
    if profile_identity_matches_pin "$root/bad-identity.txt" "$root/pin" "$(printf '%064d' 0)"; then exit 1; fi
    NQ_FLAGS_ERROR=1 profile_cache_matches "$root/pin" && exit 1
    NQ_FLAGS_ERROR=1 profile_write_stage1_flags "$root/flags-output.txt" && exit 1
    if ( prov_stage1_args(){ return 1; }; profile_write_stage1_flags "$root/flags-output.txt" ); then exit 1; fi
    NQ_MUTATE_ON_CACHE=source profile_preflight "$root/late-pin-source" && exit 1
    printf 'source\n' > "$root/selfhost/main.nq"
    NQ_MUTATE_ON_CACHE=driver profile_preflight "$root/late-pin-driver" && exit 1
    :
) || { printf 'FAIL checked cache pin or late mutation rejection\n' >&2; exit 1; }
pass 'pinned cache, source/driver races, and flags failure'

{
    printf 'original runner\n' > "$scratch/runner-original"
    cp "$scratch/runner-original" "$scratch/runner-copy"
    expected_runner=$(profile_require_digest "$scratch/runner-original")
    profile_check_copied_runner "$scratch/runner-copy" "$expected_runner" || exit 1
    profile_runner_identity_record "$scratch/runner-copy" "$expected_runner" > "$scratch/runner-identity" || exit 1
    grep -Fqx "copied_runner_sha256=$expected_runner" "$scratch/runner-identity" || exit 1
    printf 'mutated runner\n' > "$scratch/runner-copy"
    if profile_check_copied_runner "$scratch/runner-copy" "$expected_runner"; then
        printf 'FAIL accepted copied runner drift\n' >&2; exit 1
    fi
    if profile_runner_identity_record "$scratch/runner-copy" "$expected_runner" > "$scratch/runner-drift-identity"; then
        printf 'FAIL accepted runner changed between copy and identity\n' >&2; exit 1
    fi
} || { printf 'FAIL copied runner identity pin\n' >&2; exit 1; }
pass 'copied runner is pinned at identity and drift is rejected'

cat > "$scratch/costs.json" <<'EOF'
{
  "setup_ns": 1,
  "source_capture_ns": 2,
  "source_capture_bytes": 3,
  "pre_measurement_copy_ns": 4,
  "pre_measurement_copy_bytes": 5,
  "pre_run_hash_validation_ns": 6,
  "post_run_hash_validation_ns": 7,
  "total_workflow_ns": 8,
  "total_workflow_seconds": 0.000000008,
  "workflow_includes_cleanup": true
}
EOF
profile_summary_costs_valid "$scratch/costs.json" || { printf 'FAIL numeric workflow cost fields\n' >&2; exit 1; }
sed 's/"source_capture_bytes": 3/"source_capture_bytes": "3"/' "$scratch/costs.json" > "$scratch/bad-costs.json"
if profile_summary_costs_valid "$scratch/bad-costs.json"; then printf 'FAIL accepted nonnumeric workflow cost\n' >&2; exit 1; fi
pass 'workflow summary requires numeric costs and cleanup boundary'
if profile_elapsed_ns 1790815734686586200 1790815734686586199; then
    printf 'FAIL accepted negative clock interval\n' >&2; exit 1
fi
if profile_elapsed_ns malformed 1790815734686586201; then
    printf 'FAIL accepted malformed clock sample\n' >&2; exit 1
fi
pass 'workflow clock rejects negative and malformed intervals'

run_mock() {
    local mode=$1 root result rc
    root="$scratch/$mode"
    make_fixture "$root"
    if (
        repo_root="$root"; script_dir="$root/scripts"; profile_result_dir=""; profile_active=setup; profile_success=false
        profile_preflight(){ mkdir -p "$1"; printf 'inputs_sha256=%064d\nstage1_exe_sha256=%064d\nflags_sha256=%064d\n' 0 0 0 > "$1/receipt.txt"; printf 'cache\n' > "$1/cache.txt"; }; performance_budget_for(){ printf '9 999\n'; }; prov_input_paths(){ printf 'selfhost/main.nq\n'; }; prov_inputs_sha256(){ printf 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n'; }
        prov_capture_inputs(){ mkdir -p "$2/selfhost"; printf 'source\n' > "$2/selfhost/main.nq"; }
        profile_verify_snapshot(){
            [[ -x "$1/selfhost/build/nauqc" ]] || return 1
            if [[ "$mode" == runner-drift && ! -f "$NQ_PROFILE_FIXTURE_STATE/runner-drift-done" ]]; then
                printf 'changed runner\n' > "$profile_result_dir/tools/run_budgeted.sh"
                : > "$NQ_PROFILE_FIXTURE_STATE/runner-drift-done"
            fi
        }
        profile_cache_matches(){ :; }; profile_identity_matches_pin(){ grep -Fqx -- "copied_runner_sha256=$3" "$1"; }; profile_native_fs_identity(){ printf 'profile-selfhost-filesystem/v1\npath=%s\nfs_type=ext4\nfs_magic=ef53\ndevice=123\n' "$1"; }
        profile_write_identity(){ printf 'identity=%s\ncopied_runner_sha256=%s\n' "$( [[ -f "$NQ_PROFILE_FIXTURE_STATE/changed" ]] && printf changed || printf same )" "$3" > "$1"; }
        profile_write_stage1_flags(){ printf 'bootstrap_flags_sha256=%064d\n' 0 > "$1"; }; profile_record_host(){ : > "$1"; }
        if [[ "$mode" == flags ]]; then profile_write_stage1_flags(){ return 1; }; fi
        if [[ "$mode" == identity-error ]]; then profile_write_identity(){ return 1; }; fi
        if [[ "$mode" == finalization-error ]]; then profile_append_workflow_time(){ return 1; }; fi
        export NQ_PROFILE_FIXTURE_STATE="$root/state" NQ_PROFILE_FIXTURE_MODE="$mode"
        if [[ "$mode" == ok || "$mode" == finalization-error ]]; then profile_baseline; else ! profile_baseline; fi
    ); then
        rc=0
    else
        rc=$?
    fi
    if [[ "$mode" == finalization-error ]]; then
        [[ "$rc" != 0 ]] || { printf 'FAIL finalization failure returned success\n' >&2; exit 1; }
    elif [[ "$rc" != 0 ]]; then
        printf 'FAIL mocked %s pipeline\n' "$mode" >&2; exit 1
    fi
    result=$(find "$root/build/verification/performance-baseline" -name summary.json -o -name failure.txt)
    case "$mode" in
        ok)
            grep -q '"status": "pass"' "$result"
            grep -q "$root/build/verification/performance-baseline" "$root/build/verification/performance-baseline"/*/run-1/cwd.txt
            profile_summary_costs_valid "$result"
            profile_summary_json_shape_valid "$result"
            grep -q '"source_capture_bytes": 7,' "$result"
            grep -Eq '^  "runs": \[.*\],$' "$result"
            sed '/"runs":/s/],$/]/' "$result" > "$root/bad-summary.json"
            if profile_summary_json_shape_valid "$root/bad-summary.json"; then
                printf 'FAIL accepted missing JSON comma boundary\n' >&2; exit 1
            fi
            ;;
        finalization-error) [[ "$result" == *failure.txt ]] && [[ ! -f "${result%/failure.txt}/summary.json" ]] && [[ ! -f "${result%/failure.txt}/summary.pending.json" ]];;
        *) [[ "$result" == *failure.txt ]] && [[ ! -f "${result%/failure.txt}/summary.json" ]];;
    esac
    pass "mocked $mode pipeline"
}
run_mock ok; run_mock failed; run_mock spread; run_mock identity; run_mock flags; run_mock identity-error; run_mock runner-drift; run_mock finalization-error
printf 'profile selfhost shell checks passed: %s (stubs only; no Linux baseline claimed)\n' "$passed"
