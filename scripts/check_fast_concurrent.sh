#!/usr/bin/env bash
# Default: UNIT/STUB providers and disposable spies, never real systemd or gates.
# Native: real provider on the same disposable spies; requires a prebuilt NQ witness.
set -euo pipefail

p1c_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
p1c_repo_root="$(cd -- "$p1c_script_dir/.." && pwd -P)"
source "$p1c_script_dir/fast_concurrent.sh"
p1c_native=false
p1c_native_exec_only=false
p1c_witness=''
case "$#" in
    0) ;;
    2)
        [[ ( "$1" == --native || "$1" == --native-exec ) && -f "$2" && -x "$2" ]] || exit 2
        p1c_native=true
        [[ "$1" != --native-exec ]] || p1c_native_exec_only=true
        p1c_witness="$(realpath -e -- "$2")"
        ;;
    *) printf 'Usage: scripts/check_fast_concurrent.sh [--native|--native-exec PREBUILT_NQ_WITNESS]\n' >&2; exit 2 ;;
esac
p1c_scratch="$(mktemp -d -t nauqtype-concurrent-fixtures-XXXXXX)"
p1c_passed=0
p1c_pending=()
p1c_preserve=false

p1c_cleanup() {
    local p1c_code=$?
    trap - EXIT
    if (( ${#p1c_pending[@]} != 0 )); then
        printf 'concurrent fixtures: unjoined fixture handles; evidence retained\n' >&2
        p1c_preserve=true
        p1c_code=1
    fi
    if [[ "$p1c_preserve" == true ]]; then
        printf 'concurrent fixture evidence: %s\n' "$p1c_scratch" >&2
    else
        rm -rf -- "$p1c_scratch"
    fi
    exit "$p1c_code"
}
trap p1c_cleanup EXIT

p1c_fail() {
    printf 'FAIL concurrent fixture: %s\n' "$1" >&2
    p1c_preserve=true
    exit 1
}

p1c_pass() {
    p1c_passed=$((p1c_passed + 1))
    printf 'PASS %s\n' "$1"
}

p1c_require_functions() {
    local p1c_name
    for p1c_name in "$@"; do
        declare -F "$p1c_name" >/dev/null || p1c_fail "private core API missing: $p1c_name"
    done
}

p1c_make_fixture() {
    local p1c_root=$1 p1c_name
    mkdir -p -- "$p1c_root/bin" "$p1c_root/scripts" "$p1c_root/.p1c-state"
    cp -- "$p1c_script_dir/fast_concurrent.sh" "$p1c_root/scripts/fast_concurrent.sh"
    printf '%s\n' "$p1c_witness" > "$p1c_root/.p1c-state/witness"
    cat > "$p1c_root/scripts/.p1c-spy" <<'P1C_SPY'
#!/bin/bash
set -euo pipefail
p1c_name=${0##*/}
case "$p1c_name" in
    nauqc) p1c_group=0; [[ "$#" == 1 && "$1" == test ]] ;;
    check_seed_capture.sh|check_m54_10_provenance.sh) p1c_group=1; [[ "$#" == 0 ]] ;;
    check_attestation_batch.sh|check_m54_10_attestation.sh) p1c_group=2; [[ "$#" == 0 ]] ;;
    check_run_budgeted.sh) p1c_group=3; [[ "$#" == 0 ]] ;;
    *) exit 81 ;;
esac
p1c_root="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
p1c_state="$p1c_root/.p1c-state"
printf '%s.begin\n' "$p1c_name" >> "$p1c_state/trace.$p1c_group"
case "$p1c_name" in
    nauqc|check_seed_capture.sh|check_attestation_batch.sh|check_run_budgeted.sh)
        : > "$p1c_state/arrived.$p1c_group"
        if [[ -e "$p1c_state/barrier" ]]; then
            p1c_deadline=$((SECONDS + 5))
            while [[ ! -e "$p1c_state/arrived.0" || ! -e "$p1c_state/arrived.1" ||
                     ! -e "$p1c_state/arrived.2" || ! -e "$p1c_state/arrived.3" ]]; do
                (( SECONDS < p1c_deadline )) || exit 82
                /bin/sleep 0.01
            done
            : > "$p1c_state/overlapped.$p1c_group"
        fi
        ;;
esac
if [[ "$p1c_name" == nauqc && -e "$p1c_state/exec" ]]; then
    IFS= read -r p1c_witness < "$p1c_state/witness"
    exec 3>"$p1c_state/environment.fifo" 4>"$p1c_state/arguments.fifo"
    exec "$p1c_witness" exec "$@" '' 'space value' 'literal$dollar' 'both'"'"'"quotes' 'back\slash' $'line\nvalue'
fi
if [[ "$p1c_name" == nauqc && -e "$p1c_state/detached" ]]; then
    IFS= read -r p1c_witness < "$p1c_state/witness"
    /usr/bin/setsid "$p1c_witness" allocate "$p1c_state/allocated" \
        0<&- 1>&- 2>&- 3>&- 4>&- &
    printf '%s\n' "$!" > "$p1c_state/detached.pid"
    p1c_deadline=$((SECONDS + 5))
    until [[ -s "$p1c_state/allocated" ]]; do
        (( SECONDS < p1c_deadline )) || exit 83
        /bin/sleep 0.01
    done
fi
printf 'stdout:%s\n' "$p1c_name"
printf 'stderr:%s\n' "$p1c_name" >&2
if [[ "$p1c_name" == nauqc && -e "$p1c_state/slow-first" ]]; then /bin/sleep 0.1; fi
if [[ -e "$p1c_state/overflow" && "$p1c_name" == nauqc ]]; then
    /usr/bin/head -c 8388609 /dev/zero
fi
printf '%s.end\n' "$p1c_name" >> "$p1c_state/trace.$p1c_group"
p1c_code=0
[[ ! -f "$p1c_state/exit.$p1c_name" ]] || IFS= read -r p1c_code < "$p1c_state/exit.$p1c_name"
[[ "$p1c_code" =~ ^(0|[1-9][0-9]{0,2})$ ]] && (( p1c_code <= 255 )) || exit 84
exit "$p1c_code"
P1C_SPY
    chmod 755 "$p1c_root/scripts/.p1c-spy"
    cp -- "$p1c_root/scripts/.p1c-spy" "$p1c_root/bin/nauqc"
    for p1c_name in check_seed_capture check_m54_10_provenance check_attestation_batch check_m54_10_attestation check_run_budgeted; do
        cp -- "$p1c_root/scripts/.p1c-spy" "$p1c_root/scripts/$p1c_name.sh"
    done
}

p1c_expected_output() {
    local p1c_name
    for p1c_name in nauqc check_seed_capture.sh check_m54_10_provenance.sh check_attestation_batch.sh check_m54_10_attestation.sh check_run_budgeted.sh; do
        printf 'stdout:%s\nstderr:%s\n' "$p1c_name" "$p1c_name"
    done
}

p1c_assert_order() {
    local p1c_root=$1 p1c_group p1c_name
    for p1c_group in 0 1 2 3; do
        : > "$p1c_scratch/expected.trace"
        case "$p1c_group" in
            0) set -- nauqc ;;
            1) set -- check_seed_capture.sh check_m54_10_provenance.sh ;;
            2) set -- check_attestation_batch.sh check_m54_10_attestation.sh ;;
            3) set -- check_run_budgeted.sh ;;
        esac
        for p1c_name in "$@"; do
            printf '%s.begin\n%s.end\n' "$p1c_name" "$p1c_name" >> "$p1c_scratch/expected.trace"
        done
        cmp -s "$p1c_scratch/expected.trace" "$p1c_root/.p1c-state/trace.$p1c_group" || return 1
        [[ -e "$p1c_root/.p1c-state/overlapped.$p1c_group" ]] || return 1
    done
}

p1c_environment_case() (
    local p1c_label=$1 p1c_role=$2 p1c_expected=$3 p1c_status=0 p1c_writer p1c_fd
    shift 3
    if [[ "$p1c_label" == unterminated ]]; then
        exec {p1c_fd}< <(printf '%s' "$*")
    else
        exec {p1c_fd}< <(printf '%s\0' "$@")
    fi
    p1c_writer=$!
    _nqfc_validate_environment "/proc/self/fd/$p1c_fd" "$p1c_role" || p1c_status=$?
    exec {p1c_fd}<&-
    wait "$p1c_writer" || return 1
    if [[ "$p1c_expected" == accept ]]; then [[ "$p1c_status" == 0 ]];
    else [[ "$p1c_status" != 0 ]]; fi || return 1
)

p1c_environment_cases() {
    local p1c_name
    p1c_require_functions _nqfc_validate_environment
    p1c_environment_case values waiter accept 'PATH=/usr/bin:/bin' 'EMPTY=' $'NEWLINE=first\nsecond' 'DOLLAR=$literal' ||
        p1c_fail 'legal ordered environment values'
    p1c_pass 'UNIT legal empty/newline/literal-dollar environment values'
    for p1c_name in INVOCATION_ID _nqfc_private BASH_ENV ENV SHELLOPTS BASHOPTS \
        BASH_REMATCH BASH_XTRACEFD CDPATH GLOBIGNORE IFS 'BASH_FUNC_example%%'; do
        p1c_environment_case "$p1c_name" waiter reject 'PATH=/usr/bin:/bin' "$p1c_name=" ||
            p1c_fail "unsupported empty environment key $p1c_name"
        p1c_pass "UNIT reject empty unsupported key $p1c_name"
    done
    p1c_environment_case duplicate waiter reject 'PATH=/usr/bin:/bin' 'DUP=a' 'DUP=b' ||
        p1c_fail 'synthetic duplicate environment entries'
    p1c_pass 'UNIT synthetic duplicate entries, not live execve injection'
    for p1c_name in '=empty-key' 'NO_EQUALS' '9BAD=value' 'BAD-KEY=value'; do
        p1c_environment_case malformed waiter reject 'PATH=/usr/bin:/bin' "$p1c_name" ||
            p1c_fail 'malformed synthetic environment entry'
    done
    p1c_pass 'UNIT malformed/nonidentifier environment entries'
    p1c_environment_case unterminated waiter reject 'PATH=/usr/bin:/bin' ||
        p1c_fail 'missing terminal environment NUL'
    p1c_environment_case empty waiter reject '' || p1c_fail 'empty environment record'
    p1c_environment_case role invalid reject 'PATH=/usr/bin:/bin' || p1c_fail 'unknown environment role'
    p1c_pass 'UNIT missing terminal NUL/empty record/unknown role reject'
    p1c_environment_case injected scope accept 'PATH=/usr/bin:/bin' \
        'INVOCATION_ID=0123456789abcdef0123456789abcdef' || p1c_fail 'scope-only injected key domain'
    if (set -a; _nqfc_reject_reserved); then p1c_fail 'allexport shell state accepted'; fi
    p1c_pass 'UNIT injected key belongs only to scope; allexport rejects'
}

p1c_event_cases() {
    local p1c_text
    p1c_require_functions _nqfc_parse_events
    _nqfc_parse_events $'populated 1\nfrozen 0\n' || p1c_fail 'live event framing'
    [[ "$_nqfc_populated" == 1 && "$_nqfc_frozen" == 0 ]] || p1c_fail 'live event values'
    _nqfc_parse_events $'populated 0\nfrozen 1\n' || p1c_fail 'frozen event framing'
    [[ "$_nqfc_populated" == 0 && "$_nqfc_frozen" == 1 ]] || p1c_fail 'frozen event values'
    p1c_pass 'UNIT pinned-event populated/frozen states'
    for p1c_text in '' $'populated 1\n' $'populated 2\nfrozen 0\n' \
        $'populated 1\nfrozen 0\nfrozen 1\n' $'populated 1\nfrozen 0\nextra 0\n'; do
        if _nqfc_parse_events "$p1c_text"; then p1c_fail 'malformed event framing accepted'; fi
    done
    p1c_pass 'UNIT missing/duplicate/malformed cgroup event rows reject'
}

p1c_join() {
    local p1c_pid=$1 p1c_at
    p1c_join_status=0
    wait "$p1c_pid" || p1c_join_status=$?
    for p1c_at in "${!p1c_pending[@]}"; do
        [[ "${p1c_pending[p1c_at]}" != "$p1c_pid" ]] || unset 'p1c_pending[p1c_at]'
    done
}

p1c_group_case() {
    local p1c_label=$1 p1c_first=$2 p1c_second=$3 p1c_expected=$4
    local p1c_root="$p1c_scratch/groups-$p1c_label" p1c_group
    local -a p1c_handles=() p1c_status=()
    p1c_make_fixture "$p1c_root"
    : > "$p1c_root/.p1c-state/barrier"
    [[ "$p1c_first" == 0 ]] || printf '%s\n' "$p1c_first" > "$p1c_root/.p1c-state/exit.nauqc"
    [[ "$p1c_second" == 0 ]] || printf '%s\n' "$p1c_second" > "$p1c_root/.p1c-state/exit.check_run_budgeted.sh"
    [[ "$p1c_label" != ordered-nonzero ]] || : > "$p1c_root/.p1c-state/slow-first"
    for p1c_group in 0 1 2 3; do
        (_nqfc_provider_group "$p1c_root" "$p1c_group") \
            > "$p1c_root/output.$p1c_group" 2>&1 &
        p1c_handles+=("$!")
        p1c_pending+=("$!")
    done
    for p1c_group in 0 1 2 3; do
        p1c_join "${p1c_handles[p1c_group]}"
        p1c_status+=("$p1c_join_status")
    done
    [[ "${p1c_status[*]}" == "$p1c_expected" ]] || p1c_fail "actual spy statuses $p1c_label"
    p1c_assert_order "$p1c_root" || p1c_fail "overlap/original intra-group order $p1c_label"
    p1c_expected_output > "$p1c_root/expected"
    cat -- "$p1c_root/output.0" "$p1c_root/output.1" "$p1c_root/output.2" "$p1c_root/output.3" > "$p1c_root/replayed"
    cmp -s "$p1c_root/expected" "$p1c_root/replayed" || p1c_fail "fixed spy stream order $p1c_label"
    p1c_pass "UNIT actual fixed group bodies overlap and join: $p1c_label"
}

p1c_group_cases() {
    p1c_require_functions _nqfc_provider_group
    p1c_group_case success 0 0 '0 0 0 0'
    p1c_group_case ordered-nonzero 7 3 '7 0 0 3'
    p1c_group_case command124 124 0 '124 0 0 0'
    p1c_group_case command137 137 0 '137 0 0 0'
}

p1c_manager_rows() {
    printf '%s\n' \
        'ManagerVersion=255.4-1ubuntu8.18' \
        "Id=$_nqfc_unit" "Description=nq-fast-concurrent:$_nqfc_nonce" \
        'LoadState=loaded' 'ActiveState=active' 'SubState=running' 'Transient=yes' \
        'InvocationID=0123456789abcdef0123456789abcdef' \
        "ControlGroup=/unit-model/$_nqfc_unit" 'MemoryMax=536870912' 'MemorySwapMax=0' \
        'OOMPolicy=kill' 'KillMode=control-group' 'SendSIGKILL=yes' \
        'RuntimeMaxUSec=5min' 'TimeoutStopUSec=5s' \
        'CPUQuotaPerSecUSec=4s' 'TasksMax=256' 'Result=success'
}

p1c_manager_cases() (
    local _nqfc_unit=nq-concurrent-fixture.scope _nqfc_nonce=fixture-nonce _nqfc_uuid_bound=''
    local -A _nqfc_manager=()
    local p1c_rows p1c_bad p1c_setting p1c_key p1c_line p1c_reply
    p1c_rows="$(p1c_manager_rows)"$'\n'
    _nqfc_parse_manager "$p1c_rows" || return 1
    p1c_reply=$p1c_rows
    _nqfc_provider_manager() { printf '%s' "$p1c_reply"; }
    _nqfc_check_manager || return 1
    for p1c_setting in MemoryMax=536870911 MemorySwapMax=1 OOMPolicy=continue \
        KillMode=process SendSIGKILL=no RuntimeMaxUSec=6min TimeoutStopUSec=6s \
        CPUQuotaPerSecUSec=5s TasksMax=infinity Result=oom-kill \
        Transient=no InvocationID=00000000000000000000000000000000; do
        p1c_key=${p1c_setting%%=*}
        p1c_bad=''
        while IFS= read -r p1c_line; do
            if [[ "$p1c_line" == "$p1c_key="* ]]; then p1c_bad+="$p1c_setting"$'\n';
            else p1c_bad+="$p1c_line"$'\n'; fi
        done <<< "${p1c_rows%$'\n'}"
        if _nqfc_parse_manager "$p1c_bad"; then return 1; fi
    done
    if _nqfc_parse_manager "$p1c_rows"$'TasksMax=256\n'; then return 1; fi
    # All client-side assumptions and other fields stay at the supported baseline.
    # The independently observed running manager version must still reject.
    for p1c_setting in ManagerVersion=256.1 ManagerVersion=255.4-1ubuntu8.17 \
        ManagerVersion=255.4 ManagerVersion= ManagerVersion=255.4-1ubuntu8.18-extra; do
        p1c_bad=''
        while IFS= read -r p1c_line; do
            if [[ "$p1c_line" == ManagerVersion=* ]]; then p1c_bad+="$p1c_setting"$'\n';
            else p1c_bad+="$p1c_line"$'\n'; fi
        done <<< "${p1c_rows%$'\n'}"
        if _nqfc_parse_manager "$p1c_bad"; then return 1; fi
        p1c_reply=$p1c_bad
        if _nqfc_check_manager; then return 1; fi
    done
    p1c_bad=''
    while IFS= read -r p1c_line; do
        [[ "$p1c_line" == ManagerVersion=* ]] || p1c_bad+="$p1c_line"$'\n'
    done <<< "${p1c_rows%$'\n'}"
    if _nqfc_parse_manager "$p1c_bad"; then return 1; fi
    p1c_reply=$p1c_bad
    if _nqfc_check_manager; then return 1; fi
    if _nqfc_parse_manager "$p1c_rows"$'ManagerVersion=255.4-1ubuntu8.18\n'; then return 1; fi
    _nqfc_provider_manager() { printf '%s' "$p1c_rows"; return 7; }
    if _nqfc_check_manager; then return 1; fi
)

p1c_manager_version_cases() (
    local _nqfc_text='' p1c_version=$'255.4-1ubuntu8.18\n' p1c_query_status=0
    _nqfc_provider_manager_version() {
        printf '%s' "$p1c_version"
        return "$p1c_query_status"
    }
    _nqfc_check_manager_version || return 1
    [[ $_nqfc_text == $'255.4-1ubuntu8.18\n' ]] || return 1
    for p1c_version in $'256.1\n' $'255.4-1ubuntu8.17\n' '' \
        '255.4-1ubuntu8.18' $'255.4-1ubuntu8.18\n\n' $'255.4-1ubuntu8.18\nextra\n'; do
        if _nqfc_check_manager_version; then return 1; fi
    done
    p1c_version=$'255.4-1ubuntu8.18\n'
    p1c_query_status=7
    if _nqfc_check_manager_version; then return 1; fi
    [[ -z $_nqfc_text ]]
)

p1c_manager_version_entry_order() {
    local p1c_prepare p1c_run p1c_provider p1c_before p1c_after
    p1c_prepare="$(declare -f _nqfc_prepare)" || return 1
    p1c_run="$(declare -f _nqfc_run)" || return 1
    p1c_provider="$(declare -f _nqfc_provider_manager)" || return 1
    (( ${#p1c_prepare} <= 16384 && ${#p1c_run} <= 32768 && ${#p1c_provider} <= 4096 )) || return 1
    # STATIC definition-order checks only: never execute prepare, bypass its
    # EUID guard, or invoke a real provider in the default UNIT/STUB fixture.
    [[ $p1c_prepare == *'/usr/bin/systemd-run --version'*'systemd 255 (255.4-1ubuntu8.18)'*'_nqfc_check_manager_version || return 1'* ]] || return 1
    p1c_before=${p1c_prepare%%'_nqfc_check_manager_version || return 1'*}
    p1c_after=${p1c_prepare#*'_nqfc_check_manager_version || return 1'}
    [[ $p1c_after == *'is-system-running'*'/usr/bin/mktemp -d'*'_nqfc_unit='* ]] || return 1
    [[ $p1c_before != *is-system-running* && $p1c_before != */usr/bin/mktemp* &&
       $p1c_before != *'_nqfc_unit='* && $p1c_after != *'_nqfc_check_manager_version'* &&
       $p1c_prepare != *'_nqfc_provider_launch'* ]] || return 1
    [[ $p1c_run == *'_nqfc_prepare || return 125'*'_nqfc_provider_launch '* ]] || return 1
    p1c_before=${p1c_run%%'_nqfc_prepare || return 125'*}
    [[ $p1c_before != *'_nqfc_provider_launch'* ]] || return 1
    [[ $p1c_provider == *'_nqfc_check_manager_version || return 1'*'ManagerVersion=%s'* ]] || return 1
    p1c_before=${p1c_provider%%'_nqfc_check_manager_version || return 1'*}
    [[ $p1c_before != *'/usr/bin/systemctl'* && $p1c_before != *'ManagerVersion=%s'* ]]
}

p1c_capture_cases() (
    local _nqfc_text='' p1c_writer
    p1c_writer() { printf 'valid-prefix\n'; return 7; }
    if _nqfc_capture 32 p1c_writer; then return 1; fi
    [[ -z "$_nqfc_text" ]] || return 1
    p1c_writer() { printf 'oversized metadata'; }
    if _nqfc_capture 4 p1c_writer; then return 1; fi
    [[ -z "$_nqfc_text" ]] || return 1
    p1c_writer() { printf 'complete\n'; }
    _nqfc_capture 9 p1c_writer || return 1
    [[ "$_nqfc_text" == $'complete\n' ]]
)

p1c_wait_cases() (
    local p1c_code p1c_child p1c_parent=$BASHPID p1c_calls=0
    local _nqfc_wait_status _nqfc_signal_epoch=0
    for p1c_code in 0 7 124 137; do
        (exit "$p1c_code") &
        p1c_child=$!
        _nqfc_wait_handle "$p1c_child" || return 1
        [[ "$_nqfc_wait_status" == "$p1c_code" ]] || return 1
    done
    trap '_nqfc_signal_epoch=$((_nqfc_signal_epoch + 1))' USR1
    wait() {
        p1c_calls=$((p1c_calls + 1))
        : > "$p1c_scratch/wait-entered"
        builtin wait "$@"
    }
    (
        until [[ -e "$p1c_scratch/wait-entered" ]]; do /bin/sleep 0.01; done
        kill -USR1 "$p1c_parent"
        /bin/sleep 0.03
        printf 'joined\n' > "$p1c_scratch/wait-finished"
        exit 137
    ) &
    p1c_child=$!
    _nqfc_wait_handle "$p1c_child" || return 1
    [[ "$_nqfc_wait_status" == 137 && "$_nqfc_signal_epoch" == 1 && "$p1c_calls" -ge 2 &&
       -s "$p1c_scratch/wait-finished" ]]
)

# Only provider outputs below are synthetic. The transaction, parsers, resource
# checks, deadline checks and ACK write are the sourceable production functions.
p1c_freeze_case() (
    local p1c_fault=$1 p1c_expected=$2 p1c_status=0 p1c_time p1c_step
    local p1c_model="$p1c_scratch/freeze-$p1c_fault"
    local _nqfc_unit=nq-concurrent-fixture.scope _nqfc_nonce=0123456789abcdef0123456789abcdef
    local _nqfc_uuid_bound=0123456789abcdef0123456789abcdef _nqfc_coordinator=555
    local _nqfc_cgroup=/unit-model/nq-concurrent-fixture.scope _nqfc_signal=0 _nqfc_now_cs=0 _nqfc_tx_end=0
    local _nqfc_oom_base='0 0 0' _nqfc_text='' _nqfc_peak='' _nqfc_oom=''
    local _nqfc_to_child _nqfc_frozen='' _nqfc_populated=''
    local -A _nqfc_manager=() _nqfc_fds=(
        [events]=901 [procs]=902 [dir]=903 [type]=904 [memory]=905 [swap]=906
        [oomgroup]=907 [tasks]=908 [cpu]=909 [peak]=910 [memoryevents]=911 [freeze]=912
    )
    mkdir "$p1c_model"
    local _nqfc_run="$p1c_model"
    printf '0\n' > "$p1c_model/clock"
    printf '0\n' > "$p1c_model/frozen"
    : > "$p1c_model/writes"
    exec {_nqfc_to_child}> "$p1c_model/ack"
    _nqfc_provider_now() {
        IFS= read -r p1c_time < "$p1c_model/clock"
        p1c_step=1
        [[ "$p1c_fault" != never-frozen ]] || p1c_step=25
        printf '%s\n' "$((p1c_time + p1c_step))" > "$p1c_model/clock"
        printf '%s\n' "$p1c_time"
    }
    _nqfc_provider_write() {
        [[ "$1" == 912 && ( "$2" == 0 || "$2" == 1 ) ]] || return 1
        printf '%s %s\n' "$1" "$2" >> "$p1c_model/writes"
        [[ "$p1c_fault" != freeze-write ]] || return 1
        [[ "$p1c_fault" != unfreeze-write || "$2" != 0 ]] || return 1
        if [[ "$p1c_fault" != never-frozen ]]; then printf '%s\n' "$2" > "$p1c_model/frozen"; fi
    }
    _nqfc_provider_pause() { :; }
    _nqfc_provider_manager() { p1c_manager_rows; }
    _nqfc_provider_children() {
        [[ "$1" == 903 ]] || return 1
        [[ "$p1c_fault" != descendant-cgroup ]] || printf 'd\n'
    }
    _nqfc_provider_read() {
        case "$1" in
            901)
                IFS= read -r p1c_time < "$p1c_model/frozen"
                printf 'populated 1\nfrozen %s\n' "$p1c_time"
                ;;
            902)
                printf '555\n'
                [[ "$p1c_fault" != surviving-member ]] || printf '777\n'
                ;;
            904) printf 'domain\n' ;;
            905) printf '536870912\n' ;;
            906) printf '0\n' ;;
            907) printf '1\n' ;;
            908) printf '256\n' ;;
            909) printf '400000 100000\n' ;;
            910)
                if [[ "$p1c_fault" == aggregate-peak ]]; then printf '536870913\n';
                else printf '4194304\n'; fi
                ;;
            911)
                printf 'low 0\nhigh 0\nmax 0\noom 0\n'
                if [[ "$p1c_fault" == oom || "$p1c_fault" == initial-oom ]]; then printf 'oom_kill 1\n';
                else printf 'oom_kill 0\n'; fi
                printf 'oom_group_kill 0\n'
                ;;
            *) return 1 ;;
        esac
    }
    _nqfc_freeze_transaction || p1c_status=$?
    exec {_nqfc_to_child}>&-
    if [[ "$p1c_expected" == accept ]]; then
        [[ "$p1c_status" == 0 && -s "$p1c_model/ack" && -s "$p1c_model/resources" ]] || return 1
        [[ "$(< "$p1c_model/writes")" == $'912 1\n912 0' ]] || return 1
        grep -Fxq 'aggregate_peak_bytes=4194304' "$p1c_model/resources" || return 1
    else
        [[ "$p1c_status" != 0 ]] || return 1
        if [[ "$p1c_fault" != unfreeze-write ]]; then [[ ! -s "$p1c_model/ack" ]] || return 1; fi
        if [[ "$p1c_fault" == never-frozen ]]; then
            IFS= read -r p1c_time < "$p1c_model/clock"
            (( p1c_time >= 500 && p1c_time <= 550 && _nqfc_tx_end == 500 )) || return 1
        fi
    fi
)

p1c_freeze_cases() {
    local p1c_fault
    p1c_require_functions _nqfc_freeze_transaction _nqfc_capture_resources
    p1c_freeze_case success accept || p1c_fail 'modeled complete freeze/ACK/unfreeze transaction'
    p1c_pass 'UNIT production freeze transaction, synthetic descriptor/resource provider'
    for p1c_fault in freeze-write never-frozen surviving-member descendant-cgroup aggregate-peak oom unfreeze-write; do
        p1c_freeze_case "$p1c_fault" reject || p1c_fail "freeze boundary $p1c_fault"
        p1c_pass "UNIT production freeze rejection: $p1c_fault"
    done
}

p1c_drain_case() (
    local p1c_fault=$1 p1c_expected=$2 p1c_model="$p1c_scratch/drain-$1" p1c_time
    local _nqfc_pinned=1 _nqfc_now_cs=0 _nqfc_text='' _nqfc_populated='' _nqfc_frozen=''
    local p1c_status=0
    local -A _nqfc_fds=([events]=901 [dir]=902)
    mkdir "$p1c_model"
    printf '0\n' > "$p1c_model/clock"
    _nqfc_provider_now() {
        IFS= read -r p1c_time < "$p1c_model/clock"
        printf '%s\n' "$((p1c_time + 50))" > "$p1c_model/clock"
        printf '%s\n' "$p1c_time"
    }
    _nqfc_provider_pause() { :; }
    _nqfc_provider_read() {
        case "$p1c_fault" in
            empty) printf 'populated 0\nfrozen 0\n' ;;
            live) printf 'populated 1\nfrozen 0\n' ;;
            retired|read-error) printf 'synthetic retired-node read failure\n' >&2; return 1 ;;
            malformed) printf 'not cgroup events\n' ;;
        esac
    }
    _nqfc_retired() { [[ "$p1c_fault" == retired ]]; }
    _nqfc_drain 2> "$p1c_model/drain.stderr" || p1c_status=$?
    if [[ "$p1c_expected" == accept ]]; then [[ "$p1c_status" == 0 ]];
    else [[ "$p1c_status" != 0 ]]; fi || return 1
    [[ "$p1c_fault" != retired || ! -s "$p1c_model/drain.stderr" ]] || return 1
    if [[ "$p1c_fault" == read-error ]]; then
        grep -Fqx 'check_fast concurrent: cgroup events unreadable without retirement proof' \
            "$p1c_model/drain.stderr" || return 1
    fi
    [[ "$p1c_fault" != live ]] || {
        IFS= read -r p1c_time < "$p1c_model/clock"
        (( p1c_time >= 500 && p1c_time <= 600 ))
    }
)

p1c_drain_cases() {
    local p1c_fault
    p1c_drain_case empty accept || p1c_fail 'modeled populated0 drain'
    p1c_drain_case retired accept || p1c_fail 'modeled verified old-node retirement'
    for p1c_fault in live read-error malformed; do
        p1c_drain_case "$p1c_fault" reject || p1c_fail "modeled fail-closed drain $p1c_fault"
    done
    p1c_pass 'UNIT actual drain predicate: empty/retired/live/deadline/observation failure (synthetic observations)'
}

p1c_fd_case() (
    local _nqfc_pinned=1 p1c_fd p1c_status=0
    local -A _nqfc_fds=()
    printf 'old\n' > "$p1c_scratch/old-control"
    exec {p1c_fd}> "$p1c_scratch/old-control"
    _nqfc_fds[kill]=$p1c_fd
    mv "$p1c_scratch/old-control" "$p1c_scratch/retained-control"
    printf 'replacement\n' > "$p1c_scratch/old-control"
    _nqfc_kill_owned || p1c_status=1
    _nqfc_pinned=0
    if _nqfc_kill_owned; then p1c_status=1; fi
    exec {p1c_fd}>&-
    [[ "$p1c_status" == 0 && "$(< "$p1c_scratch/retained-control")" == 1 &&
       "$(< "$p1c_scratch/old-control")" == replacement ]]
)

p1c_status_cases() (
    local _nqfc_nonce=0123456789abcdef0123456789abcdef _nqfc_producer=0 _nqfc_logger=0 p1c_record
    _nqfc_parse_status "nq-fast-status/v2 $_nqfc_nonce 2 124 0"$'\n' 2 || return 1
    [[ "$_nqfc_producer" == 124 && "$_nqfc_logger" == 0 ]] || return 1
    for p1c_record in \
        "nq-fast-status/v2 $_nqfc_nonce 2 137 0" \
        "nq-fast-status/v2 $_nqfc_nonce 2 0137 0"$'\n' \
        "nq-fast-status/v2 $_nqfc_nonce 1 137 0"$'\n' \
        "nq-fast-status/v2 $_nqfc_nonce 2 256 0"$'\n' \
        "nq-fast-status/v2 $_nqfc_nonce 2 137 0"$'\nextra\n' \
        "nq-fast-status/v2 00000000000000000000000000000000 2 137 0"$'\n'; do
        if _nqfc_parse_status "$p1c_record" 2; then return 1; fi
    done
)

# An explicit protocol peer models only the manager/kernel boundary. Its jobs,
# logger, status parser, waiter, freeze transaction, replay and cleanup use core.
p1c_run_model() (
    local p1c_fault=$1 p1c_root=$2 p1c_model="$2/.p1c-state/model" p1c_fd p1c_key p1c_stage=0
    mkdir -p "$p1c_model" "$p1c_root/build/verification/.check-fast-lock"
    printf '1\n' > "$p1c_model/populated"
    printf '0\n' > "$p1c_model/frozen"
    : > "$p1c_model/operations"
    _nqfc_prepare() {
        _nqfc_run="$p1c_root/build/verification/fast-concurrent.model"
        mkdir -m 700 "$_nqfc_run" || return 1
        _nqfc_unit=nq-fast-0123456789abcdef0123456789abcdef.scope
        _nqfc_nonce=0123456789abcdef0123456789abcdef
        _nqfc_now || return 1
        _nqfc_outer_end=$((_nqfc_now_cs + 1500))
    }
    _nqfc_bind() {
        [[ "$p1c_fault" != provider ]] || return 1
        _nqfc_check_manager || return 1
        for p1c_key in dir events procs type memory swap oomgroup tasks cpu peak memoryevents kill freeze; do
            : > "$p1c_model/$p1c_key"
            exec {p1c_fd}<> "$p1c_model/$p1c_key" || return 1
            _nqfc_fds[$p1c_key]=$p1c_fd
        done
        _nqfc_oom_base='0 0 0'
        _nqfc_pinned=1
        if [[ "$p1c_fault" == signal-before-go ]]; then _nqfc_on_signal 1; fi
    }
    _nqfc_provider_manager() { p1c_manager_rows; }
    _nqfc_provider_children() { :; }
    _nqfc_provider_read() {
        case "$1" in
            "${_nqfc_fds[events]}")
                printf 'populated %s\nfrozen %s\n' "$(< "$p1c_model/populated")" "$(< "$p1c_model/frozen")"
                ;;
            "${_nqfc_fds[procs]}") printf '%s\n' "$_nqfc_coordinator" ;;
            "${_nqfc_fds[type]}") printf 'domain\n' ;;
            "${_nqfc_fds[memory]}") printf '536870912\n' ;;
            "${_nqfc_fds[swap]}") printf '0\n' ;;
            "${_nqfc_fds[oomgroup]}") printf '1\n' ;;
            "${_nqfc_fds[tasks]}") printf '256\n' ;;
            "${_nqfc_fds[cpu]}") printf '400000 100000\n' ;;
            "${_nqfc_fds[peak]}") printf '4194304\n' ;;
            "${_nqfc_fds[memoryevents]}") printf 'low 0\nhigh 0\nmax 0\noom 0\noom_kill 0\noom_group_kill 0\n' ;;
            *) return 1 ;;
        esac
    }
    _nqfc_provider_write() {
        printf '%s %s\n' "$1" "$2" >> "$p1c_model/operations"
        case "$1" in
            "${_nqfc_fds[freeze]}") printf '%s\n' "$2" > "$p1c_model/frozen" ;;
            "${_nqfc_fds[kill]}") printf '0\n' > "$p1c_model/populated" ;;
            *) return 1 ;;
        esac
    }
    _nqfc_provider_launch() (
        local _nqfc_root=$1 _nqfc_run=$2 _nqfc_unit=$3 _nqfc_nonce=$4
        local _nqfc_index _nqfc_wait_status=0 _nqfc_signal_epoch=0 p1c_peer_code=0 p1c_go
        local -a p1c_jobs=() p1c_codes=(0 0 0 0)
        trap 'printf "0\n" > "$p1c_model/populated"' EXIT
        [[ "$p1c_fault" != launch ]] || exit 7
        printf 'READY %s %s %s /unit-model/%s 1 1\n' "$_nqfc_nonce" "$_nqfc_nonce" "$BASHPID" "$_nqfc_unit"
        IFS= read -r -t 5 p1c_go || exit 125
        [[ "$p1c_go" == "GO $_nqfc_nonce $_nqfc_nonce" ]] || exit 125
        for _nqfc_index in 0 1 2 3; do
            [[ "$p1c_fault" != partial || "$_nqfc_index" != 2 ]] || break
            _nqfc_worker "$_nqfc_index" &
            p1c_jobs+=("$!")
        done
        for _nqfc_index in "${!p1c_jobs[@]}"; do
            _nqfc_wait_handle "${p1c_jobs[_nqfc_index]}" || exit 125
            p1c_codes[_nqfc_index]=$_nqfc_wait_status
            if (( p1c_peer_code == 0 && _nqfc_wait_status != 0 )); then p1c_peer_code=$_nqfc_wait_status; fi
        done
        [[ "$p1c_fault" != partial ]] || exit 7
        [[ "$p1c_fault" != missing-status ]] || rm -- "$_nqfc_run/group-1.status"
        if [[ "$p1c_fault" == malformed-status ]]; then
            printf 'stale nonce and malformed status\n' > "$_nqfc_run/group-2.status"
        fi
        printf 'FINISHED %s %s %s %s %s %s\n' "$_nqfc_nonce" "$_nqfc_nonce" "${p1c_codes[@]}"
        IFS= read -r -t 5 p1c_go || exit 125
        [[ "$p1c_go" == "ACK $_nqfc_nonce $_nqfc_nonce" ]] || exit 125
        exit "$p1c_peer_code"
    )
    if [[ "$p1c_fault" == capture ]]; then
        p1c_save_function _nqfc_logger_run p1c_logger_core
        _nqfc_logger_run() { p1c_logger_core /dev/full; }
    fi
    eval "$(declare -f _nqfc_read_control | sed '1s/_nqfc_read_control/p1c_read_control_core/')"
    _nqfc_read_control() {
        p1c_stage=$((p1c_stage + 1))
        if [[ "$p1c_fault" == signal-after-go && "$p1c_stage" == 2 ]]; then _nqfc_on_signal 15; fi
        p1c_read_control_core "$@" || return 1
        if [[ "$_nqfc_line" == FINISHED* ]]; then
            if [[ "$p1c_fault" == signal-finish ]]; then _nqfc_on_signal 2; fi
        fi
    }
    _nqfc_release_tier_lock() {
        [[ -z "$_nqfc_launcher" && "$_nqfc_drained" == 1 && "${#_nqfc_fds[@]}" == 0 ]] || return 1
        printf 'waited-and-drained\n' > "$p1c_model/released"
        rmdir "$p1c_root/build/verification/.check-fast-lock"
    }
    if [[ "$p1c_fault" == replay ]]; then
        nq_fast_concurrent_run "$p1c_root" >/dev/full
    else
        nq_fast_concurrent_run "$p1c_root"
    fi
)

p1c_model_cases() {
    local p1c_case p1c_expected p1c_status p1c_root p1c_states
    for p1c_case in success ordered-nonzero command124 command137 launch provider partial \
        capture replay overflow missing-status malformed-status signal-before-go signal-after-go signal-finish; do
        p1c_root="$p1c_scratch/model-$p1c_case"
        p1c_make_fixture "$p1c_root"
        p1c_expected=125
        case "$p1c_case" in
            success) p1c_expected=0; : > "$p1c_root/.p1c-state/barrier" ;;
            ordered-nonzero)
                p1c_expected=7
                : > "$p1c_root/.p1c-state/slow-first"
                printf '7\n' > "$p1c_root/.p1c-state/exit.nauqc"
                printf '3\n' > "$p1c_root/.p1c-state/exit.check_run_budgeted.sh"
                ;;
            command124|command137)
                p1c_expected=${p1c_case#command}
                printf '%s\n' "$p1c_expected" > "$p1c_root/.p1c-state/exit.nauqc"
                ;;
            overflow) : > "$p1c_root/.p1c-state/overflow" ;;
            signal-before-go) p1c_expected=129 ;;
            signal-after-go) p1c_expected=143 ;;
            signal-finish)
                p1c_expected=130
                printf '7\n' > "$p1c_root/.p1c-state/exit.nauqc"
                ;;
        esac
        p1c_status=0
        p1c_run_model "$p1c_case" "$p1c_root" > "$p1c_root/stdout" 2> "$p1c_root/stderr" || p1c_status=$?
        [[ "$p1c_status" == "$p1c_expected" ]] || p1c_fail "production runner/model status $p1c_case"
        if [[ "$p1c_case" == success ]]; then
            p1c_assert_order "$p1c_root" || p1c_fail 'production worker overlap/original order'
            p1c_expected_output > "$p1c_root/expected"
            cmp -s "$p1c_root/expected" "$p1c_root/stdout" || p1c_fail 'production runner ordered replay'
        fi
        if [[ "$p1c_case" == launch || "$p1c_case" == provider || "$p1c_case" == signal-before-go ]]; then
            [[ ! -e "$p1c_root/.p1c-state/arrived.0" ]] || p1c_fail "pre-GO payload launched: $p1c_case"
        else
            [[ -f "$p1c_root/.p1c-state/model/released" ]] || p1c_fail "true launcher wait/drain/FD closure: $p1c_case"
        fi
        if [[ "$p1c_case" == partial ]]; then
            [[ ! -e "$p1c_root/.p1c-state/arrived.2" && ! -e "$p1c_root/.p1c-state/arrived.3" ]] ||
                p1c_fail 'partial start launched later groups'
        fi
        p1c_pass "UNIT production runner with synthetic scope peer: $p1c_case"
    done
}

p1c_save_function() {
    eval "$(declare -f "$1" | sed "1s/$1/$2/")"
}

p1c_native_replacement() {
    local p1c_old_uuid=$_nqfc_uuid_bound p1c_old_inode=$_nqfc_inode
    local p1c_replacement_run="$_nqfc_root/build/verification/fast-concurrent.replacement"
    local p1c_nonce=abcdef0123456789abcdef0123456789 p1c_pid p1c_read='' p1c_write=''
    local p1c_original_read p1c_original_write p1c_line p1c_tag p1c_seen_nonce p1c_uuid
    local p1c_coordinator p1c_cgroup p1c_device p1c_inode p1c_extra p1c_deadline=$((SECONDS + 2))
    local p1c_good=1 p1c_code=0
    local -a p1c_replacement=()
    until _nqfc_retired; do
        (( SECONDS < p1c_deadline )) || return 1
        /bin/sleep 0.01
    done
    mkdir -m 700 "$p1c_replacement_run" || return 1
    printf 'nq-fast-lease/v2\n%s\n%s\n%s\n' "$p1c_nonce" "$_nqfc_unit" "$_nqfc_root" \
        > "$p1c_replacement_run/lease" || return 1
    coproc p1c_replacement {
        _nqfc_provider_launch "$_nqfc_root" "$p1c_replacement_run" "$_nqfc_unit" "$p1c_nonce" 2>&1
    }
    p1c_pid=$!
    p1c_original_read=${p1c_replacement[0]-} p1c_original_write=${p1c_replacement[1]-}
    if [[ -z "$p1c_original_read" || -z "$p1c_original_write" ]] ||
        ! exec {p1c_read}<&"$p1c_original_read" {p1c_write}>&"$p1c_original_write"; then
        [[ -z "$p1c_original_write" ]] || exec {p1c_original_write}>&-
        [[ -z "$p1c_original_read" ]] || exec {p1c_original_read}<&-
        _nqfc_wait_handle "$p1c_pid" || :
        return 1
    fi
    exec {p1c_original_read}<&- {p1c_original_write}>&- || p1c_good=0
    IFS= read -r -t 10 -u "$p1c_read" p1c_line || p1c_good=0
    read -r p1c_tag p1c_seen_nonce p1c_uuid p1c_coordinator p1c_cgroup p1c_device p1c_inode p1c_extra <<< "$p1c_line"
    [[ "$p1c_tag" == READY && "$p1c_seen_nonce" == "$p1c_nonce" && -z "$p1c_extra" &&
       "$p1c_uuid" != "$p1c_old_uuid" && "$p1c_inode" != "$p1c_old_inode" &&
       "$p1c_cgroup" == "$_nqfc_cgroup" ]] || p1c_good=0
    if [[ "$p1c_good" == 1 ]]; then
        # The old WRITE-ONLY capability must fail, never address the replacement.
        if p1c_write_core "${_nqfc_fds[kill]}" 1 2>/dev/null; then p1c_good=0; fi
        (
            local _nqfc_nonce=$p1c_nonce _nqfc_uuid_bound=''
            local -A _nqfc_manager=()
            _nqfc_check_manager &&
                [[ "${_nqfc_manager[InvocationID]}" == "$p1c_uuid" ]]
        ) || p1c_good=0
    fi
    # Never GO, stop or signal the replacement. EOF ends its bounded entry read.
    exec {p1c_write}>&- {p1c_read}<&-
    _nqfc_wait_handle "$p1c_pid" || p1c_good=0
    [[ "$_nqfc_wait_status" == 125 ]] || p1c_good=0
    [[ "$p1c_good" == 1 ]] || return 1
    printf 'old-fd-refused-new-inode-live-and-reaped\n' > "$p1c_state/replacement"
}

p1c_native_collision() {
    local p1c_run="$_nqfc_root/build/verification/fast-concurrent.collision"
    local p1c_nonce=abcdef0123456789abcdef0123456789 p1c_first_read p1c_first_write
    local p1c_line p1c_tag p1c_seen_nonce p1c_cg p1c_dev p1c_ino p1c_extra
    local -a p1c_collision=()
    mkdir -m 700 "$p1c_run" || return 1
    printf 'nq-fast-lease/v2\n%s\n%s\n%s\n' "$p1c_nonce" "$_nqfc_unit" "$_nqfc_root" > "$p1c_run/lease" || return 1
    coproc p1c_collision { _nqfc_provider_launch "$_nqfc_root" "$p1c_run" "$_nqfc_unit" "$p1c_nonce" 2>&1; }
    p1c_collision_pid=$!
    p1c_first_read=${p1c_collision[0]-} p1c_first_write=${p1c_collision[1]-}
    if [[ -z "$p1c_first_read" || -z "$p1c_first_write" ]] ||
        ! exec {p1c_collision_read}<&"$p1c_first_read" {p1c_collision_write}>&"$p1c_first_write"; then
        p1c_wait_core "$p1c_collision_pid" || :
        p1c_collision_pid=''
        return 1
    fi
    exec {p1c_first_read}<&- {p1c_first_write}>&-
    IFS= read -r -t 10 -u "$p1c_collision_read" p1c_line || return 1
    read -r p1c_tag p1c_seen_nonce p1c_collision_uuid p1c_collision_coordinator \
        p1c_cg p1c_dev p1c_ino p1c_extra <<< "$p1c_line"
    [[ "$p1c_tag" == READY && "$p1c_seen_nonce" == "$p1c_nonce" && -z "$p1c_extra" ]]
}

# These wrappers retain the actual provider and scope entry. Faults are injected
# in this disposable waiter only, never through a production environment knob.
p1c_native_waiter() {
    local p1c_fault=$1 p1c_root=$2 p1c_stage=0 p1c_status=0 p1c_child p1c_stdio p1c_child_stat
    local p1c_collision_pid='' p1c_collision_read='' p1c_collision_write=''
    local p1c_collision_uuid='' p1c_collision_coordinator=''
    local p1c_state="$2/.p1c-state"
    cd -- "$p1c_root"
    if [[ "$p1c_fault" == direct-exec ]]; then
        /bin/bash -p -c '
            source "$1"
            _nqfc_root=$2
            _nqfc_run=$3
            _nqfc_nonce=0123456789abcdef0123456789abcdef
            _nqfc_worker 0
        ' nq-fast-direct "$p1c_root/scripts/fast_concurrent.sh" "$p1c_root" \
            "$p1c_root/build/verification/direct-exec"
        return $?
    fi
    mkdir -p build/verification/.check-fast-lock
    p1c_save_function _nqfc_prepare p1c_prepare_core
    p1c_save_function _nqfc_bind p1c_bind_core
    p1c_save_function _nqfc_read_control p1c_read_control_core
    p1c_save_function _nqfc_freeze_transaction p1c_freeze_core
    p1c_save_function _nqfc_provider_write p1c_write_core
    p1c_save_function _nqfc_members_only p1c_members_core
    p1c_save_function _nqfc_capture_resources p1c_resources_core
    p1c_save_function _nqfc_send_ack p1c_ack_core
    p1c_save_function _nqfc_drain p1c_drain_core
    p1c_save_function _nqfc_wait_handle p1c_wait_core
    p1c_save_function _nqfc_close_pins p1c_close_pins_core
    p1c_save_function _nqfc_provider_read p1c_read_core
    p1c_save_function _nqfc_provider_manager p1c_manager_core
    p1c_save_function _nqfc_on_exit p1c_exit_core
    _nqfc_prepare() {
        p1c_prepare_core || return 1
        printf '%s\n' "$_nqfc_run" > "$p1c_state/run-path"
        [[ "$p1c_fault" != capture ]] || mkdir "$_nqfc_run/group-0.log" || return 1
        [[ "$p1c_fault" != collision ]] || p1c_native_collision
    }
    _nqfc_bind() {
        if [[ "$p1c_fault" == before-go ]]; then
            kill -HUP "$BASHPID"
            return 1
        fi
        p1c_bind_core
    }
    _nqfc_read_control() {
        p1c_stage=$((p1c_stage + 1))
        if [[ "$p1c_fault" == after-go && "$p1c_stage" == 2 ]]; then kill -TERM "$BASHPID"; fi
        p1c_read_control_core "$@"
    }
    _nqfc_freeze_transaction() {
        [[ "$p1c_fault" != finish ]] || kill -INT "$BASHPID"
        p1c_freeze_core
    }
    _nqfc_provider_write() {
        if [[ "$1" == "${_nqfc_fds[freeze]-}" && "$2" == 1 &&
              "$p1c_fault" == never-frozen ]]; then
            printf 'freeze-write-returned-zero\n' >> "$p1c_state/injected"
            return 0
        fi
        p1c_write_core "$@"
    }
    _nqfc_provider_read() {
        if [[ "$1" == "${_nqfc_fds[memoryevents]-}" &&
              ( "$p1c_fault" == initial-oom || ( "$p1c_fault" == oom && "$_nqfc_frozen" == 1 ) ) ]]; then
            printf 'low 0\nhigh 0\nmax 0\noom 0\noom_kill 1\noom_group_kill 0\n'
        else
            p1c_read_core "$@"
        fi
    }
    _nqfc_provider_manager() {
        [[ "$p1c_fault" != provider-loss || "$_nqfc_frozen" != 1 ]] || return 1
        p1c_manager_core "$@"
    }
    _nqfc_members_only() {
        if [[ "$p1c_fault" == detached && "$_nqfc_frozen" == 1 ]]; then
            IFS= read -r p1c_child < "$p1c_state/detached.pid" || return 1
            _nqfc_capture 4096 _nqfc_provider_read "${_nqfc_fds[procs]}" || return 1
            [[ $'\n'"$_nqfc_text" == *$'\n'"$p1c_child"$'\n'* ]] || return 1
            # Membership alone can include zombies; require a live child at frozen1.
            IFS= read -r p1c_child_stat < "/proc/$p1c_child/stat" || return 1
            [[ "$p1c_child_stat" == "$p1c_child ("*") "* ]] || return 1
            p1c_child_stat=${p1c_child_stat##*) }
            case "${p1c_child_stat%% *}" in R|S|D|T|t|I|P) ;; *) return 1 ;; esac
            for p1c_stdio in 0 1 2; do
                [[ ! -e "/proc/$p1c_child/fd/$p1c_stdio" && ! -L "/proc/$p1c_child/fd/$p1c_stdio" ]] || return 1
            done
            printf 'allocating-setsid-child-present-at-frozen1\n' > "$p1c_state/frozen-child"
        fi
        p1c_members_core
    }
    _nqfc_capture_resources() {
        printf 'capture-resources\n' >> "$p1c_state/resources-entry" || return 1
        p1c_resources_core "$@"
    }
    _nqfc_send_ack() {
        printf 'send-ack\n' >> "$p1c_state/ack-entry" || return 1
        p1c_ack_core "$@"
    }
    _nqfc_drain() {
        p1c_status=0
        p1c_drain_core || p1c_status=$?
        printf '%s\n' "$p1c_status" >> "$p1c_state/drain-status"
        return "$p1c_status"
    }
    _nqfc_wait_handle() {
        p1c_wait_core "$@" || return 1
        printf '%s\n' "$_nqfc_wait_status" >> "$p1c_state/wait-status"
    }
    _nqfc_close_pins() {
        p1c_status=0
        if [[ "$p1c_fault" == replacement ]]; then p1c_native_replacement || p1c_status=1; fi
        p1c_close_pins_core || p1c_status=1
        return "$p1c_status"
    }
    _nqfc_on_exit() {
        if [[ -n "$p1c_collision_pid" ]]; then
            (
                local _nqfc_nonce=abcdef0123456789abcdef0123456789 _nqfc_uuid_bound=''
                local -A _nqfc_manager=()
                _nqfc_check_manager &&
                    [[ "${_nqfc_manager[InvocationID]}" == "$p1c_collision_uuid" ]]
            ) || _nqfc_infra=1
            exec {p1c_collision_write}>&- {p1c_collision_read}<&- || _nqfc_infra=1
            p1c_wait_core "$p1c_collision_pid" || _nqfc_infra=1
            [[ "$_nqfc_wait_status" == 125 ]] || _nqfc_infra=1
            p1c_collision_pid=''
            printf 'collision-survived-primary-refusal-no-GO-reaped\n' > "$p1c_state/collision"
        fi
        p1c_exit_core "$@"
    }
    _nqfc_release_tier_lock() {
        [[ -z "$_nqfc_launcher" && "$_nqfc_drained" == 1 && "${#_nqfc_fds[@]}" == 0 ]] || return 1
        printf 'actual-wait-drain-closed\n' > "$p1c_state/released"
        rmdir build/verification/.check-fast-lock
    }
    if [[ "$p1c_fault" == replay ]]; then nq_fast_concurrent_run "$p1c_root" >/dev/full;
    else nq_fast_concurrent_run "$p1c_root"; fi
}

p1c_write_native_waiter() {
    {
        printf '#!/bin/bash\nsource "$1"\nshift\n'
        declare -f p1c_save_function p1c_native_replacement p1c_native_collision p1c_native_waiter
        printf 'p1c_native_waiter "$@"\n'
    } > "$p1c_scratch/native-waiter.sh"
}

p1c_run_native() {
    /usr/bin/timeout --foreground --kill-after=1s 30s \
        /bin/bash -p "$p1c_scratch/native-waiter.sh" "$p1c_script_dir/fast_concurrent.sh" "$1" "$2"
}

p1c_native_cases() {
    local p1c_case p1c_root p1c_expected p1c_status p1c_started p1c_run p1c_phase_path
    for p1c_case in success before-go after-go finish capture replay overflow never-frozen detached initial-oom oom replacement provider-loss collision; do
        p1c_root="$p1c_scratch/native-$p1c_case"
        p1c_make_fixture "$p1c_root"
        p1c_expected=125
        case "$p1c_case" in
            success|replacement) p1c_expected=0; : > "$p1c_root/.p1c-state/barrier" ;;
            before-go) p1c_expected=129 ;;
            after-go) p1c_expected=143 ;;
            finish)
                p1c_expected=130
                printf '7\n' > "$p1c_root/.p1c-state/exit.nauqc"
                ;;
            detached) : > "$p1c_root/.p1c-state/detached" ;;
            overflow) : > "$p1c_root/.p1c-state/overflow" ;;
        esac
        p1c_started=$SECONDS
        p1c_status=0
        p1c_run_native "$p1c_case" "$p1c_root" > "$p1c_root/stdout" 2> "$p1c_root/stderr" || p1c_status=$?
        [[ "$p1c_status" == "$p1c_expected" ]] || p1c_fail "NATIVE disposable scope status $p1c_case"
        if [[ "$p1c_expected" == 0 ]]; then
            [[ ! -s "$p1c_root/stderr" ]] || p1c_fail "NATIVE successful retirement leaked stderr $p1c_case"
        fi
        (( SECONDS - p1c_started <= 30 )) || p1c_fail "NATIVE bounded completion $p1c_case"
        [[ -s "$p1c_root/.p1c-state/wait-status" ]] || p1c_fail "NATIVE actual launcher wait $p1c_case"
        if [[ "$p1c_case" == before-go || "$p1c_case" == initial-oom || "$p1c_case" == collision ]]; then
            [[ ! -e "$p1c_root/.p1c-state/arrived.0" ]] || p1c_fail 'NATIVE payload before GO'
        else
            grep -Fxq 0 "$p1c_root/.p1c-state/drain-status" || p1c_fail "NATIVE old-object drain $p1c_case"
            [[ -s "$p1c_root/.p1c-state/released" ]] || p1c_fail "NATIVE owned FD cleanup $p1c_case"
        fi
        if [[ "$p1c_case" == success ]]; then
            p1c_assert_order "$p1c_root" || p1c_fail 'NATIVE all four spies overlap/original order'
            p1c_expected_output > "$p1c_root/expected"
            cmp -s "$p1c_root/expected" "$p1c_root/stdout" || p1c_fail 'NATIVE ordered combined replay'
            IFS= read -r p1c_run < "$p1c_root/.p1c-state/run-path"
            grep -Fxq 'oom=0 0 0' "$p1c_run/resources" || p1c_fail 'NATIVE effective resource capture'
            grep -Fxq capture-resources "$p1c_root/.p1c-state/resources-entry" ||
                p1c_fail 'NATIVE positive resource phase spy not reached'
            grep -Fxq send-ack "$p1c_root/.p1c-state/ack-entry" ||
                p1c_fail 'NATIVE positive ACK phase spy not reached'
        fi
        if [[ "$p1c_case" == never-frozen ]]; then
            [[ -s "$p1c_root/.p1c-state/injected" ]] || p1c_fail 'NATIVE unacknowledged freeze fault not reached'
        fi
        if [[ "$p1c_case" == detached ]]; then
            [[ -s "$p1c_root/.p1c-state/allocated" && -s "$p1c_root/.p1c-state/frozen-child" ]] ||
                p1c_fail 'NATIVE detached closed-stdio allocation did not survive through frozen1'
            IFS= read -r p1c_run < "$p1c_root/.p1c-state/run-path"
            for p1c_phase_path in "$p1c_root/.p1c-state/resources-entry" "$p1c_root/.p1c-state/ack-entry" \
                "$p1c_run/resources" "$p1c_run/resources.tmp"; do
                [[ ! -e "$p1c_phase_path" && ! -L "$p1c_phase_path" ]] ||
                    p1c_fail 'NATIVE detached rejection reached resource capture/ACK or published resources'
            done
        fi
        if [[ "$p1c_case" == replacement ]]; then
            [[ -s "$p1c_root/.p1c-state/replacement" ]] || p1c_fail 'NATIVE retained old kill FD/replacement test not reached'
        fi
        if [[ "$p1c_case" == collision ]]; then
            [[ -s "$p1c_root/.p1c-state/collision" ]] || p1c_fail 'NATIVE live owned creation collision not reached'
        fi
        case "$p1c_case" in
            initial-oom|oom|never-frozen|provider-loss)
                p1c_pass "NATIVE real scope plus LABELED provider fault (not kernel OOM/freezer failure): $p1c_case" ;;
            *) p1c_pass "NATIVE real provider, disposable fixed-name spies: $p1c_case" ;;
        esac
    done
}

p1c_compare_exec_environment() {
    local p1c_byte p1c_octal p1c_char p1c_entry='' p1c_fd p1c_writer p1c_writer_status=0
    local p1c_at p1c_key p1c_key_order=1 p1c_shlvl=0 p1c_underscore=0 p1c_other=0 p1c_class
    local -a _nqfc_bytes=() p1c_scoped_environment=() p1c_compare_status=()
    if ! _nqfc_capture_bytes 1048576 /usr/bin/timeout --foreground --kill-after=1s 30s /usr/bin/cat -- "$1"; then
        printf 'NATIVE exec environment: bounded FIFO capture failed\n' >&2
        return 2
    fi
    if (( ${#_nqfc_bytes[@]} == 0 )) || [[ ${_nqfc_bytes[${#_nqfc_bytes[@]}-1]} != 0 ]]; then
        printf 'NATIVE exec environment: empty or unterminated NUL stream\n' >&2
        return 2
    fi
    for p1c_byte in "${_nqfc_bytes[@]}"; do
        if [[ "$p1c_byte" == 0 ]]; then
            p1c_scoped_environment+=("$p1c_entry")
            p1c_entry=''
        else
            printf -v p1c_octal '%03o' "$p1c_byte"
            printf -v p1c_char '%b' "\\$p1c_octal"
            p1c_entry+=$p1c_char
        fi
    done
    # Both streams stay in memory/pipes. Framing is checked before reconstruction;
    # cmp still decides exact equality before any value-free classification.
    exec {p1c_fd}< <(printf '%s\0' "${p1c_scoped_environment[@]}")
    p1c_writer=$!
    if printf '%s\0' "${p1c_environment[@]}" |
        /usr/bin/timeout --foreground --kill-after=1s 30s /usr/bin/cmp -s -- - "/proc/self/fd/$p1c_fd"; then
        p1c_compare_status=("${PIPESTATUS[@]}")
    else
        p1c_compare_status=("${PIPESTATUS[@]}")
    fi
    exec {p1c_fd}<&-
    wait "$p1c_writer" || p1c_writer_status=$?
    if [[ "${p1c_compare_status[1]}" == 0 && "${p1c_compare_status[0]}" == 0 && "$p1c_writer_status" == 0 ]]; then
        return 0
    fi
    if [[ "${p1c_compare_status[1]}" != 1 ]]; then
        printf 'NATIVE exec environment: comparison transport failed (producer=%s cmp=%s writer=%s)\n' \
            "${p1c_compare_status[0]}" "${p1c_compare_status[1]}" "$p1c_writer_status" >&2
        return 2
    fi
    if (( ${#p1c_environment[@]} != ${#p1c_scoped_environment[@]} )); then
        p1c_class=entry-count-difference
    else
        for p1c_at in "${!p1c_environment[@]}"; do
            p1c_key=${p1c_environment[p1c_at]%%=*}
            [[ "$p1c_key" == "${p1c_scoped_environment[p1c_at]%%=*}" ]] || p1c_key_order=0
            [[ "${p1c_environment[p1c_at]}" != "${p1c_scoped_environment[p1c_at]}" ]] || continue
            case "$p1c_key" in
                SHLVL) p1c_shlvl=1 ;;
                _) p1c_underscore=1 ;;
                *) p1c_other=1 ;;
            esac
        done
        if [[ "$p1c_key_order" == 0 ]]; then p1c_class=key-order-or-membership;
        elif [[ "$p1c_other" == 1 ]]; then p1c_class=other-value-difference;
        elif [[ "$p1c_shlvl" == 1 && "$p1c_underscore" == 1 ]]; then p1c_class=SHLVL-and-underscore-only;
        elif [[ "$p1c_shlvl" == 1 ]]; then
            p1c_class=SHLVL-only
            for p1c_at in "${!p1c_environment[@]}"; do
                [[ ${p1c_environment[p1c_at]} == SHLVL=* ]] || continue
                if [[ ${p1c_environment[p1c_at]#*=} =~ ^[0-9]{1,4}$ &&
                      ${p1c_scoped_environment[p1c_at]#*=} =~ ^[0-9]{1,4}$ ]]; then
                    if (( 10#${p1c_scoped_environment[p1c_at]#*=} == 10#${p1c_environment[p1c_at]#*=} + 1 )); then
                        p1c_class=SHLVL-only-scoped-one-interpreter-deeper
                    elif (( 10#${p1c_environment[p1c_at]#*=} == 10#${p1c_scoped_environment[p1c_at]#*=} + 1 )); then
                        p1c_class=SHLVL-only-direct-one-interpreter-deeper
                    fi
                fi
            done
        elif [[ "$p1c_underscore" == 1 ]]; then p1c_class=underscore-only;
        else p1c_class=unclassified-byte-difference; fi
    fi
    printf 'NATIVE exec environment: exact mismatch (%s); no keys or values disclosed\n' "$p1c_class" >&2
    return 1
}

p1c_native_exec_case() {
    local p1c_root="$p1c_scratch/native-exec" p1c_state p1c_data_fd p1c_reader p1c_argv_cmp
    local p1c_runner p1c_env_cmp p1c_good=1 p1c_run
    local p1c_runner_status p1c_reader_status p1c_argv_status p1c_environment_status
    local -a p1c_environment=()
    [[ ! ${P1C_ORACLE_EMPTY+x} && ! ${P1C_ORACLE_NEWLINE+x} && ! ${P1C_ORACLE_DOLLAR+x} ]] ||
        p1c_fail 'fixture environment key already owned by caller'
    export P1C_ORACLE_EMPTY='' P1C_ORACLE_NEWLINE=$'first\nsecond' P1C_ORACLE_DOLLAR='$literal'
    p1c_make_fixture "$p1c_root"
    p1c_state="$p1c_root/.p1c-state"
    mkdir -p "$p1c_root/build/verification/direct-exec"
    : > "$p1c_state/exec"
    mkfifo -m 600 "$p1c_state/environment.fifo" "$p1c_state/arguments.fifo"
    # Only fixed fixture literals, never caller environment, enter this file.
    printf '%s\0' "$p1c_witness" exec test '' 'space value' 'literal$dollar' \
        'both'"'"'"quotes' 'back\slash' $'line\nvalue' > "$p1c_state/arguments.expected"
    /usr/bin/timeout --foreground --kill-after=1s 30s /usr/bin/cmp -s -- \
        "$p1c_state/arguments.expected" "$p1c_state/arguments.fifo" &
    p1c_argv_cmp=$!; p1c_pending+=("$!")
    exec {p1c_data_fd}< <(/usr/bin/timeout --foreground --kill-after=1s 30s \
        /usr/bin/cat -- "$p1c_state/environment.fifo")
    p1c_reader=$!; p1c_pending+=("$!")
    (
        exec {p1c_data_fd}<&-
        # Match the scoped leg's launcher function, not a tail-exec-only route.
        p1c_run_native direct-exec "$p1c_root"
    ) > "$p1c_root/direct.stdout" 2> "$p1c_root/direct.stderr" &
    p1c_runner=$!; p1c_pending+=("$!")
    mapfile -d '' -t p1c_environment <&"$p1c_data_fd" || p1c_good=0
    exec {p1c_data_fd}<&-
    p1c_join "$p1c_runner"; p1c_runner_status=$p1c_join_status
    p1c_join "$p1c_reader"; p1c_reader_status=$p1c_join_status
    p1c_join "$p1c_argv_cmp"; p1c_argv_status=$p1c_join_status
    if [[ "$p1c_good" != 1 || "$p1c_runner_status" != 0 || "$p1c_reader_status" != 0 || "$p1c_argv_status" != 0 ]]; then
        printf 'NATIVE direct exec legs: capture=%s runner=%s environment-reader=%s argv-cmp=%s\n' \
            "$p1c_good" "$p1c_runner_status" "$p1c_reader_status" "$p1c_argv_status" >&2
        p1c_good=0
    fi
    [[ "$p1c_good" == 1 && "${#p1c_environment[@]}" -gt 0 &&
       ! -s "$p1c_root/direct.stdout" && ! -s "$p1c_root/direct.stderr" &&
       ! -s "$p1c_root/build/verification/direct-exec/group-0.log" ]] ||
        p1c_fail 'NATIVE equivalent direct worker/exec witness'

    /usr/bin/timeout --foreground --kill-after=1s 30s /usr/bin/cmp -s -- \
        "$p1c_state/arguments.expected" "$p1c_state/arguments.fifo" &
    p1c_argv_cmp=$!; p1c_pending+=("$!")
    (p1c_compare_exec_environment "$p1c_state/environment.fifo") &
    p1c_env_cmp=$!; p1c_pending+=("$!")
    p1c_run_native success "$p1c_root" > "$p1c_root/scoped.stdout" 2> "$p1c_root/scoped.stderr" &
    p1c_runner=$!; p1c_pending+=("$!")
    p1c_join "$p1c_runner"; p1c_runner_status=$p1c_join_status
    p1c_join "$p1c_env_cmp"; p1c_environment_status=$p1c_join_status
    p1c_join "$p1c_argv_cmp"; p1c_argv_status=$p1c_join_status
    if [[ "$p1c_runner_status" != 0 || "$p1c_environment_status" != 0 || "$p1c_argv_status" != 0 ]]; then
        printf 'NATIVE scoped exec legs: runner=%s environment-cmp=%s argv-cmp=%s\n' \
            "$p1c_runner_status" "$p1c_environment_status" "$p1c_argv_status" >&2
        p1c_good=0
    fi
    # The array is never exported or formatted into diagnostics or a regular file.
    unset p1c_environment
    unset P1C_ORACLE_EMPTY P1C_ORACLE_NEWLINE P1C_ORACLE_DOLLAR
    [[ "$p1c_good" == 1 ]] || p1c_fail 'NATIVE full ordered NUL exec environment/literal argv mismatch'
    IFS= read -r p1c_run < "$p1c_state/run-path"
    [[ ! -s "$p1c_run/group-0.log" && -s "$p1c_state/released" ]] ||
        p1c_fail 'NATIVE exec witness stdout or real cleanup'
    p1c_pass 'NATIVE actual exec NUL environment and literal argv equal direct same-depth worker (incl SHLVL and underscore)'
}

p1c_require_functions _nqfc_capture _nqfc_parse_manager _nqfc_check_manager _nqfc_parse_status \
    _nqfc_kill_owned _nqfc_wait_handle _nqfc_drain _nqfc_worker nq_fast_concurrent_run
if [[ "$p1c_native_exec_only" == true ]]; then
    p1c_require_functions _nqfc_capture_bytes
    p1c_write_native_waiter
    p1c_native_exec_case
    printf 'concurrent fixtures: focused native exec comparison passed (%s assertion); UNIT and other native cases NOT run\n' "$p1c_passed"
    exit 0
fi
p1c_environment_cases
p1c_event_cases
p1c_manager_cases || p1c_fail 'strict REAL-rendered provider properties/failure prefix'
p1c_pass 'UNIT actual systemctl 5min/5s/4s rendering, independent manager version, wrong/missing/duplicate metadata and provider failure reject'
p1c_require_functions _nqfc_provider_manager_version _nqfc_check_manager_version _nqfc_prepare _nqfc_run
p1c_manager_version_cases || p1c_fail 'actual running-manager checker accepted wrong/missing/failed-prefix Version'
p1c_pass 'UNIT actual running-manager checker accepts exact Version+LF; wrong/missing/framing/query-failed prefix reject (stub provider)'
p1c_manager_version_entry_order || p1c_fail 'STATIC running-manager prelaunch entry order'
p1c_pass 'STATIC supported-client check then running-manager guard precede manager state/workspace/unit/launch; not an executed prepare oracle'
p1c_capture_cases || p1c_fail 'bounded failed/oversized provider capture'
p1c_pass 'UNIT checked provider capture preserves final LF and rejects failed/oversized prefixes'
p1c_status_cases || p1c_fail 'strict current nonce/group/status framing'
p1c_pass 'UNIT current nonce/group/status framing rejects stale/extra/malformed rows'
p1c_wait_cases || p1c_fail 'genuine wait status after trap interruption'
p1c_pass 'UNIT genuine 0/7/124/137 waits; interrupted wait joins actual terminal child'
p1c_fd_case || p1c_fail 'retained FD replacement/unowned-write refusal'
p1c_pass 'UNIT actual generic-file FD remains on old object; unpinned write refuses (not cgroup kernel evidence)'
p1c_group_cases
p1c_freeze_cases
p1c_drain_cases
p1c_model_cases
if [[ "$p1c_native" == true ]]; then
    p1c_write_native_waiter
    p1c_native_cases
    p1c_native_exec_case
    printf 'concurrent fixtures: UNIT plus real-provider disposable-root checks passed (%s assertions); no real test/proof groups run\n' "$p1c_passed"
else
    printf 'concurrent fixtures: UNIT/STUB passed (%s assertions); real manager/native checks NOT run\n' "$p1c_passed"
fi
