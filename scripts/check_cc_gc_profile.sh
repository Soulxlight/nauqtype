#!/usr/bin/env bash
# Synthetic host-compiler profile contracts only; this is not Linux compiler evidence.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
source "$script_dir/provenance.sh"
source "$script_dir/seed_manifest.sh"
scratch=$(mktemp -d -t nauqtype-cc-profile-tests-XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
cp -- "$repo_root/tests/fixtures/m56_cc_profile/cc.sh" "$scratch/cc"
chmod +x "$scratch/cc"
CC="$scratch/cc"
export CC
passed=0

pass() { printf 'PASS %s\n' "$1"; passed=$((passed + 1)); }
reject() {
    local label=$1
    shift
    if "$@" > "$scratch/reject.out" 2> "$scratch/reject.err"; then
        printf 'FAIL accepted: %s\n' "$label" >&2
        exit 1
    fi
    pass "$label"
}
select_profile() {
    local mode=$1 output=$2
    NQ_TEST_CC_MODE="$mode" prov_cc_identity "$CC" "$scratch/identity"
    NQ_TEST_CC_MODE="$mode" prov_cc_gc_profile_select "$CC" "$scratch/identity" "$output"
}

bash -n "$script_dir/provenance.sh" "$script_dir/seed_manifest.sh" "$script_dir/check_cc_gc_profile.sh" "$CC"
pass 'shell syntax'

select_profile gcc "$scratch/profile"
[[ "$(< "$scratch/profile")" == gcc-20-32768 ]]
prov_bootstrap_args_materialize gcc-20-32768 "$scratch"
prov_argv_load "$scratch/stage1-args" 10 stage1_args
mkdir -p "$scratch/build/seed" "$scratch/stdlib" "$scratch/selfhost/build"
: > "$scratch/build/seed/stage1.c"; : > "$scratch/stdlib/runtime.c"
(cd "$scratch" && NQ_TEST_ARGV_LOG="$scratch/executed-argv" "$CC" "${stage1_args[@]}")
cmp -s "$scratch/stage1-args" "$scratch/executed-argv"
flags=$(prov_bootstrap_flags_sha256_from_files gcc-20-32768 "$scratch/seed-args" "$scratch/stage1-args")
expected=$({ printf '%s\0' nauqtype-bootstrap-flags/v1 seed; cat "$scratch/seed-args"; printf 'stage1\0'; cat "$scratch/stage1-args"; } | prov_hash_stream)
[[ "$flags" == "$expected" ]]
pass 'GCC fixed profile execution and digest share validated argv bytes'

for mode in portable exit1 exit2 duplicate malformed stderr; do
    select_profile "$mode" "$scratch/profile-$mode"
    [[ "$(< "$scratch/profile-$mode")" == portable ]]
done
pass 'portable fallback covers unsupported clean outputs and exit 1/2'

select_profile exact64k-exit1 "$scratch/profile-exact64k"
[[ "$(< "$scratch/profile-exact64k")" == portable ]]
pass 'exact 64 KiB capture remains accepted for exit 1 fallback'

for mode in timeout signal oversize overflow-stdout-exit1 overflow-stderr-exit2; do
    NQ_TEST_CC_MODE="$mode" prov_cc_identity "$CC" "$scratch/identity-$mode"
    reject "$mode probe is a hard error" env NQ_TEST_CC_MODE="$mode" bash -c \
        'source "$1"; prov_cc_gc_profile_select "$2" "$3" "$4"' _ \
        "$script_dir/provenance.sh" "$CC" "$scratch/identity-$mode" "$scratch/rejected-$mode"
done
for mode in overflow-stdout-exit1 overflow-stderr-exit2; do
    reject "POSIX $mode probe is a hard error" env POSIXLY_CORRECT=1 NQ_TEST_CC_MODE="$mode" bash -c \
        'source "$1"; prov_cc_gc_profile_select "$2" "$3" "$4"' _ \
        "$script_dir/provenance.sh" "$CC" "$scratch/identity-$mode" "$scratch/rejected-posix-$mode"
done
for mode in gcc exact64k-exit1; do
    NQ_TEST_CC_MODE="$mode" prov_cc_identity "$CC" "$scratch/identity-posix-$mode"
    env POSIXLY_CORRECT=1 NQ_TEST_CC_MODE="$mode" bash -c \
        'source "$1"; prov_cc_gc_profile_select "$2" "$3" "$4"' _ \
        "$script_dir/provenance.sh" "$CC" "$scratch/identity-posix-$mode" "$scratch/profile-posix-$mode"
    expected=portable
    [[ "$mode" != gcc ]] || expected=gcc-20-32768
    [[ "$(< "$scratch/profile-posix-$mode")" == "$expected" ]]
done
pass 'POSIX probe preserves exact 68 KiB capture and 64 KiB acceptance bounds'
cp -- "$repo_root/tests/fixtures/m56_cc_profile/cc.sh" "$scratch/cc-changing"
chmod +x "$scratch/cc-changing"
NQ_TEST_CC_MODE=identity-change prov_cc_identity "$scratch/cc-changing" "$scratch/identity-change"
reject 'compiler identity change during probe' env NQ_TEST_CC_MODE=identity-change bash -c \
    'source "$1"; prov_cc_gc_profile_select "$2" "$3" "$4"' _ \
    "$script_dir/provenance.sh" "$scratch/cc-changing" "$scratch/identity-change" "$scratch/rejected-identity"

NQ_TEST_CC_MODE=gcc prov_cc_identity "$CC" "$scratch/freeze-identity"
NQ_TEST_CC_MODE=gcc NQ_BOOTSTRAP_CC_GC_PROFILE=gcc-20-32768 \
    prov_cc_gc_profile_freeze "$CC" "$scratch/freeze-identity" "$scratch/frozen"
[[ "$(< "$scratch/frozen")" == gcc-20-32768 ]]
reject 'empty inherited profile' env NQ_TEST_CC_MODE=gcc NQ_BOOTSTRAP_CC_GC_PROFILE= bash -c \
    'source "$1"; prov_cc_gc_profile_freeze "$2" "$3" "$4"' _ \
    "$script_dir/provenance.sh" "$CC" "$scratch/freeze-identity" "$scratch/rejected-empty"
reject 'parent child profile mismatch' env NQ_TEST_CC_MODE=gcc NQ_BOOTSTRAP_CC_GC_PROFILE=portable bash -c \
    'source "$1"; prov_cc_gc_profile_freeze "$2" "$3" "$4"' _ \
    "$script_dir/provenance.sh" "$CC" "$scratch/freeze-identity" "$scratch/rejected-mismatch"
pass 'validated private transport is equality-only'

producer_failure_after_eight() { prov_stage1_args portable; return 73; }
producer_truncated() {
    printf '%s\0' -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib build/seed/stage1.c stdlib/runtime.c -o
    printf '%s' selfhost/build/nauqc
}
reject 'producer failure after eight complete items' prov_argv_materialize "$scratch/partial" 8 producer_failure_after_eight
reject 'producer truncated without final NUL' prov_argv_materialize "$scratch/truncated" 8 producer_truncated
[[ ! -e "$scratch/partial" && ! -e "$scratch/truncated" ]]

printf '%s\0' -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib build/generator.c stdlib/runtime.c -o build/generator > "$scratch/old-flags"
seed_flags_verify "$scratch/old-flags"
cp -- "$scratch/old-flags" "$scratch/old-ten-flags"
printf '%s\0' --param=ggc-min-expand=20 --param=ggc-min-heapsize=32768 >> "$scratch/old-ten-flags"
seed_flags_verify "$scratch/old-ten-flags"
cp -- "$scratch/stage1-args" "$scratch/new-flags"
seed_flags_verify "$scratch/new-flags"
printf '%s\0' --param=ggc-min-heapsize=32768 --param=ggc-min-expand=20 >> "$scratch/old-flags"
reject 'reordered GCC seed flags' seed_flags_verify "$scratch/old-flags"
pass 'historical safe-relative eight and fixed-suffix current ten seed recipes'

printf 'M56 CC GC profile fixtures passed (%s assertions; synthetic CC only)\n' "$passed"
