#!/usr/bin/env bash
# Host-unit spies exercise routing only; no real compiler or build is invoked.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
scratch=$(mktemp -d)
lock_pending_handle=
lock_pending_command=
lock_pending_join=
lock_pending_token=
lock_preserve=false

routing_cleanup() {
    local cleanup_code=$? cleanup_record= cleanup_status=0
    trap - EXIT
    if [[ -n "$lock_pending_command" ]]; then
        printf 'RELEASE %s\n' "$lock_pending_token" >&"$lock_pending_command" || lock_preserve=true
    fi
    if [[ -n "$lock_pending_handle" ]]; then
        wait "$lock_pending_handle" || cleanup_status=$?
        lock_pending_handle=
        [[ "$cleanup_status" == 124 ]] || lock_preserve=true
    fi
    if [[ -n "$lock_pending_join" ]]; then
        if ! IFS= read -r -t 2 -u "$lock_pending_join" cleanup_record ||
            [[ "$cleanup_record" != "JOINED $lock_pending_token 37" ]]; then
            lock_preserve=true
        fi
    fi
    if [[ "$lock_preserve" == true ]]; then
        printf 'routing lifecycle evidence retained: %s\n' "$scratch" >&2
        (( cleanup_code != 0 )) || cleanup_code=1
    else
        rm -rf -- "$scratch" || cleanup_code=1
    fi
    exit "$cleanup_code"
}
trap routing_cleanup EXIT
root="$scratch/root"
mkdir -p "$root/scripts" "$root/bin"
cp -- "$script_dir/check_fast.sh" "$root/scripts/check_fast.sh"
printf '%s\n' 'nq_fast_concurrent_run() {' \
    '    printf "concurrent:%s:%s\n" "${NQ_TEST_REUSE_C-unset}" "$*" >> "$NQ_FAST_ROUTING_LOG"' \
    '    _nqfc_release_tier_lock' '    trap - EXIT' '    exit 0' '}' > "$root/scripts/fast_concurrent.sh"
printf '%s\n' '#!/bin/sh' 'printf "cache:%s:%s\n" "${NQ_TEST_REUSE_C-unset}" "$*" >> "$NQ_FAST_ROUTING_LOG"' > "$root/scripts/stage1_cache.sh"
printf '%s\n' '#!/bin/sh' 'printf "unexpected build\n" >> "$NQ_FAST_ROUTING_LOG"' 'exit 99' > "$root/scripts/build_stage1_from_seed.sh"
printf '%s\n' '#!/bin/sh' 'printf "driver:%s:%s\n" "${NQ_TEST_REUSE_C-unset}" "$*" >> "$NQ_FAST_ROUTING_LOG"' > "$root/bin/nauqc"
hosts=(check_seed_capture check_m54_10_provenance check_attestation_batch check_m54_10_attestation check_run_budgeted)
for host in "${hosts[@]}"; do
    printf '%s\n' '#!/bin/sh' 'printf "host:%s:%s\n" "${NQ_TEST_REUSE_C-unset}" "${0##*/}" >> "$NQ_FAST_ROUTING_LOG"' > "$root/scripts/$host.sh"
done
chmod 755 "$root/scripts/"*.sh "$root/bin/nauqc"
export NQ_FAST_ROUTING_LOG="$scratch/calls"
passed=0

routing_case() {
    local setting=$1 selection=$2 expected=$3 code=0 mode=1
    local -a environment=(env) arguments=()
    if [[ "$setting" == unset ]]; then environment+=(-u NQ_TEST_REUSE_C);
    else environment+=("NQ_TEST_REUSE_C=$setting"); mode=$setting; fi
    environment+=(NQ_FAST_CONCURRENT=0)
    [[ "$selection" != partial ]] || arguments=(--suite compiler-index)
    : > "$NQ_FAST_ROUTING_LOG"
    : > "$scratch/expected"
    "${environment[@]}" bash "$root/scripts/check_fast.sh" "${arguments[@]}" \
        > "$scratch/stdout" 2> "$scratch/stderr" || code=$?
    if [[ "$code" != "$expected" ]]; then
        printf 'routing failure: %s/%s exit%s expected%s\n' "$setting" "$selection" "$code" "$expected" >&2
        cat -- "$scratch/stderr" >&2
        exit 1
    fi
    if [[ "$expected" == 0 ]]; then
        printf 'cache:%s:check\n' "$mode" >> "$scratch/expected"
        if [[ "$selection" == partial ]]; then printf 'driver:%s:test --suite compiler-index\n' "$mode" >> "$scratch/expected";
        else
            printf 'driver:%s:test\n' "$mode" >> "$scratch/expected"
            for host in "${hosts[@]}"; do printf 'host:%s:%s.sh\n' "$mode" "$host" >> "$scratch/expected"; done
        fi
        [[ ! -s "$scratch/stderr" ]]
    else
        grep -q 'NQ_TEST_REUSE_C must be 0 or 1' "$scratch/stderr"
    fi
    cmp -s "$scratch/expected" "$NQ_FAST_ROUTING_LOG" || { printf 'routing dispatch mismatch: %s/%s\n' "$setting" "$selection" >&2; exit 1; }
    passed=$((passed + 1))
}

for setting in unset 0 1; do routing_case "$setting" partial 0; done
for setting in '' invalid 2; do
    routing_case "$setting" partial 2
    routing_case "$setting" full 2
done
routing_case unset full 0

concurrent_routing_case() {
    local concurrent=$1 reuse=$2 selection=$3 expected=$4 diagnostic=$5 code=0
    local -a arguments=()
    case "$selection" in
        partial) arguments=(--suite compiler-index) ;;
        host) arguments=(--host-suite provenance) ;;
    esac
    : > "$NQ_FAST_ROUTING_LOG"
    : > "$scratch/expected"
    env "NQ_FAST_CONCURRENT=$concurrent" "NQ_TEST_REUSE_C=$reuse" \
        bash "$root/scripts/check_fast.sh" "${arguments[@]}" \
        > "$scratch/stdout" 2> "$scratch/stderr" || code=$?
    [[ "$code" == "$expected" ]] || { printf 'concurrent routing exit mismatch\n' >&2; exit 1; }
    if [[ "$expected" == 0 ]]; then
        printf 'cache:1:check\nconcurrent:1:%s\n' "$root" > "$scratch/expected"
        [[ ! -s "$scratch/stderr" ]]
        [[ ! -e "$root/build/verification/.check-fast-lock" ]]
    else
        grep -Fq -- "$diagnostic" "$scratch/stderr"
    fi
    cmp -s "$scratch/expected" "$NQ_FAST_ROUTING_LOG" || { printf 'concurrent routing dispatch mismatch\n' >&2; exit 1; }
    passed=$((passed + 1))
}
concurrent_routing_case 1 1 full 0 ''
concurrent_routing_case 1 0 full 2 'requires NQ_TEST_REUSE_C=1'
concurrent_routing_case 1 1 partial 2 'requires the complete no-argument warm tier'
concurrent_routing_case 1 1 host 2 'requires the complete no-argument warm tier'
for setting in '' invalid 2; do
    concurrent_routing_case "$setting" 1 full 2 'NQ_FAST_CONCURRENT must be 0 or 1'
done
grep -Fqx 'run_phase owned_tests env NQ_TEST_REUSE_C=0 NQ_FAST_CONCURRENT=0 scripts/check_fast.sh' \
    "$script_dir/check_milestone.sh"
passed=$((passed + 1))
# Interrupt the actual wrapper while its synchronous stage owns a live
# descendant. No PID is signalled or polled: GNU timeout owns each direct
# target. Fresh challenges prove liveness on BOTH sides of the refusal.
# The surviving stage genuinely waits its own timeout child, which reaps the
# leaf. The harness cannot directly wait that stage after it is orphaned.
cat > "$scratch/blocked-leaf.sh" <<'ROUTING_LEAF'
#!/bin/bash
set -euo pipefail
control=$1
IFS= read -r token < "$control/token"
exec {command_fd}<>"$control/command" {reply_fd}<>"$control/reply"
printf 'READY %s\n' "$token" >&"$reply_fd"
while IFS= read -r -t 2 -u "$command_fd" command; do
    case "$command" in
        "PING $token before"|"PING $token after")
            printf 'ALIVE %s\n' "${command#PING }" >&"$reply_fd" ;;
        "RELEASE $token") exit 37 ;;
        *) exit 82 ;;
    esac
done
exit 83
ROUTING_LEAF
cat > "$scratch/blocked-stage.sh" <<'ROUTING_STAGE'
#!/bin/bash
set -euo pipefail
stage_root=$(cd -- "${BASH_SOURCE[0]%/*}/.." && pwd -P)
control="$stage_root/control"
IFS= read -r token < "$control/token"
exec {join_fd}<>"$control/join"
printf 'blocked:%s\n' "${0##*/}" >> "$NQ_FAST_ROUTING_LOG"
/usr/bin/timeout --foreground --kill-after=0.2s 3s \
    /bin/bash "$control/leaf.sh" "$control" &
child_handle=$!
child_status=0
wait "$child_handle" || child_status=$?
child_handle=
printf 'JOINED %s %s\n' "$token" "$child_status" >&"$join_fd"
exit "$child_status"
ROUTING_STAGE

interrupted_lock_case() {
    local stage=$1 case_root="$scratch/lock-$1" control
    local command_fd reply_fd join_fd record= first_status=0 second_status=0
    cp -R -- "$root" "$case_root"
    control="$case_root/control"
    mkdir -- "$control"
    cp -- "$scratch/blocked-leaf.sh" "$control/leaf.sh"
    printf '%s\n' "lock-$stage-$BASHPID" > "$control/token"
    mkfifo -- "$control/command" "$control/reply" "$control/join"
    exec {command_fd}<>"$control/command" {reply_fd}<>"$control/reply" {join_fd}<>"$control/join"
    case "$stage" in
        cache) cp -- "$scratch/blocked-stage.sh" "$case_root/scripts/stage1_cache.sh" ;;
        builder)
            printf '%s\n' '#!/bin/sh' \
                'printf "cache:%s:%s\n" "${NQ_TEST_REUSE_C-unset}" "$*" >> "$NQ_FAST_ROUTING_LOG"' \
                'exit 1' > "$case_root/scripts/stage1_cache.sh"
            cp -- "$scratch/blocked-stage.sh" "$case_root/scripts/build_stage1_from_seed.sh"
            ;;
        serial) cp -- "$scratch/blocked-stage.sh" "$case_root/bin/nauqc" ;;
        *) return 1 ;;
    esac
    chmod 755 "$case_root/scripts/"*.sh "$case_root/bin/nauqc"
    : > "$NQ_FAST_ROUTING_LOG"
    lock_pending_command=$command_fd
    lock_pending_join=$join_fd
    IFS= read -r lock_pending_token < "$control/token"
    /usr/bin/timeout --foreground --kill-after=0.2s 0.5s \
        /usr/bin/env NQ_FAST_CONCURRENT=0 NQ_TEST_REUSE_C=1 \
        /bin/bash "$case_root/scripts/check_fast.sh" \
        > "$control/first.stdout" 2> "$control/first.stderr" &
    lock_pending_handle=$!
    IFS= read -r -t 1 -u "$reply_fd" record
    [[ "$record" == "READY $lock_pending_token" ]]
    wait "$lock_pending_handle" || first_status=$?
    lock_pending_handle=
    [[ "$first_status" == 124 ]]
    # KILL alone also leaves the old buggy lock. Require actual EXIT handling.
    grep -Fq 'unverified tier completion; lock retained' "$control/first.stderr"
    printf 'PING %s before\n' "$lock_pending_token" >&"$command_fd"
    IFS= read -r -t 1 -u "$reply_fd" record
    [[ "$record" == "ALIVE $lock_pending_token before" ]]
    cp -- "$NQ_FAST_ROUTING_LOG" "$control/before-second"
    /usr/bin/timeout --foreground --kill-after=0.2s 1s \
        /usr/bin/env NQ_FAST_CONCURRENT=0 NQ_TEST_REUSE_C=1 \
        /bin/bash "$case_root/scripts/check_fast.sh" \
        > "$control/second.stdout" 2> "$control/second.stderr" || second_status=$?
    [[ "$second_status" == 1 ]]
    grep -Fq 'complete tier lock refused' "$control/second.stderr"
    cmp -s "$control/before-second" "$NQ_FAST_ROUTING_LOG"
    [[ -d "$case_root/build/verification/.check-fast-lock" ]]
    printf 'PING %s after\n' "$lock_pending_token" >&"$command_fd"
    IFS= read -r -t 1 -u "$reply_fd" record
    [[ "$record" == "ALIVE $lock_pending_token after" ]]
    printf 'RELEASE %s\n' "$lock_pending_token" >&"$command_fd"
    lock_pending_command=
    IFS= read -r -t 1 -u "$join_fd" record
    [[ "$record" == "JOINED $lock_pending_token 37" ]]
    lock_pending_join=
    [[ -d "$case_root/build/verification/.check-fast-lock" ]]
    # Explicit isolated-fixture teardown after the reported terminal wait;
    # never production stale-lock recovery or a PID/marker liveness guess.
    rmdir -- "$case_root/build/verification/.check-fast-lock"
    exec {command_fd}>&- {reply_fd}>&- {join_fd}>&-
    lock_pending_token=
    passed=$((passed + 1))
}
for setting in cache builder serial; do interrupted_lock_case "$setting"; done

unexpected_exit_case() {
    local case_root="$scratch/unexpected-exit" code=0
    cp -R -- "$root" "$case_root"
    # Omit the concurrent stub's explicit release and EXIT clearing.
    printf '%s\n' 'nq_fast_concurrent_run() { return 0; }' > "$case_root/scripts/fast_concurrent.sh"
    env NQ_FAST_CONCURRENT=1 NQ_TEST_REUSE_C=1 \
        bash "$case_root/scripts/check_fast.sh" > "$scratch/unexpected.stdout" \
        2> "$scratch/unexpected.stderr" || code=$?
    [[ "$code" == 125 && -d "$case_root/build/verification/.check-fast-lock" ]]
    grep -Fq 'unverified tier completion; lock retained' "$scratch/unexpected.stderr"
    rmdir -- "$case_root/build/verification/.check-fast-lock"
    passed=$((passed + 1))
}
unexpected_exit_case

printf 'fast routing unit fixtures passed (%s cases; compiler/build spies only)\n' "$passed"
