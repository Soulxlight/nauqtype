#!/usr/bin/env bash
# Private implementation of CONCURRENT_WARM_CONTRACT_v2 (375311b26ba6).
# Sourcing defines functions only. No variables, shell options, or traps change.
# Public: nq_fast_concurrent_run ROOT; owns this shell and ultimately exits.
# Caller already holds the full-tier lease and supplies
# _nqfc_release_tier_lock, called ONLY after verified cleanup/drain.
# Internal executable entry: bash fast_concurrent.sh --scope-entry ROOT RUN UNIT NONCE.
#
# Stable model-test seams (override only in the test process):
# _nqfc_provider_now                         -> monotonic centiseconds
# _nqfc_provider_manager UNIT                -> ManagerVersion first + unit rows
# _nqfc_provider_manager_version             -> bounded live-manager Version row
# _nqfc_provider_launch ROOT RUN UNIT NONCE  -> exec bounded real scope launcher
# _nqfc_provider_read FD                     -> complete pinned-file bytes
# _nqfc_provider_write FD VALUE              -> checked write, no pathname reopen
# _nqfc_provider_stat FD                     -> uid device inode hex-mode row
# _nqfc_provider_children DIRFD              -> one 'd' row per child cgroup
# _nqfc_provider_pause                       -> bounded polling interval
# _nqfc_provider_group ROOT GROUP            -> exec one of four genuine groups
# _nqfc_validate_environment PATH ROLE       -> predicate; ROLE=waiter|scope
# _nqfc_parse_events TEXT                    -> _nqfc_populated/_nqfc_frozen
# _nqfc_freeze_transaction                   -> one NONRESETTING 500cs transaction
# _nqfc_drain                                -> bounded old-object drain predicate
# _nqfc_wait_handle PID                      -> _nqfc_wait_status; PID is wait-only
# Private state and all local names use _nqfc_; no environment test switches.

_nqfc_provider_now() {
    local _nqfc_uptime _nqfc_idle
    read -r _nqfc_uptime _nqfc_idle < /proc/uptime || return 1
    [[ $_nqfc_uptime =~ ^([0-9]{1,11})\.([0-9]{2})$ ]] || return 1
    printf '%s\n' "$((10#${BASH_REMATCH[1]} * 100 + 10#${BASH_REMATCH[2]}))"
}

_nqfc_provider_manager_version() {
    /usr/bin/timeout --foreground --kill-after=1s 1s \
        /usr/bin/systemctl --user --no-ask-password show --property=Version --value
}

_nqfc_check_manager_version() {
    _nqfc_capture 256 _nqfc_provider_manager_version || return 1
    [[ $_nqfc_text == 255.4-1ubuntu8.18$'\n' ]] || return 1
}

_nqfc_provider_manager() {
    local _nqfc_text=
    _nqfc_check_manager_version || return 1
    printf 'ManagerVersion=%s\n' "${_nqfc_text%$'\n'}" || return 1
    /usr/bin/timeout --foreground --kill-after=1s 1s \
        /usr/bin/systemctl --user --no-ask-password show \
        --property=Id,Description,LoadState,ActiveState,SubState,Transient,InvocationID,ControlGroup,MemoryMax,MemorySwapMax,OOMPolicy,KillMode,SendSIGKILL,RuntimeMaxUSec,TimeoutStopUSec,CPUQuotaPerSecUSec,TasksMax,Result -- "$1"
}

_nqfc_provider_launch() {
    exec /usr/bin/timeout --foreground --kill-after=1s 320s \
        /usr/bin/systemd-run --user --scope --quiet --no-ask-password \
        --expand-environment=no --unit="$3" --description="nq-fast-concurrent:$4" \
        --property=MemoryMax=536870912 --property=MemorySwapMax=0 \
        --property=OOMPolicy=kill --property=KillMode=control-group \
        --property=SendSIGKILL=yes --property=RuntimeMaxSec=300s \
        --property=TimeoutStopSec=5s --property=CPUQuota=400% --property=TasksMax=256 \
        /bin/bash -p "$1/scripts/fast_concurrent.sh" --scope-entry "$1" "$2" "$3" "$4"
}

_nqfc_provider_read() {
    /usr/bin/cat -- "/proc/$$/fd/$1"
}

_nqfc_provider_write() {
    [[ $1 =~ ^[0-9]+$ ]] || return 1
    printf '%s\n' "$2" >&"$1"
}

_nqfc_provider_stat() {
    /usr/bin/stat -L --printf='%u %d %i %f\n' -- "/proc/$$/fd/$1"
}

_nqfc_provider_children() {
    /usr/bin/find -H "/proc/$$/fd/$1" -mindepth 1 -maxdepth 1 -type d -printf 'd\n'
}

_nqfc_provider_pause() {
    /usr/bin/sleep 0.01
}

_nqfc_provider_group() {
    case "$2" in
        0) exec /bin/bash -euo pipefail -c 'cd -- "$1"; exec bin/nauqc test' nq-fast-group "$1" ;;
        1) exec /bin/bash -euo pipefail -c 'cd -- "$1"; scripts/check_seed_capture.sh; exec scripts/check_m54_10_provenance.sh' nq-fast-group "$1" ;;
        2) exec /bin/bash -euo pipefail -c 'cd -- "$1"; scripts/check_attestation_batch.sh; exec scripts/check_m54_10_attestation.sh' nq-fast-group "$1" ;;
        3) exec /bin/bash -euo pipefail -c 'cd -- "$1"; exec scripts/check_run_budgeted.sh' nq-fast-group "$1" ;;
        *) return 1 ;;
    esac
}

# A bounded byte transport, including NUL, with the provider's actual status.
# Its only output is the caller's private in-memory _nqfc_bytes array.
_nqfc_capture_bytes() {
    local _nqfc_limit=$1 _nqfc_encoded
    shift
    _nqfc_bytes=()
    if ! _nqfc_encoded=$(
        trap - EXIT INT TERM HUP PIPE
        set -o pipefail
        "$@" | /usr/bin/head -c "$((_nqfc_limit + 1))" | /usr/bin/od -An -v -tu1
        [[ $? == 0 ]] || exit 1
    ); then
        return 1
    fi
    _nqfc_encoded=${_nqfc_encoded//$'\n'/ }
    read -r -a _nqfc_bytes <<< "$_nqfc_encoded"
    (( ${#_nqfc_bytes[@]} <= _nqfc_limit ))
}

# Metadata is ASCII; explicitly reject NUL instead of Bash silently dropping it.
_nqfc_capture() {
    local _nqfc_byte _nqfc_octal _nqfc_char
    local -a _nqfc_bytes=()
    _nqfc_text=
    _nqfc_capture_bytes "$@" || return 1
    for _nqfc_byte in "${_nqfc_bytes[@]}"; do
        [[ $_nqfc_byte =~ ^[0-9]{1,3}$ ]] || return 1
        (( 10#$_nqfc_byte > 0 && 10#$_nqfc_byte < 128 )) || return 1
        printf -v _nqfc_octal '%03o' "$((10#$_nqfc_byte))" || return 1
        printf -v _nqfc_char '%b' "\\$_nqfc_octal" || return 1
        _nqfc_text+=$_nqfc_char
    done
}

_nqfc_reject_reserved() {
    [[ $- != *a* && $- != *x* && $- != *v* ]] || return 1
    if /usr/bin/grep -az '^_nqfc_' "/proc/$BASHPID/environ" >/dev/null 2>/dev/null; then
        return 1
    else
        [[ $? == 1 ]] || return 1
    fi
    # Do not assign private state before checking current exports too.
    if (set -o pipefail; /usr/bin/env -0 | /usr/bin/grep -az '^_nqfc_' >/dev/null) 2>/dev/null; then
        return 1
    else
        [[ $? == 1 ]] || return 1
    fi
}

_nqfc_validate_environment() {
    local _nqfc_path=$1 _nqfc_role=$2
    local -a _nqfc_bytes=()
    _nqfc_capture_bytes 1048576 /usr/bin/cat -- "$_nqfc_path" || return 1
    _nqfc_validate_environment_bytes "$_nqfc_role"
}

_nqfc_validate_exports() {
    local _nqfc_role=$1
    local -a _nqfc_bytes=()
    _nqfc_capture_bytes 1048576 /usr/bin/env -0 || return 1
    _nqfc_validate_environment_bytes "$_nqfc_role"
}

_nqfc_validate_environment_bytes() {
    local _nqfc_role=$1 _nqfc_entry= _nqfc_key
    local _nqfc_byte _nqfc_octal _nqfc_char _nqfc_last= _nqfc_count=0
    local -A _nqfc_seen=()
    [[ $_nqfc_role == waiter || $_nqfc_role == scope ]] || return 1
    # One fresh capture supports proc environ and anonymous-pipe unit inputs.
    # Encoded bytes and decoded entries remain memory-only, never diagnostics.
    (( ${#_nqfc_bytes[@]} > 0 )) || return 1
    for _nqfc_byte in "${_nqfc_bytes[@]}"; do
        [[ $_nqfc_byte =~ ^[0-9]{1,3}$ ]] || return 1
        (( 10#$_nqfc_byte <= 255 )) || return 1
        _nqfc_last=$_nqfc_byte
        if (( 10#$_nqfc_byte != 0 )); then
            printf -v _nqfc_octal '%03o' "$((10#$_nqfc_byte))" || return 1
            printf -v _nqfc_char '%b' "\\$_nqfc_octal" || return 1
            _nqfc_entry+=$_nqfc_char
            continue
        fi
        _nqfc_count=$((_nqfc_count + 1))
        (( _nqfc_count <= 32768 )) || return 1
        [[ $_nqfc_entry == *=* ]] || return 1
        _nqfc_key=${_nqfc_entry%%=*}
        [[ $_nqfc_key == [abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_]* &&
           $_nqfc_key != *[!abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789]* ]] || return 1
        [[ ! ${_nqfc_seen[$_nqfc_key]+present} ]] || return 1
        _nqfc_seen[$_nqfc_key]=1
        case "$_nqfc_key" in
            _nqfc_*|BASH_ENV|ENV|SHELLOPTS|BASHOPTS|BASH_COMPAT|POSIXLY_CORRECT|BASH_REMATCH|BASH_XTRACEFD|CDPATH|GLOBIGNORE|IFS)
                return 1 ;;
            INVOCATION_ID) [[ $_nqfc_role == scope ]] || return 1 ;;
        esac
        _nqfc_entry=
    done
    [[ $_nqfc_last == 0 && -z $_nqfc_entry && $_nqfc_count != 0 ]]
}

_nqfc_now() {
    local _nqfc_clock _nqfc_sample
    # The fixed provider itself emits only validated decimal uptime. Keep this
    # builtin-only hot path separate from general metadata's byte transport.
    _nqfc_clock=$(trap - EXIT INT TERM HUP PIPE; _nqfc_provider_now || exit 1; printf '.') || return 1
    [[ $_nqfc_clock =~ ^(0|[1-9][0-9]{0,12})$'\n'[.]$ ]] || return 1
    _nqfc_sample=$((10#${BASH_REMATCH[1]}))
    (( _nqfc_sample >= ${_nqfc_now_cs:-0} )) || return 1
    _nqfc_now_cs=$_nqfc_sample
}

_nqfc_before() {
    _nqfc_now || return 1
    (( _nqfc_now_cs < $1 ))
}

# Every individual observation within the frozen transaction uses the same
# deadline. Clock reads bypass this wrapper to avoid recursive deadline checks.
_nqfc_observe() {
    local _nqfc_observed
    if (( ${_nqfc_tx_active:-0} == 1 )); then
        (( _nqfc_signal == 0 )) && _nqfc_before "$_nqfc_tx_end" || return 1
    fi
    _nqfc_capture "$@" || return 1
    _nqfc_observed=$_nqfc_text
    if (( ${_nqfc_tx_active:-0} == 1 )); then
        (( _nqfc_signal == 0 )) && _nqfc_before "$_nqfc_tx_end" || return 1
    fi
    _nqfc_text=$_nqfc_observed
}

_nqfc_uuid() {
    [[ $1 =~ ^[a-f0-9]{32}$ && $1 != 00000000000000000000000000000000 ]]
}

_nqfc_cgroup_path() {
    [[ $1 == /* && $1 != / && $1 != *'..'* && $1 != *'//'* &&
       $1 != *$'\n'* && $1 != *$'\r'* && $1 != *' '* &&
       $1 == */"$_nqfc_unit" ]]
}

_nqfc_parse_manager() {
    local _nqfc_rows=$1 _nqfc_row _nqfc_key _nqfc_value
    local -a _nqfc_lines=()
    _nqfc_manager=()
    [[ $_nqfc_rows == ManagerVersion=255.4-1ubuntu8.18$'\n'* &&
       $_nqfc_rows == *$'\n' ]] || return 1
    mapfile -t _nqfc_lines <<< "${_nqfc_rows%$'\n'}"
    for _nqfc_row in "${_nqfc_lines[@]}"; do
        [[ $_nqfc_row == *=* ]] || return 1
        _nqfc_key=${_nqfc_row%%=*}
        _nqfc_value=${_nqfc_row#*=}
        case "$_nqfc_key" in
            ManagerVersion|Id|Description|LoadState|ActiveState|SubState|Transient|InvocationID|ControlGroup|MemoryMax|MemorySwapMax|OOMPolicy|KillMode|SendSIGKILL|RuntimeMaxUSec|TimeoutStopUSec|CPUQuotaPerSecUSec|TasksMax|Result) ;;
            *) return 1 ;;
        esac
        [[ ! ${_nqfc_manager[$_nqfc_key]+present} ]] || return 1
        _nqfc_manager[$_nqfc_key]=$_nqfc_value
    done
    (( ${#_nqfc_manager[@]} == 19 )) || return 1
    [[ ${_nqfc_manager[ManagerVersion]-} == 255.4-1ubuntu8.18 &&
       ${_nqfc_manager[Id]-} == "$_nqfc_unit" &&
       ${_nqfc_manager[Description]-} == "nq-fast-concurrent:$_nqfc_nonce" &&
       ${_nqfc_manager[LoadState]-} == loaded &&
       ${_nqfc_manager[ActiveState]-} == active &&
       ${_nqfc_manager[SubState]-} == running &&
       ${_nqfc_manager[Transient]-} == yes &&
       ${_nqfc_manager[MemoryMax]-} == 536870912 &&
       ${_nqfc_manager[MemorySwapMax]-} == 0 &&
       ${_nqfc_manager[OOMPolicy]-} == kill &&
       ${_nqfc_manager[KillMode]-} == control-group &&
       ${_nqfc_manager[SendSIGKILL]-} == yes &&
       ${_nqfc_manager[TasksMax]-} == 256 &&
       ${_nqfc_manager[Result]-} == success ]] || return 1
    # systemctl 255.4 show renders timespans, not raw D-Bus microseconds.
    # Accept only these exact equivalent fixed values, never general times.
    case "${_nqfc_manager[RuntimeMaxUSec]-}" in 5min|300000000) ;; *) return 1 ;; esac
    case "${_nqfc_manager[TimeoutStopUSec]-}" in 5s|5000000) ;; *) return 1 ;; esac
    case "${_nqfc_manager[CPUQuotaPerSecUSec]-}" in 4s|4000000) ;; *) return 1 ;; esac
    _nqfc_uuid "${_nqfc_manager[InvocationID]-}" || return 1
    _nqfc_cgroup_path "${_nqfc_manager[ControlGroup]-}"
}

_nqfc_check_manager() {
    _nqfc_observe 8192 _nqfc_provider_manager "$_nqfc_unit" || return 1
    _nqfc_parse_manager "$_nqfc_text" || return 1
    if [[ -n ${_nqfc_uuid_bound-} ]]; then
        [[ ${_nqfc_manager[InvocationID]} == "$_nqfc_uuid_bound" &&
           ${_nqfc_manager[ControlGroup]} == "$_nqfc_cgroup" ]] || return 1
    fi
}

_nqfc_parse_events() {
    local _nqfc_rows=$1 _nqfc_key _nqfc_value _nqfc_extra
    _nqfc_populated= _nqfc_frozen=
    [[ $_nqfc_rows == *$'\n' ]] || return 1
    while read -r _nqfc_key _nqfc_value _nqfc_extra; do
        [[ -z $_nqfc_extra && ( $_nqfc_value == 0 || $_nqfc_value == 1 ) ]] || return 1
        case "$_nqfc_key" in
            populated) [[ -z $_nqfc_populated ]] || return 1; _nqfc_populated=$_nqfc_value ;;
            frozen) [[ -z $_nqfc_frozen ]] || return 1; _nqfc_frozen=$_nqfc_value ;;
            *) return 1 ;;
        esac
    done <<< "${_nqfc_rows%$'\n'}"
    [[ -n $_nqfc_populated && -n $_nqfc_frozen ]]
}

_nqfc_events() {
    _nqfc_observe 128 _nqfc_provider_read "${_nqfc_fds[events]}" || return 1
    _nqfc_parse_events "$_nqfc_text"
}

_nqfc_stat() {
    _nqfc_observe 128 _nqfc_provider_stat "$1" || return 1
    [[ $_nqfc_text =~ ^([0-9]+)' '([0-9]+)' '([0-9]+)' '([a-f0-9]+)$'\n'$ ]] || return 1
    _nqfc_stat_uid=${BASH_REMATCH[1]}
    _nqfc_stat_dev=${BASH_REMATCH[2]}
    _nqfc_stat_ino=${BASH_REMATCH[3]}
    _nqfc_stat_mode=${BASH_REMATCH[4]}
}

_nqfc_read_control() {
    local _nqfc_end=$1 _nqfc_left _nqfc_char _nqfc_timeout
    _nqfc_line=
    while (( ${#_nqfc_line} < 4096 )); do
        (( _nqfc_signal == 0 )) && _nqfc_before "$_nqfc_end" || return 1
        _nqfc_left=$((_nqfc_end - _nqfc_now_cs))
        printf -v _nqfc_timeout '%s.%02d' "$((_nqfc_left / 100))" "$((_nqfc_left % 100))" || return 1
        _nqfc_char=
        # An explicit NUL delimiter makes a NUL an observable empty read,
        # rather than read's usual silent NUL skipping.
        IFS= read -r -t "$_nqfc_timeout" -d '' -n 1 -u "$_nqfc_from_child" _nqfc_char || return 1
        [[ -n $_nqfc_char ]] || return 1
        _nqfc_before "$_nqfc_end" || return 1
        [[ $_nqfc_char == $'\n' ]] && return 0
        _nqfc_line+=$_nqfc_char
    done
    return 1
}

_nqfc_wait_handle() {
    local _nqfc_handle=$1 _nqfc_before_epoch _nqfc_code
    [[ $_nqfc_handle =~ ^[1-9][0-9]*$ ]] || return 1
    while :; do
        _nqfc_before_epoch=${_nqfc_signal_epoch:-0}
        if wait "$_nqfc_handle"; then _nqfc_code=0; else _nqfc_code=$?; fi
        if (( ${_nqfc_signal_epoch:-0} != _nqfc_before_epoch )); then
            continue
        fi
        _nqfc_wait_status=$_nqfc_code
        return 0
    done
}

_nqfc_parse_status() {
    local _nqfc_record=$1 _nqfc_index=$2
    [[ $_nqfc_record =~ ^nq-fast-status/v2' '([a-f0-9]{32})' '([0-3])' '([0-9]{1,3})' '([0-9]{1,3})$'\n'$ ]] || return 1
    [[ ${BASH_REMATCH[1]} == "$_nqfc_nonce" && ${BASH_REMATCH[2]} == "$_nqfc_index" ]] || return 1
    _nqfc_producer=$((10#${BASH_REMATCH[3]}))
    _nqfc_logger=$((10#${BASH_REMATCH[4]}))
    (( _nqfc_producer <= 255 && _nqfc_logger <= 255 )) || return 1
    [[ $_nqfc_record == "nq-fast-status/v2 $_nqfc_nonce $_nqfc_index $_nqfc_producer $_nqfc_logger"$'\n' ]]
}

_nqfc_read_status() {
    local _nqfc_index=$1
    [[ -f $_nqfc_run/group-$_nqfc_index.status && ! -L $_nqfc_run/group-$_nqfc_index.status ]] || return 1
    _nqfc_capture 160 /usr/bin/cat -- "$_nqfc_run/group-$_nqfc_index.status" || return 1
    _nqfc_parse_status "$_nqfc_text" "$_nqfc_index"
}

_nqfc_logger_run() {
    # Bash's non-POSIX file-limit units are KiB; this limit never reaches payload.
    set +o posix
    ulimit -f 8192 || return 1
    exec /usr/bin/tee --output-error=exit -- "$1" >/dev/null
}

_nqfc_worker() {
    local _nqfc_index=$1
    local -a _nqfc_pipeline=()
    trap - EXIT INT TERM HUP PIPE
    set +e
    set -o pipefail
    _nqfc_provider_group "$_nqfc_root" "$_nqfc_index" </dev/null 2>&1 |
        _nqfc_logger_run "$_nqfc_run/group-$_nqfc_index.log"
    _nqfc_pipeline=("${PIPESTATUS[@]}")
    (( ${#_nqfc_pipeline[@]} == 2 )) || exit 125
    if ! printf 'nq-fast-status/v2 %s %s %s %s\n' "$_nqfc_nonce" "$_nqfc_index" \
        "${_nqfc_pipeline[0]}" "${_nqfc_pipeline[1]}" > "$_nqfc_run/group-$_nqfc_index.status.tmp"; then
        exit 125
    fi
    /usr/bin/mv -fT -- "$_nqfc_run/group-$_nqfc_index.status.tmp" "$_nqfc_run/group-$_nqfc_index.status" || exit 125
    (( _nqfc_pipeline[1] == 0 )) || exit 125
    exit "${_nqfc_pipeline[0]}"
}

_nqfc_check_lease() {
    [[ $_nqfc_run == "$_nqfc_root"/build/verification/fast-concurrent.* &&
       $_nqfc_run != *$'\n'* && $_nqfc_run != *'/../'* &&
       -d $_nqfc_run && ! -L $_nqfc_run &&
       -f $_nqfc_run/lease && ! -L $_nqfc_run/lease ]] || return 1
    _nqfc_capture 128 /usr/bin/stat -L --printf='%u %a\n' -- "$_nqfc_run" || return 1
    [[ $_nqfc_text == "$EUID 700"$'\n' ]] || return 1
    _nqfc_capture 4096 /usr/bin/cat -- "$_nqfc_run/lease" || return 1
    [[ $_nqfc_text == "nq-fast-lease/v2"$'\n'"$_nqfc_nonce"$'\n'"$_nqfc_unit"$'\n'"$_nqfc_root"$'\n' ]]
}

_nqfc_scope_entry() {
    _nqfc_reject_reserved || exit 125
    (( $# == 5 )) && [[ $1 == --scope-entry ]] || exit 125
    local _nqfc_root=$2 _nqfc_run=$3 _nqfc_unit=$4 _nqfc_nonce=$5
    local _nqfc_uuid_bound= _nqfc_cgroup= _nqfc_dirfd _nqfc_device _nqfc_inode
    local _nqfc_text= _nqfc_line= _nqfc_now_cs=0 _nqfc_end=0
    local _nqfc_stat_uid _nqfc_stat_dev _nqfc_stat_ino _nqfc_stat_mode
    local _nqfc_index _nqfc_wait_status=0 _nqfc_signal_epoch=0 _nqfc_code=0
    local _nqfc_producer=0 _nqfc_logger=0 _nqfc_worker_error=0
    local -a _nqfc_handles=() _nqfc_codes=()
    local -A _nqfc_manager=()
    [[ $_nqfc_unit =~ ^nq-fast-[a-f0-9]{32}\.scope$ ]] || exit 125
    _nqfc_uuid "$_nqfc_nonce" || exit 125
    _nqfc_validate_environment "/proc/$BASHPID/environ" scope || exit 125
    _nqfc_validate_exports scope || exit 125
    _nqfc_check_lease || exit 125
    trap 'exit 125' PIPE
    trap '_nqfc_signal_epoch=$((_nqfc_signal_epoch + 1))' INT TERM HUP
    set -o pipefail
    _nqfc_check_manager || exit 125
    _nqfc_uuid_bound=${INVOCATION_ID-}
    [[ $_nqfc_uuid_bound == "${_nqfc_manager[InvocationID]}" ]] || exit 125
    _nqfc_cgroup=${_nqfc_manager[ControlGroup]}
    _nqfc_capture 4096 /usr/bin/cat -- "/proc/$BASHPID/cgroup" || exit 125
    [[ $_nqfc_text == "0::$_nqfc_cgroup"$'\n' ]] || exit 125
    exec {_nqfc_dirfd}< "/sys/fs/cgroup$_nqfc_cgroup" || exit 125
    _nqfc_stat "$_nqfc_dirfd" || exit 125
    [[ $_nqfc_stat_uid == "$EUID" && $((16#$_nqfc_stat_mode & 16#f000)) == 16384 ]] || exit 125
    _nqfc_device=$_nqfc_stat_dev _nqfc_inode=$_nqfc_stat_ino
    unset INVOCATION_ID || exit 125
    [[ ! ${INVOCATION_ID+x} ]] || exit 125
    printf 'READY %s %s %s %s %s %s\n' "$_nqfc_nonce" "$_nqfc_uuid_bound" \
        "$BASHPID" "$_nqfc_cgroup" "$_nqfc_device" "$_nqfc_inode" || exit 125
    IFS= read -r -t 5 -n 256 _nqfc_line || exit 125
    [[ $_nqfc_line == "GO $_nqfc_nonce $_nqfc_uuid_bound" && $_nqfc_signal_epoch == 0 ]] || exit 125
    exec {_nqfc_dirfd}<&- || exit 125
    for _nqfc_index in 0 1 2 3; do
        (( _nqfc_signal_epoch == 0 )) || { _nqfc_worker_error=1; break; }
        _nqfc_worker "$_nqfc_index" &
        _nqfc_handles[$_nqfc_index]=$!
    done
    for _nqfc_index in 0 1 2 3; do
        [[ -n ${_nqfc_handles[$_nqfc_index]-} ]] || { _nqfc_worker_error=1; continue; }
        if ! _nqfc_wait_handle "${_nqfc_handles[$_nqfc_index]}"; then
            _nqfc_worker_error=1
            continue
        fi
        _nqfc_codes[$_nqfc_index]=$_nqfc_wait_status
        _nqfc_handles[$_nqfc_index]=
        if ! _nqfc_read_status "$_nqfc_index" ||
            (( _nqfc_logger != 0 || _nqfc_producer != _nqfc_wait_status )); then
            _nqfc_worker_error=1
            continue
        fi
        if (( _nqfc_code == 0 && _nqfc_producer != 0 )); then _nqfc_code=$_nqfc_producer; fi
    done
    (( _nqfc_signal_epoch == 0 && _nqfc_worker_error == 0 )) || exit 125
    printf 'FINISHED %s %s %s %s %s %s\n' "$_nqfc_nonce" "$_nqfc_uuid_bound" \
        "${_nqfc_codes[0]}" "${_nqfc_codes[1]}" "${_nqfc_codes[2]}" "${_nqfc_codes[3]}" || exit 125
    # No fork or payload work after FINISHED. ACK may be queued while frozen.
    IFS= read -r -t 10 -n 256 _nqfc_line || exit 125
    [[ $_nqfc_line == "ACK $_nqfc_nonce $_nqfc_uuid_bound" && $_nqfc_signal_epoch == 0 ]] || exit 125
    exit "$_nqfc_code"
}

_nqfc_open_read() {
    local _nqfc_name=$1 _nqfc_file=$2 _nqfc_fd
    exec {_nqfc_fd}< "/proc/$$/fd/${_nqfc_fds[dir]}/$_nqfc_file" || return 1
    _nqfc_fds[$_nqfc_name]=$_nqfc_fd
    _nqfc_stat "$_nqfc_fd" || return 1
    [[ $_nqfc_stat_uid == "$EUID" && $_nqfc_stat_dev == "$_nqfc_device" &&
       $((16#$_nqfc_stat_mode & 16#f000)) == 32768 ]]
}

_nqfc_open_write() {
    local _nqfc_name=$1 _nqfc_file=$2 _nqfc_fd
    exec {_nqfc_fd}> "/proc/$$/fd/${_nqfc_fds[dir]}/$_nqfc_file" || return 1
    _nqfc_fds[$_nqfc_name]=$_nqfc_fd
    _nqfc_stat "$_nqfc_fd" || return 1
    [[ $_nqfc_stat_uid == "$EUID" && $_nqfc_stat_dev == "$_nqfc_device" &&
       $((16#$_nqfc_stat_mode & 16#f000)) == 32768 ]]
}

_nqfc_check_caps() {
    local _nqfc_name _nqfc_expected
    for _nqfc_name in type memory swap oomgroup tasks; do
        case "$_nqfc_name" in
            type) _nqfc_expected=domain ;;
            memory) _nqfc_expected=536870912 ;;
            swap) _nqfc_expected=0 ;;
            oomgroup) _nqfc_expected=1 ;;
            tasks) _nqfc_expected=256 ;;
        esac
        _nqfc_observe 64 _nqfc_provider_read "${_nqfc_fds[$_nqfc_name]}" || return 1
        [[ $_nqfc_text == "$_nqfc_expected"$'\n' ]] || return 1
    done
    _nqfc_observe 64 _nqfc_provider_read "${_nqfc_fds[cpu]}" || return 1
    [[ $_nqfc_text =~ ^([1-9][0-9]{0,8})' '([1-9][0-9]{0,8})$'\n'$ ]] || return 1
    (( 10#${BASH_REMATCH[1]} == 4 * 10#${BASH_REMATCH[2]} ))
}

_nqfc_memory_events() {
    local _nqfc_key _nqfc_value _nqfc_extra
    local -A _nqfc_memory_rows=()
    _nqfc_observe 1024 _nqfc_provider_read "${_nqfc_fds[memoryevents]}" || return 1
    [[ $_nqfc_text == *$'\n' ]] || return 1
    while read -r _nqfc_key _nqfc_value _nqfc_extra; do
        case "$_nqfc_key" in low|high|max|oom|oom_kill|oom_group_kill) ;; *) return 1 ;; esac
        [[ -z $_nqfc_extra && $_nqfc_value =~ ^(0|[1-9][0-9]{0,15})$ &&
           ! ${_nqfc_memory_rows[$_nqfc_key]+present} ]] || return 1
        _nqfc_memory_rows[$_nqfc_key]=$_nqfc_value
    done <<< "${_nqfc_text%$'\n'}"
    (( ${#_nqfc_memory_rows[@]} == 6 )) || return 1
    _nqfc_oom="${_nqfc_memory_rows[oom]} ${_nqfc_memory_rows[oom_kill]} ${_nqfc_memory_rows[oom_group_kill]}"
}

_nqfc_bind() {
    local _nqfc_fd
    _nqfc_check_manager || return 1
    _nqfc_capture 4096 /usr/bin/cat -- "/proc/$BASHPID/cgroup" || return 1
    [[ $_nqfc_text == 0::*$'\n' ]] || return 1
    [[ $_nqfc_text != "0::$_nqfc_cgroup"$'\n' &&
       $_nqfc_text != "0::$_nqfc_cgroup/"* ]] || return 1
    _nqfc_capture 128 /usr/bin/stat -f --printf='%T\n' -- "/sys/fs/cgroup" || return 1
    [[ $_nqfc_text == cgroup2fs$'\n' ]] || return 1
    _nqfc_cgpath="/sys/fs/cgroup$_nqfc_cgroup"
    exec {_nqfc_fd}< "$_nqfc_cgpath" || return 1
    _nqfc_fds[dir]=$_nqfc_fd
    _nqfc_stat "$_nqfc_fd" || return 1
    [[ $_nqfc_stat_uid == "$EUID" && $_nqfc_stat_dev == "$_nqfc_device" &&
       $_nqfc_stat_ino == "$_nqfc_inode" &&
       $((16#$_nqfc_stat_mode & 16#f000)) == 16384 ]] || return 1
    _nqfc_open_read events cgroup.events || return 1
    _nqfc_open_read procs cgroup.procs || return 1
    _nqfc_open_read type cgroup.type || return 1
    _nqfc_open_read memory memory.max || return 1
    _nqfc_open_read swap memory.swap.max || return 1
    _nqfc_open_read oomgroup memory.oom.group || return 1
    _nqfc_open_read tasks pids.max || return 1
    _nqfc_open_read cpu cpu.max || return 1
    _nqfc_open_read peak memory.peak || return 1
    _nqfc_open_read memoryevents memory.events || return 1
    _nqfc_open_write kill cgroup.kill || return 1
    _nqfc_open_write freeze cgroup.freeze || return 1
    _nqfc_check_caps || return 1
    _nqfc_members_only || return 1
    _nqfc_check_manager || return 1
    _nqfc_pinned=1
    _nqfc_memory_events || return 1
    _nqfc_oom_base=$_nqfc_oom
    [[ $_nqfc_oom_base == '0 0 0' ]] || return 1
}

_nqfc_members_only() {
    _nqfc_observe 4096 _nqfc_provider_read "${_nqfc_fds[procs]}" || return 1
    [[ $_nqfc_text == "$_nqfc_coordinator"$'\n' ]] || return 1
    _nqfc_observe 64 _nqfc_provider_children "${_nqfc_fds[dir]}" || return 1
    [[ -z $_nqfc_text ]]
}

_nqfc_tx_step() {
    (( _nqfc_signal == 0 )) || return 1
    _nqfc_before "$_nqfc_tx_end" || return 1
    "$@" || return 1
    _nqfc_before "$_nqfc_tx_end"
}

_nqfc_write_resources() {
    printf 'nq-fast-resources/v2\naggregate_peak_bytes=%s\noom=%s\n' \
        "$_nqfc_peak" "$_nqfc_oom" > "$_nqfc_run/resources.tmp"
}

_nqfc_capture_resources() {
    _nqfc_check_caps || return 1
    _nqfc_check_manager || return 1
    _nqfc_memory_events || return 1
    [[ $_nqfc_oom == "$_nqfc_oom_base" ]] || return 1
    _nqfc_observe 64 _nqfc_provider_read "${_nqfc_fds[peak]}" || return 1
    [[ $_nqfc_text =~ ^([1-9][0-9]{0,9})$'\n'$ ]] || return 1
    _nqfc_peak=${BASH_REMATCH[1]}
    (( _nqfc_peak <= 536870912 )) || return 1
    _nqfc_tx_step _nqfc_write_resources || return 1
    _nqfc_tx_step /usr/bin/mv -fT -- "$_nqfc_run/resources.tmp" "$_nqfc_run/resources" || return 1
}

_nqfc_send_ack() {
    printf 'ACK %s %s\n' "$_nqfc_nonce" "$_nqfc_uuid_bound" >&"$_nqfc_to_child"
}

_nqfc_freeze_transaction() {
    local _nqfc_tx_active=1
    _nqfc_now || return 1
    _nqfc_tx_end=$((_nqfc_now_cs + 500))
    _nqfc_tx_step _nqfc_provider_write "${_nqfc_fds[freeze]}" 1 || return 1
    while :; do
        _nqfc_tx_step _nqfc_events || return 1
        [[ $_nqfc_populated == 1 ]] || return 1
        [[ $_nqfc_frozen == 1 ]] && break
        _nqfc_tx_step _nqfc_provider_pause || return 1
    done
    _nqfc_tx_step _nqfc_members_only || return 1
    _nqfc_tx_step _nqfc_capture_resources || return 1
    _nqfc_tx_step _nqfc_send_ack || return 1
    _nqfc_tx_step _nqfc_provider_write "${_nqfc_fds[freeze]}" 0 || return 1
}

_nqfc_retired() {
    [[ -n ${_nqfc_fds[dir]-} ]] || return 1
    _nqfc_stat "${_nqfc_fds[dir]}" || return 1
    [[ $_nqfc_stat_uid == "$EUID" && $_nqfc_stat_dev == "$_nqfc_device" &&
       $_nqfc_stat_ino == "$_nqfc_inode" ]] || return 1
    _nqfc_capture 4096 /usr/bin/readlink -- "/proc/$$/fd/${_nqfc_fds[dir]}" || return 1
    # VFS retirement of this pinned old inode follows empty-before-removal.
    # Never infer retirement from a failed read or a replacement unit path.
    [[ $_nqfc_text == "$_nqfc_cgpath (deleted)"$'\n' ]]
}

_nqfc_drain() {
    local _nqfc_drain_end
    (( _nqfc_pinned == 1 )) || return 1
    _nqfc_now || return 1
    _nqfc_drain_end=$((_nqfc_now_cs + 500))
    while _nqfc_before "$_nqfc_drain_end"; do
        if _nqfc_events 2>/dev/null; then
            if [[ $_nqfc_populated == 0 ]]; then
                _nqfc_before "$_nqfc_drain_end"
                return "$?"
            fi
        elif _nqfc_retired; then
            _nqfc_before "$_nqfc_drain_end"
            return "$?"
        else
            printf 'check_fast concurrent: cgroup events unreadable without retirement proof\n' >&2
            return 1
        fi
        _nqfc_provider_pause || return 1
    done
    return 1
}

_nqfc_kill_owned() {
    (( _nqfc_pinned == 1 )) || return 1
    _nqfc_provider_write "${_nqfc_fds[kill]}" 1
}

_nqfc_on_signal() {
    _nqfc_signal_epoch=$((_nqfc_signal_epoch + 1))
    (( _nqfc_signal != 0 )) || _nqfc_signal=$1
    if (( _nqfc_pinned == 1 && _nqfc_drained == 0 )); then
        _nqfc_kill_owned || _nqfc_infra=1
    fi
}

_nqfc_close_controls() {
    if [[ -n $_nqfc_to_child ]]; then
        exec {_nqfc_to_child}>&- || return 1
        _nqfc_to_child=
    fi
    if [[ -n $_nqfc_from_child ]]; then
        exec {_nqfc_from_child}<&- || return 1
        _nqfc_from_child=
    fi
}

_nqfc_close_pins() {
    local _nqfc_name _nqfc_fd _nqfc_failed=0
    for _nqfc_name in "${!_nqfc_fds[@]}"; do
        _nqfc_fd=${_nqfc_fds[$_nqfc_name]}
        if ! exec {_nqfc_fd}>&-; then _nqfc_failed=1; fi
        unset '_nqfc_fds[$_nqfc_name]'
    done
    _nqfc_pinned=0
    (( _nqfc_failed == 0 ))
}

_nqfc_on_exit() {
    local _nqfc_exit_code=$1
    trap - EXIT
    set +e
    if (( _nqfc_drained == 0 )); then
        _nqfc_close_controls || _nqfc_infra=1
        if (( _nqfc_pinned == 1 )); then
            if ! _nqfc_kill_owned; then
                _nqfc_retired || _nqfc_infra=1
            fi
            if _nqfc_drain; then _nqfc_drained=1; else _nqfc_infra=1; fi
        elif (( _nqfc_launched == 0 )); then
            _nqfc_drained=1
        fi
    fi
    if [[ -n $_nqfc_launcher ]]; then
        if _nqfc_wait_handle "$_nqfc_launcher"; then
            _nqfc_launcher=
        else
            _nqfc_infra=1
        fi
    fi
    _nqfc_close_controls || _nqfc_infra=1
    if (( _nqfc_drained == 1 )) && [[ -z $_nqfc_launcher ]]; then
        _nqfc_close_pins || _nqfc_infra=1
        if _nqfc_release_tier_lock; then
            if [[ -n $_nqfc_run ]]; then
                /usr/bin/rm -f -- "$_nqfc_run/lease" || _nqfc_infra=1
            fi
        else
            _nqfc_infra=1
        fi
    else
        _nqfc_infra=1
        printf 'check_fast concurrent: cleanup uncertain; tier lease and evidence retained\n' >&2
    fi
    if (( _nqfc_infra != 0 )); then _nqfc_exit_code=125; fi
    if (( _nqfc_signal != 0 )); then _nqfc_exit_code=$((128 + _nqfc_signal)); fi
    if [[ -n $_nqfc_run ]]; then
        if ! printf 'nq-fast-result/v2\nexit_code=%s\naggregate_peak_bytes=%s\ndrained=%s\n' \
            "$_nqfc_exit_code" "$_nqfc_peak" "$_nqfc_drained" > "$_nqfc_run/result"; then
            (( _nqfc_signal != 0 )) || _nqfc_exit_code=125
        fi
    fi
    exit "$_nqfc_exit_code"
}

_nqfc_prepare() {
    [[ $EUID != 0 && ${BASH_VERSINFO[0]} -ge 5 ]] || return 1
    _nqfc_validate_environment "/proc/$BASHPID/environ" waiter || return 1
    _nqfc_validate_exports waiter || return 1
    _nqfc_capture 2048 /usr/bin/systemd-run --version || return 1
    [[ $_nqfc_text == 'systemd 255 (255.4-1ubuntu8.18)'$'\n'* ]] || return 1
    _nqfc_check_manager_version || return 1
    _nqfc_capture 128 /usr/bin/timeout --foreground --kill-after=1s 1s \
        /usr/bin/systemctl --user --no-ask-password is-system-running || return 1
    [[ $_nqfc_text == running$'\n' ]] || return 1
    [[ $_nqfc_root == /* && $_nqfc_root != *$'\n'* && $_nqfc_root != *$'\r'* &&
       -d $_nqfc_root && -d $_nqfc_root/build/verification ]] || return 1
    _nqfc_run=$(/usr/bin/mktemp -d -- "$_nqfc_root/build/verification/fast-concurrent.XXXXXXXXXXXX") || return 1
    _nqfc_capture 128 /usr/bin/stat -L --printf='%u %a\n' -- "$_nqfc_run" || return 1
    [[ $_nqfc_text == "$EUID 700"$'\n' ]] || return 1
    IFS= read -r _nqfc_random < /proc/sys/kernel/random/uuid || return 1
    _nqfc_random=${_nqfc_random//-/}
    _nqfc_uuid "$_nqfc_random" || return 1
    _nqfc_unit="nq-fast-$_nqfc_random.scope"
    IFS= read -r _nqfc_random < /proc/sys/kernel/random/uuid || return 1
    _nqfc_nonce=${_nqfc_random//-/}
    _nqfc_uuid "$_nqfc_nonce" || return 1
    _nqfc_capture 4096 /usr/bin/timeout --foreground --kill-after=1s 1s \
        /usr/bin/systemctl --user --no-ask-password --no-legend --plain \
        list-units --all -- "$_nqfc_unit" || return 1
    [[ -z $_nqfc_text ]] || return 1
    printf 'nq-fast-lease/v2\n%s\n%s\n%s\n' "$_nqfc_nonce" "$_nqfc_unit" \
        "$_nqfc_root" > "$_nqfc_run/lease" || return 1
    _nqfc_now || return 1
    _nqfc_outer_end=$((_nqfc_now_cs + 32000))
}

_nqfc_parse_ready() {
    local _nqfc_tag _nqfc_seen_nonce _nqfc_seen_uuid _nqfc_extra
    read -r _nqfc_tag _nqfc_seen_nonce _nqfc_seen_uuid _nqfc_coordinator \
        _nqfc_cgroup _nqfc_device _nqfc_inode _nqfc_extra <<< "$_nqfc_line"
    [[ $_nqfc_tag == READY && $_nqfc_seen_nonce == "$_nqfc_nonce" &&
       -z $_nqfc_extra && $_nqfc_coordinator =~ ^[1-9][0-9]{0,9}$ &&
       $_nqfc_device =~ ^[0-9]{1,20}$ && $_nqfc_inode =~ ^[0-9]{1,20}$ ]] || return 1
    (( _nqfc_coordinator <= 2147483647 )) || return 1
    _nqfc_uuid "$_nqfc_seen_uuid" || return 1
    _nqfc_cgroup_path "$_nqfc_cgroup" || return 1
    [[ $_nqfc_line == "READY $_nqfc_nonce $_nqfc_seen_uuid $_nqfc_coordinator $_nqfc_cgroup $_nqfc_device $_nqfc_inode" ]] || return 1
    _nqfc_uuid_bound=$_nqfc_seen_uuid
}

_nqfc_parse_finished() {
    local _nqfc_tag _nqfc_seen_nonce _nqfc_seen_uuid _nqfc_extra _nqfc_index
    read -r _nqfc_tag _nqfc_seen_nonce _nqfc_seen_uuid \
        '_nqfc_codes[0]' '_nqfc_codes[1]' '_nqfc_codes[2]' '_nqfc_codes[3]' \
        _nqfc_extra <<< "$_nqfc_line"
    [[ $_nqfc_tag == FINISHED && $_nqfc_seen_nonce == "$_nqfc_nonce" &&
       $_nqfc_seen_uuid == "$_nqfc_uuid_bound" && -z $_nqfc_extra ]] || return 1
    _nqfc_result=0
    for _nqfc_index in 0 1 2 3; do
        [[ ${_nqfc_codes[$_nqfc_index]} =~ ^(0|[1-9][0-9]{0,2})$ ]] || return 1
        (( _nqfc_codes[$_nqfc_index] <= 255 )) || return 1
        _nqfc_read_status "$_nqfc_index" || return 1
        (( _nqfc_logger == 0 && _nqfc_producer == _nqfc_codes[$_nqfc_index] )) || return 1
        if (( _nqfc_result == 0 && _nqfc_producer != 0 )); then _nqfc_result=$_nqfc_producer; fi
    done
    [[ $_nqfc_line == "FINISHED $_nqfc_nonce $_nqfc_uuid_bound ${_nqfc_codes[0]} ${_nqfc_codes[1]} ${_nqfc_codes[2]} ${_nqfc_codes[3]}" ]]
}

_nqfc_run() {
    local _nqfc_ready_end _nqfc_index _nqfc_original_read _nqfc_original_write
    _nqfc_prepare || return 125
    (( _nqfc_signal == 0 )) || return 125
    _nqfc_now || return 125
    _nqfc_ready_end=$((_nqfc_now_cs + 1000))
    # Once creation is attempted, an unbound/ambiguous outcome retains the
    # lease. $! is recorded only after a successful coprocess creation.
    _nqfc_launched=1
    if ! coproc _nqfc_launch {
        trap - EXIT INT TERM HUP PIPE
        _nqfc_provider_launch "$_nqfc_root" "$_nqfc_run" "$_nqfc_unit" "$_nqfc_nonce" 2>&1
    }; then
        return 125
    fi
    _nqfc_launcher=$!
    [[ $_nqfc_launcher =~ ^[1-9][0-9]*$ ]] || return 125
    [[ -n ${_nqfc_launch[0]-} && -n ${_nqfc_launch[1]-} ]] || return 125
    _nqfc_original_read=${_nqfc_launch[0]} _nqfc_original_write=${_nqfc_launch[1]}
    exec {_nqfc_from_child}<&"$_nqfc_original_read" || return 125
    exec {_nqfc_to_child}>&"$_nqfc_original_write" || return 125
    exec {_nqfc_original_read}<&- || return 125
    exec {_nqfc_original_write}>&- || return 125
    _nqfc_read_control "$_nqfc_ready_end" || return 125
    _nqfc_parse_ready || return 125
    (( _nqfc_signal == 0 )) || return 125
    _nqfc_bind || return 125
    _nqfc_before "$_nqfc_ready_end" || return 125
    (( _nqfc_signal == 0 )) || return 125
    printf 'GO %s %s\n' "$_nqfc_nonce" "$_nqfc_uuid_bound" >&"$_nqfc_to_child" || return 125
    _nqfc_read_control "$_nqfc_outer_end" || return 125
    _nqfc_parse_finished || return 125
    _nqfc_freeze_transaction || return 125
    _nqfc_wait_handle "$_nqfc_launcher" || return 125
    _nqfc_launcher=
    (( _nqfc_wait_status == _nqfc_result )) || return 125
    _nqfc_drain || return 125
    _nqfc_drained=1
    _nqfc_before "$_nqfc_outer_end" || return 125
    for _nqfc_index in 0 1 2 3; do
        [[ -f $_nqfc_run/group-$_nqfc_index.log && ! -L $_nqfc_run/group-$_nqfc_index.log ]] || return 125
        /usr/bin/cat -- "$_nqfc_run/group-$_nqfc_index.log" || return 125
    done
    _nqfc_complete=1
    return "$_nqfc_result"
}

nq_fast_concurrent_run() {
    # This check precedes every private assignment, including local declarations.
    if ! _nqfc_reject_reserved; then
        printf 'check_fast concurrent: unsupported caller environment or shell state\n' >&2
        exit 125
    fi
    (( $# == 1 )) || exit 125
    local _nqfc_root=${1-} _nqfc_run= _nqfc_unit= _nqfc_nonce= _nqfc_random=
    local _nqfc_text= _nqfc_line= _nqfc_now_cs=0 _nqfc_outer_end=0 _nqfc_tx_end=0
    local _nqfc_signal=0 _nqfc_signal_epoch=0 _nqfc_infra=0 _nqfc_pinned=0
    local _nqfc_launched=0 _nqfc_drained=0 _nqfc_launcher= _nqfc_launch_PID=
    local _nqfc_to_child= _nqfc_from_child= _nqfc_uuid_bound= _nqfc_cgroup=
    local _nqfc_cgpath= _nqfc_coordinator= _nqfc_device= _nqfc_inode=
    local _nqfc_stat_uid= _nqfc_stat_dev= _nqfc_stat_ino= _nqfc_stat_mode=
    local _nqfc_populated= _nqfc_frozen= _nqfc_peak=0 _nqfc_oom= _nqfc_oom_base=
    local _nqfc_producer=0 _nqfc_logger=0 _nqfc_wait_status=0 _nqfc_result=0
    local _nqfc_run_code _nqfc_complete=0
    local -a _nqfc_launch=() _nqfc_codes=()
    local -A _nqfc_manager=() _nqfc_fds=()
    declare -F _nqfc_release_tier_lock >/dev/null || exit 125
    trap '_nqfc_on_exit "$?"' EXIT
    trap '_nqfc_on_signal 2' INT
    trap '_nqfc_on_signal 15' TERM
    trap '_nqfc_on_signal 1' HUP
    trap '_nqfc_infra=1' PIPE
    set -o pipefail
    umask 077
    if _nqfc_run; then _nqfc_run_code=0; else _nqfc_run_code=$?; fi
    if (( _nqfc_run_code == 125 && _nqfc_complete == 0 )); then _nqfc_infra=1; fi
    exit "$_nqfc_run_code"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    _nqfc_scope_entry "$@"
fi
