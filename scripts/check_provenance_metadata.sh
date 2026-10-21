#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
source "$repo_root/scripts/provenance.sh"

scratch=$(mktemp -d /tmp/nauqtype-provenance-metadata-XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
root="$scratch/tree"
mkdir -p "$root/real-parent"
printf '' > "$root/empty"
printf 'metadata payload\n' > "$root/content"
printf '#!/bin/sh\nexit 0\n' > "$root/executable"
printf 'read only\n' > "$root/read-only"
printf 'no read bits\n' > "$root/unreadable"
printf 'space in path\n' > "$root/space path"
chmod 755 "$root/executable"
chmod 444 "$root/read-only"
chmod 000 "$root/unreadable"
printf 'parent target\n' > "$root/real-parent/file"
ln -s real-parent/file "$root/file-link"
ln -s real-parent "$root/parent-link"

# Independent pre-coalescing algorithms: retain the separate stat calls.
legacy_regular() {
    local p=$1 mode
    [[ -f "$p" && ! -L "$p" && -r "$p" ]] || return 1
    legacy_directory "${p%/*}" || return 1
    mode=$(stat -c '%a' -- "$p") || return 1
    [[ "$mode" =~ ^[0-7]{1,4}$ ]] && (( (8#$mode & 0444) != 0 ))
}

legacy_directory() {
    local p=$1
    [[ "$p" == /* ]] || return 1
    while [[ "$p" != / ]]; do
        [[ -d "$p" && ! -L "$p" ]] || return 1
        p=${p%/*}
        [[ -n "$p" ]] || p=/
    done
}

legacy_mode() {
    local mode
    legacy_regular "$1" || return 1
    mode=$(stat -c '%a' -- "$1") || return 1
    if (( (8#$mode & 0111) != 0 )); then printf '100755\n'; else printf '100644\n'; fi
}

legacy_frame() {
    local root=$1 domain=$2 list=$3 p count mode size LC_ALL=C
    legacy_directory "$root" || return 1
    [[ "$domain" =~ ^[a-z0-9-]+/v[0-9]+$ ]] || return 1
    count=$(wc -l < "$list") || return 1
    printf '%s\nfiles:%d\n' "$domain" "$count" || return 1
    while IFS= read -r p; do
        legacy_mode "$root/$p" > "$scratch/legacy-mode" || return 1
        mode=$(<"$scratch/legacy-mode")
        size=$(stat -c '%s' -- "$root/$p") || return 1
        [[ "$size" =~ ^(0|[1-9][0-9]*)$ ]] || return 1
        printf 'path-bytes:%d\n%s\nmode:%s\ncontent-bytes:%s\n' "${#p}" "$p" "$mode" "$size" || return 1
        cat -- "$root/$p" || return 1
        printf '\n' || return 1
    done < "$list"
}

legacy_files_digest() (
    set -o pipefail
    legacy_frame "$@" | sha256sum | { read -r digest _; printf '%s\n' "$digest"; }
)

assert_equal() {
    local expected=$1 actual=$2 label=$3
    if [[ "$expected" != "$actual" ]]; then
        printf 'FAIL %s: expected <%s>, got <%s>\n' "$label" "$expected" "$actual" >&2
        exit 1
    fi
}

passed=0
compare_path() {
    local label=$1 path=$2 legacy_status=0 current_status=0 metadata_status=0
    if legacy_regular "$path" > "$scratch/legacy-regular.out"; then :; else legacy_status=$?; fi
    if prov_regular "$path" > "$scratch/current-regular.out"; then :; else current_status=$?; fi
    assert_equal "$legacy_status" "$current_status" "$label regular status"
    cmp -s "$scratch/legacy-regular.out" "$scratch/current-regular.out"
    [[ ! -s "$scratch/legacy-regular.out" ]]

    legacy_status=0; current_status=0
    if legacy_mode "$path" > "$scratch/legacy-mode.out"; then :; else legacy_status=$?; fi
    if prov_mode "$path" > "$scratch/current-mode.out"; then :; else current_status=$?; fi
    assert_equal "$legacy_status" "$current_status" "$label mode status"
    cmp -s "$scratch/legacy-mode.out" "$scratch/current-mode.out"

    metadata_status=0
    if prov_file_metadata "$path" > "$scratch/current-metadata.out"; then :; else metadata_status=$?; fi
    assert_equal "$legacy_status" "$metadata_status" "$label metadata status"
    if (( legacy_status == 0 )); then
        printf '%s %s\n' "$(<"$scratch/legacy-mode.out")" "$(stat -c '%s' -- "$path")" > "$scratch/expected-metadata.out"
    else
        : > "$scratch/expected-metadata.out"
    fi
    cmp -s "$scratch/expected-metadata.out" "$scratch/current-metadata.out"
    ((passed += 1))
}

compare_path empty "$root/empty"
compare_path content "$root/content"
compare_path executable "$root/executable"
compare_path read-only "$root/read-only"
compare_path unreadable "$root/unreadable"
compare_path missing "$root/missing"
compare_path directory "$root/real-parent"
compare_path symlink-file "$root/file-link"
compare_path symlink-parent "$root/parent-link/file"
compare_path space-path "$root/space path"

printf '%s\n' 'content' 'empty' 'executable' 'read-only' 'space path' > "$scratch/valid.paths"
legacy_frame "$root" provenance-metadata/v1 "$scratch/valid.paths" > "$scratch/legacy.frame"
prov_files_frame "$root" provenance-metadata/v1 "$scratch/valid.paths" > "$scratch/current.frame"
cmp -s "$scratch/legacy.frame" "$scratch/current.frame"
((passed += 1))

legacy_digest=$(legacy_files_digest "$root" provenance-metadata/v1 "$scratch/valid.paths")
current_digest=$(prov_files_digest "$root" provenance-metadata/v1 "$scratch/valid.paths")
assert_equal "$legacy_digest" "$current_digest" 'framed digest'
((passed += 1))

printf '%s\n' missing > "$scratch/invalid.paths"
legacy_status=0; current_status=0
if legacy_frame "$root" provenance-metadata/v1 "$scratch/invalid.paths" > "$scratch/legacy-failure.out"; then :; else legacy_status=$?; fi
if prov_files_frame "$root" provenance-metadata/v1 "$scratch/invalid.paths" > "$scratch/current-failure.out"; then :; else current_status=$?; fi
assert_equal "$legacy_status" "$current_status" 'frame failure status'
[[ "$legacy_status" != 0 ]]
cmp -s "$scratch/legacy-failure.out" "$scratch/current-failure.out"
((passed += 1))

legacy_status=0; current_status=0
if legacy_files_digest "$root" provenance-metadata/v1 "$scratch/invalid.paths" > "$scratch/legacy-digest-failure.out"; then :; else legacy_status=$?; fi
if prov_files_digest "$root" provenance-metadata/v1 "$scratch/invalid.paths" > "$scratch/current-digest-failure.out"; then :; else current_status=$?; fi
assert_equal "$legacy_status" "$current_status" 'digest failure status'
[[ "$legacy_status" != 0 ]]
cmp -s "$scratch/legacy-digest-failure.out" "$scratch/current-digest-failure.out"
((passed += 1))

assert_equal 14 "$passed" 'original metadata cases retained'
metadata_scratch=$scratch

md_pass() { ((passed += 1)); printf 'ok %s\n' "$1"; }
md_fail() { printf 'FAIL %s\n' "$*" >&2; exit 1; }
gnu_stat=$(command -v stat)
gnu_cp=$(command -v cp)

# Frozen pre-batching path language, independent of the new capture reader.
legacy_safe_relative() {
    local LC_ALL=C p=$1
    [[ -n "$p" && "$p" != /* && "$p" != */ && "$p" != *\\* && ! "$p" =~ [^\ -~] ]] || return 1
    case "/$p/" in *'//'*|*'/./'*|*'/../'*) return 1;; esac
}

legacy_validate_paths() (
    local list=$1 scratch p previous='' LC_ALL=C
    legacy_regular "$list" || exit 1
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    while IFS= read -r p; do
        legacy_safe_relative "$p" || exit 1
        [[ -z "$previous" || "$p" > "$previous" ]] || exit 1
        printf '%s\n' "$p" >> "$scratch" || exit 1
        previous=$p
    done < "$list"
    cmp -s "$list" "$scratch"
)

md_paths_case() {
    local label=$1 list=$2 expected=$3 old=0 new=0
    if legacy_validate_paths "$list" > "$scratch/paths.old"; then :; else old=$?; fi
    if prov_validate_paths "$list" > "$scratch/paths.new"; then :; else new=$?; fi
    assert_equal "$expected" "$old" "$label frozen status"
    assert_equal "$old" "$new" "$label current status"
    [[ ! -s "$scratch/paths.old" && ! -s "$scratch/paths.new" ]] || md_fail "$label public output"
    md_pass "paths $label"
}

: > "$scratch/paths-empty"
printf '%65535s\n' '' | tr ' ' a > "$scratch/paths-65536"
printf '%65536s\n' '' | tr ' ' a > "$scratch/paths-65537"
assert_equal 65536 "$(wc -c < "$scratch/paths-65536")" 'boundary fixture 65536'
assert_equal 65537 "$(wc -c < "$scratch/paths-65537")" 'boundary fixture 65537'
md_paths_case empty "$scratch/paths-empty" 0
md_paths_case 65536-bytes "$scratch/paths-65536" 0
md_paths_case 65537-bytes "$scratch/paths-65537" 0
for md_case in nul nul-final missing-lf blank duplicate unordered tab cr control del non-ascii absolute dotdot double-slash backslash trailing-slash; do
    case "$md_case" in
        nul) printf 'a\0b\n' ;;
        nul-final) printf 'a\n\0' ;;
        missing-lf) printf a ;;
        blank) printf '\n' ;;
        duplicate) printf 'a\na\n' ;;
        unordered) printf 'b\na\n' ;;
        tab) printf 'a\tb\n' ;;
        cr) printf 'a\r\n' ;;
        control) printf 'a\037b\n' ;;
        del) printf 'a\177b\n' ;;
        non-ascii) printf 'a\200b\n' ;;
        absolute) printf '/a\n' ;;
        dotdot) printf 'a/../b\n' ;;
        double-slash) printf 'a//b\n' ;;
        backslash) printf 'a\\b\n' ;;
        trailing-slash) printf 'a/\n' ;;
    esac > "$scratch/paths-bad"
    md_paths_case "$md_case" "$scratch/paths-bad" 1
done
printf '%s\n' ' space path ' 'both'"'"'"quotes' $'literal $(exit 91);\140exit 92\140&|<>(){}[]*?!#' |
    LC_ALL=C sort > "$scratch/paths-printable"
md_paths_case printable-punctuation "$scratch/paths-printable" 0

# Only the two bounded capture reads are intercepted; ordinary line reads stay real.
md_read_case() {
    local md_fault=$1 md_expected=$2 md_reads=$3 md_fault_file="$scratch/read.paths"
    local md_status=0 md_target md_rc
    if (( $# > 3 )); then "$gnu_cp" -- "$4" "$md_fault_file"; else printf 'a\n' > "$md_fault_file"; fi
    : > "$scratch/read.calls"; : > "$scratch/read.legacy"
    if (
        read() {
            local md_target=${!#} md_rc=0
            if [[ "$md_target" != bytes && "$md_target" != again ]]; then builtin read "$@"; return $?; fi
            printf '%s\n' "$md_target" >> "$scratch/read.calls"
            case "$md_fault:$md_target" in
                truncate:bytes) printf a > "$md_fault_file" ;;
                growth:bytes) printf b >> "$md_fault_file" ;;
                same-size:again) printf 'b\n' > "$md_fault_file" ;;
                partial-status1:bytes) builtin read -r -n 1 "$md_target" || :; return 1 ;;
            esac
            if builtin read "$@"; then md_rc=0; else md_rc=$?; fi
            case "$md_fault:$md_target" in error-first:bytes|error-second:again) return 2;; esac
            return "$md_rc"
        }
        _prov_validate_paths_legacy() { printf 'fallback\n' >> "$scratch/read.legacy"; return 0; }
        prov_validate_paths "$md_fault_file"
    ) > "$scratch/read.out" 2> "$scratch/read.err"; then :; else md_status=$?; fi
    assert_equal "$md_expected" "$md_status" "read $md_fault status"
    assert_equal "$md_reads" "$(wc -l < "$scratch/read.calls")" "read $md_fault bounded calls"
    [[ ! -s "$scratch/read.out" && ! -s "$scratch/read.legacy" ]] || md_fail "read $md_fault output/fallback"
    md_pass "bounded read $md_fault"
}
md_read_case complete-eof 0 2
md_read_case empty-boundary 0 2 "$scratch/paths-empty"
md_read_case 65536-boundary 0 2 "$scratch/paths-65536"
md_read_case truncate 1 1
md_read_case growth 1 1
md_read_case same-size 1 2
md_read_case partial-status1 1 1
md_read_case error-first 1 1
md_read_case error-second 1 2
(
    read() {
        local md_target=${!#}
        if [[ "$md_target" == bytes || "$md_target" == again ]]; then
            printf 'bounded\n' >> "$scratch/large.read"; return 2
        fi
        builtin read "$@"
    }
    _prov_validate_paths_legacy() { printf 'legacy\n' >> "$scratch/large.legacy"; legacy_validate_paths "$@"; }
    prov_validate_paths "$scratch/paths-65537"
) > "$scratch/large.out"
[[ ! -s "$scratch/large.out" && ! -e "$scratch/large.read" ]] || md_fail 'large input bounded read'
assert_equal 1 "$(wc -l < "$scratch/large.legacy")" 'large input legacy selection'
md_pass 'over-64K selects legacy before bounded capture'

md_capacity_case() {
    local md_limit=$1 md_environment=$2 md_expected=$3 md_status=0
    if (
        getconf() {
            [[ "$1" == ARG_MAX ]] || return 2
            if [[ "$md_limit" == error ]]; then printf 'unsupported\n' >&2; return 3; fi
            printf '%s\n' "$md_limit"
        }
        env() {
            [[ "$*" == -0 ]] || return 2
            [[ "$md_environment" != error ]] || return 3
            head -c "$md_environment" /dev/zero
        }
        _prov_batch_supported
    ) > "$scratch/capacity.out" 2> "$scratch/capacity.err"; then :; else md_status=$?; fi
    assert_equal "$md_expected" "$md_status" "capacity $md_limit/$md_environment"
    [[ ! -s "$scratch/capacity.out" && ! -s "$scratch/capacity.err" ]] || md_fail 'capacity query not quiet'
    md_pass "capacity $md_limit/$md_environment"
}
md_capacity_case error 0 1
md_capacity_case 0 0 1
md_capacity_case 131071 0 1
md_capacity_case 131072 0 0
md_capacity_case 131072 8000 1
md_capacity_case 2097152 32768 0
md_capacity_case 2097152 32769 1
md_capacity_case 2097152 error 1

# Log every stat invocation, delegating all formats other than the selected batch.
md_stat() {
    local md_path md_argbytes=0
    printf '%q ' "$@" >> "$metadata_scratch/stat.argv"; printf '\n' >> "$metadata_scratch/stat.argv"
    if [[ "${1-}" != --printf || "${2-}" != '%f %s %n\0' ]]; then
        printf 'scalar\n' >> "$metadata_scratch/stat.calls"
        "$gnu_stat" "$@"
        return $?
    fi
    local -a md_files=("${@:4}")
    for md_path in "${md_files[@]}"; do md_argbytes=$((md_argbytes + ${#md_path} + 1)); done
    printf 'batch:%s:%s\n' "${#md_files[@]}" "$md_argbytes" >> "$metadata_scratch/stat.calls"
    case "$md_stat_fault" in
        pass) "$gnu_stat" "$@" ;;
        partial) "$gnu_stat" --printf '%f %s %n\0' -- "${md_files[0]}" ;;
        fail) return 9 ;;
        partial-fail) "$gnu_stat" --printf '%f %s %n\0' -- "${md_files[0]}"; return 9 ;;
        extra) "$gnu_stat" "$@"; printf '81a4 0 /unexpected\0' ;;
        nul) "$gnu_stat" "$@"; printf '\0' ;;
        empty) return 0 ;;
        over-bound) printf '%16385s' '' ;;
        missing-nul) "$gnu_stat" --printf '%f %s %n' -- "${md_files[@]}" ;;
        swapped) "$gnu_stat" --printf '%f %s %n\0' -- "${md_files[1]}" "${md_files[0]}" "${md_files[@]:2}" ;;
        *)
            for md_path in "${md_files[@]}"; do
                case "$md_stat_fault" in
                    malformed) printf '81a4 nope %s\0' "$md_path" ;;
                    noncanonical-size) printf '81a4 00 %s\0' "$md_path" ;;
                    uppercase-mode) printf '81A4 0 %s\0' "$md_path" ;;
                    directory-mode) printf '41ed 0 %s\0' "$md_path" ;;
                    unreadable-mode) printf '8000 0 %s\0' "$md_path" ;;
                    wrong-path) printf '81a4 0 %s.wrong\0' "$md_path" ;;
                    *) return 2 ;;
                esac
            done
            ;;
    esac
}

md_frame_case() {
    local label=$1 md_root=$2 md_list=$3 md_select=$4 md_expected=$5
    local md_stat_fault=pass old=0 new=0 md_batches
    if legacy_frame "$md_root" provenance-metadata/v1 "$md_list" > "$scratch/frame.old"; then :; else old=$?; fi
    : > "$scratch/stat.calls"; : > "$scratch/stat.argv"
    if (
        _prov_batch_supported() { [[ "$md_select" == batch ]]; }
        stat() { md_stat "$@"; }
        prov_files_frame "$md_root" provenance-metadata/v1 "$md_list"
    ) > "$scratch/frame.new"; then :; else new=$?; fi
    assert_equal "$md_expected" "$old" "$label legacy frame"
    assert_equal "$old" "$new" "$label current frame"
    cmp -s "$scratch/frame.old" "$scratch/frame.new" || md_fail "$label frame bytes/failure prefix"
    md_batches=$(grep -c '^batch:' "$scratch/stat.calls" || :)
    if [[ "$md_select" == scalar ]]; then assert_equal 0 "$md_batches" "$label preselected scalar"; fi
    if [[ "$md_select" == batch && "$md_expected" == 0 && -s "$md_list" ]]; then
        (( md_batches > 0 )) || md_fail "$label never batched"
    fi
    awk -F: '$1 == "batch" && ($2 < 1 || $2 > 64 || $3 > 8192) { exit 1 }' "$scratch/stat.calls" || md_fail "$label batch limits"
    md_pass "frame $label"
}

md_frame_root="$scratch/frame-tree"
mkdir -p "$md_frame_root"
printf 'A\0B\n\377' > "$md_frame_root/binary"
printf '' > "$md_frame_root/empty"
printf 'spaces\n' > "$md_frame_root/space path"
printf 'quotes\n' > "$md_frame_root/both'\"quotes"
md_punct_name='semicolon;$()'
printf 'punctuation\n' > "$md_frame_root/$md_punct_name"
printf 'execute\n' > "$md_frame_root/executable"
chmod 751 "$md_frame_root/executable"
printf '%s\n' binary empty executable 'space path' "both'\"quotes" "$md_punct_name" | LC_ALL=C sort > "$scratch/frame.paths"
md_frame_case binary-quotes-modes "$md_frame_root" "$scratch/frame.paths" batch 0
md_frame_case preselected-capacity "$md_frame_root" "$scratch/frame.paths" scalar 0
md_frame_case empty "$md_frame_root" "$scratch/paths-empty" batch 0
cp -- "$scratch/frame.paths" "$scratch/frame-missing.paths"
printf '%s\n' zz-missing >> "$scratch/frame-missing.paths"
md_frame_case missing-prefix "$md_frame_root" "$scratch/frame-missing.paths" batch 1
md_frame_case missing-scalar-prefix "$md_frame_root" "$scratch/frame-missing.paths" scalar 1
for ((md_index=0; md_index<130; md_index++)); do
    printf -v md_name 'chunk-%03d' "$md_index"
    printf '%s\n' "$md_name" > "$md_frame_root/$md_name"
    printf '%s\n' "$md_name"
done > "$scratch/chunks.paths"
md_frame_case count-chunks "$md_frame_root" "$scratch/chunks.paths" batch 0
assert_equal 3 "$(grep -c '^batch:' "$scratch/stat.calls")" 'count chunk split'
for ((md_index=0; md_index<40; md_index++)); do
    printf -v md_name 'long-%03d-%0220d' "$md_index" 0
    printf x > "$md_frame_root/$md_name"
    printf '%s\n' "$md_name"
done > "$scratch/byte-chunks.paths"
md_frame_case byte-chunks "$md_frame_root" "$scratch/byte-chunks.paths" batch 0
(( $(grep -c '^batch:' "$scratch/stat.calls") > 1 )) || md_fail 'byte chunk split'
printf '%s\n' binary empty > "$scratch/stat-fault.paths"

md_stat_case() {
    local md_stat_fault=$1 md_read_fault=${2:-none} md_status=0 md_row_reads=0
    : > "$scratch/stat.calls"; : > "$scratch/stat.argv"; : > "$scratch/stat.fallback"
    : > "$scratch/stat.reads"
    if (
        _prov_batch_supported() { return 0; }
        _prov_frame_files_scalar() { printf 'fallback\n' >> "$scratch/stat.fallback"; return 0; }
        stat() { md_stat "$@"; }
        read() {
            local md_target=${!#} md_rc=0
            if [[ "$md_target" == row ]]; then
                md_row_reads=$((md_row_reads + 1))
                printf 'row\n' >> "$metadata_scratch/stat.reads"
                case "$md_read_fault" in
                    prefix)
                        if (( md_row_reads > 2 )); then printf -v "$md_target" ''; return 1; fi ;;
                    partial-status1) builtin read -r -n 1 "$md_target" || :; return 1 ;;
                    error) return 2 ;;
                esac
            fi
            if builtin read "$@"; then md_rc=0; else md_rc=$?; fi
            return "$md_rc"
        }
        prov_files_frame "$md_frame_root" provenance-metadata/v1 "$scratch/stat-fault.paths"
    ) > "$scratch/stat.out" 2> "$scratch/stat.err"; then :; else md_status=$?; fi
    [[ "$md_status" != 0 && ! -s "$scratch/stat.fallback" ]] || md_fail "stat $md_stat_fault/$md_read_fault green/fallback"
    assert_equal 1 "$(grep -c '^batch:' "$scratch/stat.calls")" "stat $md_stat_fault invocation"
    [[ "$(tail -n 1 "$scratch/stat.calls")" == batch:* ]] || md_fail 'scalar stat after failed batch'
    if [[ "$md_read_fault" != none ]]; then [[ -s "$scratch/stat.reads" ]] || md_fail 'stat read fault not exercised'; fi
    md_pass "stat $md_stat_fault/$md_read_fault rejects without fallback"
}
for md_case in partial fail partial-fail malformed noncanonical-size uppercase-mode directory-mode unreadable-mode extra nul empty over-bound missing-nul; do
    md_stat_case "$md_case"
done
md_stat_case extra prefix
md_stat_case nul prefix
md_stat_case pass partial-status1
md_stat_case pass error

md_capture_paths=(
    VERSION
    scripts/bootstrap_seed.sh scripts/build_stage1_from_seed.sh scripts/provenance.sh
    scripts/seed_manifest.sh scripts/stage1_cache.sh
    stdlib/runtime.c stdlib/runtime.h selfhost/main.nq
    bootstrap/seed/nauqc-seed.c bootstrap/seed/runtime.c bootstrap/seed/runtime.h
    "bootstrap/seed/a file 'quoted'" bootstrap/seed/b-dir/file bootstrap/seed/c-file
)
printf '%s\n' "${md_capture_paths[@]}" | LC_ALL=C sort > "$scratch/capture.paths"
md_make_capture_tree() {
    local md_root=$1 md_path
    mkdir -p -- "$md_root"
    for md_path in "${md_capture_paths[@]}"; do
        mkdir -p -- "$md_root/$(dirname -- "$md_path")"
        printf 'fixture %s\n' "$md_path" > "$md_root/$md_path"
        chmod 640 "$md_root/$md_path"
    done
    printf 'seed\0binary\n\377' > "$md_root/bootstrap/seed/runtime.c"
    chmod 751 "$md_root/scripts/bootstrap_seed.sh"
    chmod 444 "$md_root/stdlib/runtime.h"
}

legacy_copy() {
    local md_root=$1 md_dest=$2 md_list=$3 md_path
    legacy_validate_paths "$md_list" || return 1
    mkdir -p -- "$md_dest" || return 1
    while IFS= read -r md_path; do
        legacy_regular "$md_root/$md_path" || return 1
        mkdir -p -- "$md_dest/$(dirname -- "$md_path")" || return 1
        "$gnu_cp" --preserve=mode -- "$md_root/$md_path" "$md_dest/$md_path" || return 1
    done < "$md_list"
}

md_cp() {
    local md_count=$(($# - 3))
    printf 'copy:%s\n' "$md_count" >> "$metadata_scratch/copy.calls"
    printf '%q ' "$@" >> "$metadata_scratch/copy.argv"; printf '\n' >> "$metadata_scratch/copy.argv"
    "$gnu_cp" "$@" || return $?
    if [[ "$md_copy_fault" == fail ]]; then return 9; fi
    if [[ "$md_copy_fault" == mutate && "$md_mutated" == false ]]; then
        printf 'persistent source mutation\n' >> "$md_copy_root/VERSION"
        md_mutated=true
    fi
}

md_compare_copies() {
    local md_source=$1 md_dest=$2 md_reference=$3 md_path
    find "$md_dest" -type f -printf '%P\n' | LC_ALL=C sort > "$scratch/capture.actual"
    cmp -s "$scratch/capture.paths" "$scratch/capture.actual" || md_fail 'captured exact membership'
    while IFS= read -r md_path; do
        cmp -s "$md_source/$md_path" "$md_dest/$md_path" || md_fail "capture content $md_path"
        cmp -s "$md_reference/$md_path" "$md_dest/$md_path" || md_fail "legacy copy $md_path"
        assert_equal "$("$gnu_stat" -c '%a' -- "$md_source/$md_path")" \
            "$("$gnu_stat" -c '%a' -- "$md_dest/$md_path")" "capture exact raw mode $md_path"
    done < "$scratch/capture.paths"
    assert_equal "$(legacy_files_digest "$md_source" nauqtype-build-inputs/v2 "$scratch/capture.paths")" \
        "$(legacy_files_digest "$md_dest" nauqtype-build-inputs/v2 "$scratch/capture.paths")" 'capture frozen hash'
}

md_copy_case() {
    local md_select=$1 md_copy_root="$scratch/copy-$1-source" md_dest="$scratch/copy-$1-dest"
    local md_reference="$scratch/copy-$1-legacy" md_copy_fault=pass md_mutated=false md_expected md_path md_parent=''
    local md_previous='' md_count=0
    md_make_capture_tree "$md_copy_root"
    md_expected=$(legacy_files_digest "$md_copy_root" nauqtype-build-inputs/v2 "$scratch/capture.paths")
    legacy_copy "$md_copy_root" "$md_reference" "$scratch/capture.paths"
    : > "$scratch/copy.calls"; : > "$scratch/copy.argv"
    (
        _prov_batch_supported() { [[ "$md_select" == batch ]]; }
        cp() { md_cp "$@"; }
        prov_capture_inputs "$md_copy_root" "$md_dest" "$scratch/capture.paths" "$md_expected"
    ) > "$scratch/copy.out" 2> "$scratch/copy.err" || md_fail "capture $md_select failed"
    [[ ! -s "$scratch/copy.out" && ! -s "$scratch/copy.err" ]] || md_fail 'capture public output'
    md_compare_copies "$md_copy_root" "$md_dest" "$md_reference"
    : > "$scratch/copy.expected"
    while IFS= read -r md_path; do
        if [[ "$md_select" == scalar ]]; then
            printf 'copy:1\n' >> "$scratch/copy.expected"
        else
            md_parent=''
            [[ "$md_path" != */* ]] || md_parent=${md_path%/*}
            if (( md_count > 0 )) && [[ "$md_previous" != "$md_parent" ]]; then
                printf 'copy:%s\n' "$md_count" >> "$scratch/copy.expected"
                md_count=0
            fi
            md_previous=$md_parent
            md_count=$((md_count + 1))
        fi
    done < "$scratch/capture.paths"
    if (( md_count > 0 )); then printf 'copy:%s\n' "$md_count" >> "$scratch/copy.expected"; fi
    cmp -s "$scratch/copy.expected" "$scratch/copy.calls" || md_fail "capture $md_select grouping/call count"
    md_pass "capture $md_select exact membership/hash/raw modes/interleaved groups"
}
md_copy_case batch
md_copy_case scalar

md_copy_fault_case() {
    local md_copy_fault=$1 md_copy_root="$scratch/copy-$1-source" md_dest="$scratch/copy-$1-rejected"
    local md_mutated=false md_expected md_status=0 md_captured
    md_make_capture_tree "$md_copy_root"
    md_expected=$(legacy_files_digest "$md_copy_root" nauqtype-build-inputs/v2 "$scratch/capture.paths")
    : > "$scratch/copy.calls"; : > "$scratch/copy.argv"
    if (
        _prov_batch_supported() { return 0; }
        cp() { md_cp "$@"; }
        prov_capture_inputs "$md_copy_root" "$md_dest" "$scratch/capture.paths" "$md_expected"
    ) > "$scratch/copy.out" 2> "$scratch/copy.err"; then :; else md_status=$?; fi
    [[ "$md_status" != 0 ]] || md_fail "copy $md_copy_fault accepted"
    if [[ "$md_copy_fault" == fail ]]; then
        assert_equal 1 "$(wc -l < "$scratch/copy.calls")" 'failed cp no retry/fallback'
    else
        md_captured=$(legacy_files_digest "$md_dest" nauqtype-build-inputs/v2 "$scratch/capture.paths")
        assert_equal "$md_expected" "$md_captured" 'mutation capture itself unchanged'
        [[ "$(legacy_files_digest "$md_copy_root" nauqtype-build-inputs/v2 "$scratch/capture.paths")" != "$md_expected" ]] || md_fail 'mutation did not persist'
        grep -q 'inputs changed during capture' "$scratch/copy.err" || md_fail 'original-source guard not exercised'
    fi
    md_pass "capture rejects $md_copy_fault"
}
md_copy_fault_case fail
md_copy_fault_case mutate

md_copy_symlink_case() {
    local md_kind=$1 md_source="$scratch/link-$1-source" md_dest="$scratch/link-$1-dest"
    local md_expected md_status=0
    md_make_capture_tree "$md_source"
    md_expected=$(legacy_files_digest "$md_source" nauqtype-build-inputs/v2 "$scratch/capture.paths")
    case "$md_kind" in
        source-leaf)
            rm -- "$md_source/bootstrap/seed/runtime.c"
            ln -s "$md_source/bootstrap/seed/runtime.h" "$md_source/bootstrap/seed/runtime.c" ;;
        source-parent)
            mv -- "$md_source/bootstrap/seed" "$scratch/link-seed-real"
            ln -s "$scratch/link-seed-real" "$md_source/bootstrap/seed" ;;
        dest-leaf)
            mkdir -- "$scratch/link-dest-real"
            ln -s "$scratch/link-dest-real" "$md_dest" ;;
        dest-parent)
            mkdir -- "$scratch/link-parent-real"
            ln -s "$scratch/link-parent-real" "$scratch/link-parent"
            md_dest="$scratch/link-parent/capture" ;;
    esac
    if prov_capture_inputs "$md_source" "$md_dest" "$scratch/capture.paths" "$md_expected" \
        > "$scratch/copy.out" 2> "$scratch/copy.err"; then :; else md_status=$?; fi
    [[ "$md_status" != 0 ]] || md_fail "capture $md_kind symlink accepted"
    md_pass "capture rejects $md_kind symlink"
}
md_copy_symlink_case source-leaf
md_copy_symlink_case source-parent
md_copy_symlink_case dest-leaf
md_copy_symlink_case dest-parent

assert_equal 84 "$passed" 'existing metadata cases retained before walk extension'
gnu_find=$(command -v find)

# Frozen pre-extension walk, using the independent scalar/path checks above.
md_walk_legacy() (
    local md_root=$1 md_subtree=$2 md_kind=${3:-all} md_tmp md_path md_rel LC_ALL=C
    legacy_directory "$md_root" && legacy_safe_relative "$md_subtree" || exit 1
    legacy_directory "$md_root/$md_subtree" || exit 1
    md_tmp=$(mktemp -d "$metadata_scratch/walk-legacy-XXXXXX") || exit 1
    trap 'rm -rf -- "$md_tmp"' EXIT
    find "$md_root/$md_subtree" -print0 > "$md_tmp/entries" || exit 1
    : > "$md_tmp/paths"
    while IFS= read -r -d '' md_path; do
        md_rel=${md_path#"$md_root/"}
        legacy_safe_relative "$md_rel" && [[ ! -L "$md_path" ]] || exit 1
        if [[ -d "$md_path" ]]; then continue; fi
        legacy_regular "$md_path" || exit 1
        if [[ "$md_kind" != all && "$md_rel" != *.nq ]]; then
            [[ "$md_kind" == source ]] || exit 1
            continue
        fi
        printf '%s\n' "$md_rel" >> "$md_tmp/paths" || exit 1
    done < "$md_tmp/entries"
    LC_ALL=C sort "$md_tmp/paths"
)

md_walk_prefix() {
    printf 'd\000755\000%s\000f\000644\000%s\000' "$md_walk_base" "$md_walk_base/a.nq"
}

# Only walk/version formats are intercepted. Logs live outside production scratch.
md_find() {
    printf '%q ' "$@" >> "$metadata_scratch/walk.argv"; printf '\n' >> "$metadata_scratch/walk.argv"
    if [[ "${1-}" == --version ]]; then
        printf 'version\n' >> "$metadata_scratch/walk.calls"
        case "$md_walk_capability" in
            gnu) "$gnu_find" "$@" ;;
            unknown) printf 'find (unknown provider) 1\n' ;;
            empty) return 0 ;;
            error) printf 'unsupported version query\n' >&2; return 9 ;;
            *) return 2 ;;
        esac
        return $?
    fi
    if [[ $# == 2 && "$1" == "$md_walk_base" && "$2" == -print0 ]]; then
        printf 'print0\n' >> "$metadata_scratch/walk.calls"
        if [[ "$md_walk_fault" == legacy-fail ]]; then printf '%s\0' "$md_walk_base"; return 9; fi
        "$gnu_find" "$@"
        return $?
    fi
    [[ $# == 3 && "$1" == "$md_walk_base" && "$2" == -printf && "$3" == '%y\0%m\0%p\0' ]] || return 2
    printf 'printf\n' >> "$metadata_scratch/walk.calls"
    case "$md_walk_fault" in
        pass) "$gnu_find" "$@" ;;
        nonzero) return 9 ;;
        nonzero-valid) "$gnu_find" "$@" || return $?; return 9 ;;
        empty-spool) return 0 ;;
        partial-root-type) printf d ;;
        partial-root-mode) printf 'd\000755' ;;
        partial-root-path) printf 'd\000755\000%s' "$md_walk_base" ;;
        partial-type) md_walk_prefix; printf f ;;
        partial-mode) md_walk_prefix; printf 'f\000644' ;;
        partial-path) md_walk_prefix; printf 'f\000644\000%s' "$md_walk_base/nested/b.nq" ;;
        trailing-byte) md_walk_prefix; printf x ;;
        trailing-nul) md_walk_prefix; printf '\0' ;;
        trailing-lf) md_walk_prefix; printf '\n' ;;
        missing-root) printf 'f\000644\000%s\000' "$md_walk_base/a.nq" ;;
        wrong-root-type) printf 'f\000644\000%s\000' "$md_walk_base" ;;
        out-of-root) md_walk_prefix; printf 'f\000644\000%s\000' "$metadata_scratch/outside.nq" ;;
        sibling-prefix) md_walk_prefix; printf 'f\000644\000%s\000' "$md_walk_base-other/a.nq" ;;
        relative-path) md_walk_prefix; printf 'f\000644\000scan/a.nq\000' ;;
        empty-type|unknown-type|multi-type|directory-as-file|file-as-directory)
            md_walk_prefix
            case "$md_walk_fault" in
                empty-type) printf '\000644\000%s\000' "$md_walk_base/nested/b.nq" ;;
                unknown-type) printf 'x\000644\000%s\000' "$md_walk_base/nested/b.nq" ;;
                multi-type) printf 'ff\000644\000%s\000' "$md_walk_base/nested/b.nq" ;;
                directory-as-file) printf 'f\000755\000%s\000' "$md_walk_base/nested" ;;
                file-as-directory) printf 'd\000644\000%s\000' "$md_walk_base/nested/b.nq" ;;
            esac ;;
        mode-empty|mode-nonoctal|mode-long|mode-newline|mode-unreadable|mode-ignored-output)
            md_walk_prefix
            case "$md_walk_fault" in
                mode-empty) printf 'f\000\000%s\000' "$md_walk_base/nested/b.nq" ;;
                mode-nonoctal) printf 'f\000648\000%s\000' "$md_walk_base/nested/b.nq" ;;
                mode-long) printf 'f\000100644\000%s\000' "$md_walk_base/nested/b.nq" ;;
                mode-newline) printf 'f\000644\n\000%s\000' "$md_walk_base/nested/b.nq" ;;
                mode-unreadable) printf 'f\0000000\000%s\000' "$md_walk_base/nested/b.nq" ;;
                mode-ignored-output) printf 'f\0000000\000%s\000' "$md_walk_base/output.bin" ;;
            esac ;;
        mutate-delete|mutate-leaf|mutate-parent|mutate-file-type|mutate-directory-type)
            "$gnu_find" "$@" || return $?
            case "$md_walk_fault" in
                mutate-delete) rm -- "$md_walk_base/a.nq" ;;
                mutate-leaf)
                    rm -- "$md_walk_base/a.nq"
                    ln -s "$metadata_scratch/outside.nq" "$md_walk_base/a.nq" ;;
                mutate-parent)
                    mv -- "$md_walk_base/nested" "$md_walk_base-parent-real"
                    ln -s "$md_walk_base-parent-real" "$md_walk_base/nested" ;;
                mutate-file-type) rm -- "$md_walk_base/a.nq"; mkdir -- "$md_walk_base/a.nq" ;;
                mutate-directory-type) rmdir -- "$md_walk_base/empty"; printf x > "$md_walk_base/empty" ;;
            esac ;;
        *) return 2 ;;
    esac
}

md_walk_reset_logs() {
    : > "$metadata_scratch/walk.calls"; : > "$metadata_scratch/walk.argv"
}

md_walk_case() {
    local md_label=$1 md_root=$2 md_subtree=$3 md_kind=$4 md_expected=$5 md_expected_paths=$6
    local md_walk_capability=gnu md_walk_fault=pass md_walk_base="$2/$3"
    local md_before_walk=${7:-false} md_old=0 md_retained=0 md_new=0
    if md_walk_legacy "$md_root" "$md_subtree" "$md_kind" > "$metadata_scratch/walk.old" 2> "$metadata_scratch/walk.old.err"; then :; else md_old=$?; fi
    if _prov_tree_paths_legacy "$md_root" "$md_subtree" "$md_kind" > "$metadata_scratch/walk.retained" 2> "$metadata_scratch/walk.retained.err"; then :; else md_retained=$?; fi
    md_walk_reset_logs
    if (
        find() { md_find "$@"; }
        _prov_tree_paths_legacy() { printf 'fallback\n' >> "$metadata_scratch/walk.calls"; return 0; }
        prov_tree_paths "$md_root" "$md_subtree" "$md_kind"
    ) > "$metadata_scratch/walk.new" 2> "$metadata_scratch/walk.new.err"; then :; else md_new=$?; fi
    assert_equal "$md_expected" "$md_old" "walk $md_label frozen status"
    assert_equal "$md_old" "$md_retained" "walk $md_label retained legacy status"
    assert_equal "$md_old" "$md_new" "walk $md_label indexed status"
    cmp -s "$metadata_scratch/walk.old" "$metadata_scratch/walk.retained" || md_fail "walk $md_label retained bytes"
    cmp -s "$metadata_scratch/walk.old" "$metadata_scratch/walk.new" || md_fail "walk $md_label differential bytes"
    if [[ "$md_expected" == 0 ]]; then
        cmp -s "$md_expected_paths" "$metadata_scratch/walk.new" || md_fail "walk $md_label expected sorted bytes"
        [[ ! -s "$metadata_scratch/walk.new.err" ]] || md_fail "walk $md_label successful stderr"
    else
        [[ ! -s "$metadata_scratch/walk.new" ]] || md_fail "walk $md_label rejected output"
    fi
    if [[ "$md_before_walk" == true ]]; then : > "$metadata_scratch/walk.expected";
    else printf 'version\nprintf\n' > "$metadata_scratch/walk.expected"; fi
    cmp -s "$metadata_scratch/walk.expected" "$metadata_scratch/walk.calls" || md_fail "walk $md_label selection/fallback"
    md_pass "walk $md_label"
}

md_walk_tree="$scratch/walk-valid"
mkdir -p -- "$md_walk_tree/scan/nested" "$md_walk_tree/scan/empty directory"
md_walk_names=(a.nq z-last.nq nested/b.nq 'nested/empty file.nq' 'space path.nq' "both'\"quotes.nq" 'semicolon;$().nq' .hidden.nq -option.nq)
for md_name in "${md_walk_names[@]}"; do printf 'walk %s\n' "$md_name" > "$md_walk_tree/scan/$md_name"; done
: > "$md_walk_tree/scan/nested/empty file.nq"
printf 'binary\000payload\n\377' > "$md_walk_tree/scan/nested/output.bin"
chmod 751 "$md_walk_tree/scan/z-last.nq"
chmod 444 "$md_walk_tree/scan/nested/b.nq"
printf '%s\n' "${md_walk_names[@]/#/scan/}" | LC_ALL=C sort > "$scratch/walk.source.paths"
{ cat "$scratch/walk.source.paths"; printf '%s\n' scan/nested/output.bin; } | LC_ALL=C sort > "$scratch/walk.all.paths"
md_walk_case all-nested "$md_walk_tree" scan all 0 "$scratch/walk.all.paths"
md_walk_case source-nested "$md_walk_tree" scan source 0 "$scratch/walk.source.paths"
md_walk_case snapshot-rejects-output "$md_walk_tree" scan snapshot 1 "$scratch/paths-empty"
rm -- "$md_walk_tree/scan/nested/output.bin"
md_walk_case snapshot-nested "$md_walk_tree" scan snapshot 0 "$scratch/walk.source.paths"
mkdir -p -- "$scratch/walk-empty/scan/nested empty"
for md_kind in all source snapshot; do md_walk_case "empty-$md_kind" "$scratch/walk-empty" scan "$md_kind" 0 "$scratch/paths-empty"; done

for md_bad in newline tab cr backslash non-ascii del directory unreadable-source unreadable-output symlink-source symlink-output symlink-directory fifo-source fifo-output; do
    md_bad_root="$scratch/walk-bad-$md_bad"
    mkdir -p -- "$md_bad_root/scan"
    printf 'valid prefix\n' > "$md_bad_root/scan/a.nq"
    case "$md_bad" in
        newline) md_name=$'bad\nname.output' ;;
        tab) md_name=$'bad\tname.output' ;;
        cr) md_name=$'bad\rname.output' ;;
        backslash) md_name='bad\name.output' ;;
        non-ascii) md_name=$'bad-\200.output' ;;
        del) md_name=$'bad-\177.output' ;;
        directory) mkdir -- "$md_bad_root/scan/"$'bad\ndir'; md_name=$'bad\ndir/child.nq' ;;
        unreadable-source|symlink-source|fifo-source) md_name=z-bad.nq ;;
        *) md_name=z-bad.output ;;
    esac
    case "$md_bad" in
        unreadable-*) printf x > "$md_bad_root/scan/$md_name"; chmod 000 "$md_bad_root/scan/$md_name" ;;
        symlink-source|symlink-output) ln -s a.nq "$md_bad_root/scan/$md_name" ;;
        symlink-directory) ln -s "$md_walk_tree/scan/nested" "$md_bad_root/scan/$md_name" ;;
        fifo-*) mkfifo -- "$md_bad_root/scan/$md_name" ;;
        *) printf x > "$md_bad_root/scan/$md_name" ;;
    esac
    md_walk_case "$md_bad" "$md_bad_root" scan source 1 "$scratch/paths-empty"
done
ln -s "$md_walk_tree" "$scratch/walk-root-link"
md_walk_case symlink-root "$scratch/walk-root-link" scan all 1 "$scratch/paths-empty" true
ln -s "$md_walk_tree" "$scratch/walk-ancestor-link"
md_walk_case symlink-ancestor "$scratch" walk-ancestor-link/scan all 1 "$scratch/paths-empty" true
md_walk_case missing-subtree "$md_walk_tree" missing source 1 "$scratch/paths-empty" true

md_walk_capability_case() {
    local md_walk_capability=$1 md_walk_fault=${2:-pass} md_walk_base="$md_walk_tree/scan" md_status=0
    md_walk_reset_logs
    if (
        find() { md_find "$@"; }
        _prov_tree_paths_legacy() { printf 'legacy\n' >> "$metadata_scratch/walk.calls"; md_walk_legacy "$@"; }
        prov_tree_paths "$md_walk_tree" scan source
    ) > "$metadata_scratch/walk.new" 2> "$metadata_scratch/walk.new.err"; then :; else md_status=$?; fi
    if [[ "$md_walk_fault" == pass ]]; then
        assert_equal 0 "$md_status" "walk capability $md_walk_capability"
        cmp -s "$scratch/walk.source.paths" "$metadata_scratch/walk.new" || md_fail 'legacy capability bytes'
    else
        [[ "$md_status" != 0 && ! -s "$metadata_scratch/walk.new" ]] || md_fail 'failed legacy walk accepted/published'
    fi
    [[ ! -s "$metadata_scratch/walk.new.err" ]] || md_fail 'capability query stderr escaped'
    printf 'version\nlegacy\nprint0\n' > "$metadata_scratch/walk.expected"
    cmp -s "$metadata_scratch/walk.expected" "$metadata_scratch/walk.calls" || md_fail 'legacy not preselected before walk'
    md_pass "walk capability $md_walk_capability/$md_walk_fault preselected legacy"
}
md_walk_capability_case unknown
md_walk_capability_case empty
md_walk_capability_case error
md_walk_capability_case unknown legacy-fail

md_walk_fault_case() {
    local md_walk_fault=$1 md_walk_capability=gnu md_root="$scratch/walk-fault-$1" md_status=0 md_after=0
    local md_walk_base="$scratch/walk-fault-$1/scan"
    mkdir -p -- "$md_walk_base/nested" "$md_walk_base/empty" "$md_walk_base-other"
    printf a > "$md_walk_base/a.nq"; printf b > "$md_walk_base/nested/b.nq"
    printf x > "$md_walk_base/output.bin"; printf x > "$md_walk_base-other/a.nq"
    printf x > "$metadata_scratch/outside.nq"
    md_walk_reset_logs
    if (
        find() { md_find "$@"; }
        _prov_tree_paths_legacy() { printf 'fallback\n' >> "$metadata_scratch/walk.calls"; return 0; }
        prov_tree_paths "$md_root" scan source
    ) > "$metadata_scratch/walk.new" 2> "$metadata_scratch/walk.new.err"; then :; else md_status=$?; fi
    [[ "$md_status" != 0 && ! -s "$metadata_scratch/walk.new" ]] || md_fail "walk $md_walk_fault green/published prefix"
    printf 'version\nprintf\n' > "$metadata_scratch/walk.expected"
    cmp -s "$metadata_scratch/walk.expected" "$metadata_scratch/walk.calls" || md_fail "walk $md_walk_fault retry/fallback"
    if [[ "$md_walk_fault" == mutate-* ]]; then
        if md_walk_legacy "$md_root" scan source > "$metadata_scratch/walk.after" 2> "$metadata_scratch/walk.after.err"; then :; else md_after=$?; fi
        if [[ "$md_walk_fault" == mutate-leaf || "$md_walk_fault" == mutate-parent ]]; then
            [[ "$md_after" != 0 && ! -s "$metadata_scratch/walk.after" ]] || md_fail 'persistent symlink mutation accepted'
        else
            assert_equal 0 "$md_after" 'fresh legacy walk of changed valid tree'
            if [[ "$md_walk_fault" == mutate-directory-type ]]; then
                printf 'scan/a.nq\nscan/nested/b.nq\n' > "$metadata_scratch/walk.expected.after"
            else
                printf 'scan/nested/b.nq\n' > "$metadata_scratch/walk.expected.after"
            fi
            cmp -s "$metadata_scratch/walk.expected.after" "$metadata_scratch/walk.after" || md_fail 'persistent changed-tree bytes'
        fi
        case "$md_walk_fault" in
            mutate-delete) [[ ! -e "$md_walk_base/a.nq" ]] ;;
            mutate-leaf) [[ -L "$md_walk_base/a.nq" ]] ;;
            mutate-parent) [[ -L "$md_walk_base/nested" ]] ;;
            mutate-file-type) [[ -d "$md_walk_base/a.nq" ]] ;;
            mutate-directory-type) [[ -f "$md_walk_base/empty" ]] ;;
        esac || md_fail "walk $md_walk_fault fixture did not persist"
    fi
    md_pass "walk $md_walk_fault rejects without output/fallback"
}
for md_fault in nonzero nonzero-valid empty-spool partial-root-type partial-root-mode partial-root-path partial-type partial-mode partial-path trailing-byte trailing-nul trailing-lf missing-root wrong-root-type out-of-root sibling-prefix relative-path empty-type unknown-type multi-type directory-as-file file-as-directory mode-empty mode-nonoctal mode-long mode-newline mode-unreadable mode-ignored-output mutate-delete mutate-leaf mutate-parent mutate-file-type mutate-directory-type; do
    md_walk_fault_case "$md_fault"
done

assert_equal 145 "$passed" 'existing metadata and walk cases retained before hash rows'
md_stat_case swapped
gnu_sha256sum=$(command -v sha256sum)

# Independent old mode/hash loop, never consuming either new provider format.
md_hash_rows_legacy() {
    local md_root=$1 md_list=$2 md_path md_mode md_hash
    legacy_directory "$md_root" && legacy_validate_paths "$md_list" || return 1
    while IFS= read -r md_path; do
        md_mode=$(legacy_mode "$md_root/$md_path") || return 1
        md_hash=$("$gnu_sha256sum" < "$md_root/$md_path") || return 1
        md_hash=${md_hash%% *}
        [[ "$md_hash" =~ ^[0-9a-f]{64}$ ]] || return 1
        printf '%s\t%s\t%s\n' "$md_mode" "$md_hash" "$md_path" || return 1
    done < "$md_list"
}

md_hash_fixture() {
    local md_root=$1 md_count=$2 md_style=${3:-short} md_at md_name md_parent
    local -a md_names=(a-binary b-empty 'c executable' "d'\"quoted" e-parent/a e-parent/b 'f;$()' g-last)
    mkdir -p -- "$md_root"
    for ((md_at=0; md_at<md_count; md_at++)); do
        if [[ "$md_style" == long ]]; then printf -v md_name 'parent-%d/file-%03d-%0220d' "$((md_at % 3))" "$md_at" 0;
        elif (( md_at < 8 )); then md_name=${md_names[md_at]};
        else printf -v md_name 'parent-%d/file-%03d' "$((md_at % 3))" "$md_at"; fi
        md_parent=$md_root
        [[ "$md_name" != */* ]] || md_parent="$md_root/${md_name%/*}"
        mkdir -p -- "$md_parent"
        printf 'hash fixture %s\n' "$md_name" > "$md_root/$md_name"
        chmod 640 "$md_root/$md_name"
        case "$md_at" in
            0) printf 'A\000B\n\377' > "$md_root/$md_name" ;;
            1) : > "$md_root/$md_name" ;;
            2) chmod 751 "$md_root/$md_name" ;;
            3) chmod 444 "$md_root/$md_name" ;;
        esac
        printf '%s\n' "$md_name"
    done
}

md_hash_batches() {
    local md_root=$1 md_list=$2 md_path md_full md_count=0 md_bytes=0
    while IFS= read -r md_path; do
        md_full="$md_root/$md_path"
        if (( md_count > 0 && (md_count == 64 || md_bytes + ${#md_full} + 1 > 8192) )); then
            printf 'batch:%s:%s\n' "$md_count" "$md_bytes"; md_count=0; md_bytes=0
        fi
        md_count=$((md_count + 1)); md_bytes=$((md_bytes + ${#md_full} + 1))
    done < "$md_list"
    if (( md_count > 0 )); then printf 'batch:%s:%s\n' "$md_count" "$md_bytes"; fi
}

md_sha() {
    local md_path md_bytes=0 md_hash
    printf '%q ' "$@" >> "$metadata_scratch/hash.argv"; printf '\n' >> "$metadata_scratch/hash.argv"
    if [[ "${1-}" == --version ]]; then
        printf 'version\n' >> "$metadata_scratch/hash.calls"
        case "$md_sha_capability" in
            gnu) "$gnu_sha256sum" "$@" ;;
            unknown) printf 'sha256sum (unknown provider) 1\n' ;;
            error) printf 'unsupported SHA version query\n' >&2; return 9 ;;
            *) return 2 ;;
        esac
        return $?
    fi
    if (( $# == 0 )); then
        printf 'stdin\n' >> "$metadata_scratch/hash.calls"
        "$gnu_sha256sum"
        return $?
    fi
    (( $# > 2 )) && [[ "$1" == --zero && "$2" == -- ]] || return 2
    local -a md_files=("${@:3}")
    for md_path in "${md_files[@]}"; do md_bytes=$((md_bytes + ${#md_path} + 1)); done
    printf 'batch:%s:%s\n' "${#md_files[@]}" "$md_bytes" >> "$metadata_scratch/hash.calls"
    case "$md_sha_fault" in
        pass) "$gnu_sha256sum" "$@" ;;
        fail) return 9 ;;
        partial) "$gnu_sha256sum" --zero -- "${md_files[0]}" ;;
        partial-fail) "$gnu_sha256sum" --zero -- "${md_files[0]}"; return 9 ;;
        missing-nul) "$gnu_sha256sum" "$@" | head -c -1 ;;
        extra) "$gnu_sha256sum" "$@"; "$gnu_sha256sum" --zero -- "${md_files[0]}" ;;
        nul) "$gnu_sha256sum" "$@"; printf '\0' ;;
        trailing-byte) "$gnu_sha256sum" "$@"; printf x ;;
        reordered) "$gnu_sha256sum" --zero -- "${md_files[1]}" "${md_files[0]}" "${md_files[@]:2}" ;;
        wrong-path) "$gnu_sha256sum" --zero -- "$md_hash_root/excluded" "${md_files[@]:1}" ;;
        badhash|uppercase-hash|short-hash|separator)
            case "$md_sha_fault" in
                badhash) printf -v md_hash '%064d' 0; md_hash="z${md_hash:1}" ;;
                uppercase-hash) printf -v md_hash '%064d' 0; md_hash="A${md_hash:1}" ;;
                short-hash) printf -v md_hash '%063d' 0 ;;
                separator) printf -v md_hash '%064d' 0 ;;
            esac
            for md_path in "${md_files[@]}"; do
                if [[ "$md_sha_fault" == separator ]]; then printf '%s *%s\0' "$md_hash" "$md_path";
                else printf '%s  %s\0' "$md_hash" "$md_path"; fi
            done ;;
        empty) return 0 ;;
        over-bound) printf '%16385s' '' ;;
        second-fail)
            if [[ $(grep -c '^batch:' "$metadata_scratch/hash.calls") == 2 ]]; then return 9; fi
            "$gnu_sha256sum" "$@" ;;
        mutate-leaf|mutate-parent)
            "$gnu_sha256sum" "$@" || return $?
            if [[ "$md_sha_fault" == mutate-leaf ]]; then
                rm -- "${md_files[0]}"; ln -s "${md_files[1]}" "${md_files[0]}"
            else
                mv -- "$md_hash_root/e-parent" "$md_hash_root/e-parent-real"
                ln -s "$md_hash_root/e-parent-real" "$md_hash_root/e-parent"
            fi ;;
        *) return 2 ;;
    esac
}

md_hash_reset_logs() {
    : > "$metadata_scratch/hash.calls"; : > "$metadata_scratch/hash.argv"; : > "$metadata_scratch/hash.fallback"
    : > "$metadata_scratch/stat.calls"; : > "$metadata_scratch/stat.argv"
}

md_hash_case() {
    local md_label=$1 md_hash_root=$2 md_list=$3 md_select=$4 md_count=$5
    local md_sha_capability=${6:-gnu} md_sha_fault=pass md_stat_fault=pass md_old=0 md_new=0 md_at
    if md_hash_rows_legacy "$md_hash_root" "$md_list" > "$scratch/hash.old"; then :; else md_old=$?; fi
    md_hash_reset_logs
    if (
        _prov_batch_supported() { [[ "$md_select" == batch ]]; }
        stat() { md_stat "$@"; }
        sha256sum() { md_sha "$@"; }
        prov_file_hash_rows "$md_hash_root" "$md_list"
    ) > "$scratch/hash.new" 2> "$scratch/hash.err"; then :; else md_new=$?; fi
    assert_equal 0 "$md_old" "hash rows $md_label frozen status"
    if [[ "$md_old" != "$md_new" ]]; then
        cat "$scratch/hash.err" "$scratch/hash.calls" >&2
    fi
    assert_equal "$md_old" "$md_new" "hash rows $md_label status"
    cmp -s "$scratch/hash.old" "$scratch/hash.new" || md_fail "hash rows $md_label exact ordered mode/hash/path bytes"
    [[ ! -s "$scratch/hash.err" ]] || md_fail "hash rows $md_label stderr"
    : > "$scratch/hash.expected"; : > "$scratch/hash.batch.expected"
    if (( md_count >= 8 )) && [[ "$md_select" == batch ]]; then
        printf 'version\n' >> "$scratch/hash.expected"
        if [[ "$md_sha_capability" == gnu ]]; then
            md_hash_batches "$md_hash_root" "$md_list" > "$scratch/hash.batch.expected"
            cat "$scratch/hash.batch.expected" >> "$scratch/hash.expected"
        fi
    fi
    if [[ ! -s "$scratch/hash.batch.expected" ]]; then
        for ((md_at=0; md_at<md_count; md_at++)); do printf 'stdin\n' >> "$scratch/hash.expected"; done
    fi
    cmp -s "$scratch/hash.expected" "$scratch/hash.calls" || md_fail "hash rows $md_label selection/empty stdin"
    grep '^batch:' "$scratch/stat.calls" > "$scratch/hash.stat.batches" || :
    cmp -s "$scratch/hash.batch.expected" "$scratch/hash.stat.batches" || md_fail "hash rows $md_label stat/hash chunk correspondence"
    awk -F: '$1 == "batch" && ($2 < 1 || $2 > 64 || $3 > 8192) { exit 1 }' "$scratch/hash.calls" || md_fail 'hash argv bounds'
    md_pass "hash rows $md_label exact legacy bytes/dispatch"
}

md_hash_root="$scratch/hash rows 'quoted'"
md_hash_fixture "$md_hash_root" 65 | LC_ALL=C sort > "$scratch/hash65.paths"
head -n 7 "$scratch/hash65.paths" > "$scratch/hash7.paths"
head -n 8 "$scratch/hash65.paths" > "$scratch/hash8.paths"
md_hash_case empty "$md_hash_root" "$scratch/paths-empty" batch 0
md_hash_case seven "$md_hash_root" "$scratch/hash7.paths" batch 7
md_hash_case eight "$md_hash_root" "$scratch/hash8.paths" batch 8
md_hash_case sixty-five "$md_hash_root" "$scratch/hash65.paths" batch 65
assert_equal 2 "$(grep -c '^batch:' "$scratch/hash.calls")" '65 hashes split into two bounded batches'
md_hash_case preselected-capacity "$md_hash_root" "$scratch/hash8.paths" scalar 8
md_hash_case preselected-unknown-sha "$md_hash_root" "$scratch/hash8.paths" batch 8 unknown
md_hash_case preselected-sha-query-error "$md_hash_root" "$scratch/hash8.paths" batch 8 error
md_hash_fixture "$scratch/hash-long-parents" 40 long | LC_ALL=C sort > "$scratch/hash-long.paths"
md_hash_case parent-byte-chunks "$scratch/hash-long-parents" "$scratch/hash-long.paths" batch 40
(( $(grep -c '^batch:' "$scratch/hash.calls") > 1 )) || md_fail 'long parent paths not byte-chunked'
md_hash_weird_root="$scratch/"$'hash\\root\nline'
md_hash_fixture "$md_hash_weird_root" 8 | LC_ALL=C sort > "$scratch/hash-weird.paths"
md_hash_case backslash-newline-root "$md_hash_weird_root" "$scratch/hash-weird.paths" batch 8

md_hash_fault_case() {
    local md_provider=$1 md_fault=$2 md_hash_root="$scratch/hash-fault-$1-$2" md_status=0 md_after=0 md_count=8
    local md_sha_capability=gnu md_sha_fault=pass md_stat_fault=pass
    [[ "$md_fault" != second-fail ]] || md_count=65
    md_hash_fixture "$md_hash_root" "$md_count" | LC_ALL=C sort > "$scratch/hash-fault.paths"
    printf excluded > "$md_hash_root/excluded"
    md_hash_rows_legacy "$md_hash_root" "$scratch/hash-fault.paths" > "$scratch/hash.before"
    if [[ "$md_provider" == stat ]]; then md_stat_fault=$md_fault; else md_sha_fault=$md_fault; fi
    md_hash_reset_logs
    if (
        _prov_batch_supported() { return 0; }
        _prov_file_hash_rows_scalar() { printf 'fallback\n' >> "$metadata_scratch/hash.fallback"; return 0; }
        stat() { md_stat "$@"; }
        sha256sum() { md_sha "$@"; }
        prov_file_hash_rows "$md_hash_root" "$scratch/hash-fault.paths"
    ) > "$scratch/hash.new" 2> "$scratch/hash.err"; then :; else md_status=$?; fi
    [[ "$md_status" != 0 && ! -s "$scratch/hash.fallback" ]] || md_fail "hash rows $md_provider/$md_fault green/fallback"
    if [[ "$md_fault" == second-fail ]]; then
        head -n 64 "$scratch/hash.before" > "$scratch/hash.prefix"
        cmp -s "$scratch/hash.prefix" "$scratch/hash.new" || md_fail 'failed second batch altered valid first-batch prefix'
    else
        [[ ! -s "$scratch/hash.new" ]] || md_fail "hash rows $md_provider/$md_fault published failed batch"
    fi
    assert_equal 1 "$(grep -c '^version$' "$scratch/hash.calls")" 'hash capability queried once before batch'
    [[ $(grep -c '^stdin$' "$scratch/hash.calls" || :) == 0 ]] || md_fail 'failed hash batch used scalar stdin'
    if [[ "$md_provider" == stat ]]; then
        assert_equal 0 "$(grep -c '^batch:' "$scratch/hash.calls" || :)" 'failed stat reached SHA provider'
        assert_equal 1 "$(grep -c '^batch:' "$scratch/stat.calls")" 'failed stat retried'
    elif [[ "$md_fault" == second-fail ]]; then
        assert_equal 2 "$(grep -c '^batch:' "$scratch/hash.calls")" 'second hash failure retried'
    else
        assert_equal 1 "$(grep -c '^batch:' "$scratch/hash.calls")" 'failed hash retried'
    fi
    if [[ "$md_fault" == mutate-* ]]; then
        if md_hash_rows_legacy "$md_hash_root" "$scratch/hash-fault.paths" > "$scratch/hash.after"; then :; else md_after=$?; fi
        [[ "$md_after" != 0 ]] || md_fail 'persistent hash-time symlink mutation lost'
        if [[ "$md_fault" == mutate-leaf ]]; then [[ -L "$md_hash_root/a-binary" ]];
        else [[ -L "$md_hash_root/e-parent" ]]; fi || md_fail 'hash mutation not persistent'
    fi
    md_pass "hash rows $md_provider/$md_fault rejects without failed fallback"
}
for md_fault in fail partial partial-fail extra nul swapped wrong-path missing-nul malformed directory-mode unreadable-mode; do md_hash_fault_case stat "$md_fault"; done
for md_fault in fail partial partial-fail missing-nul extra nul trailing-byte reordered wrong-path badhash uppercase-hash short-hash separator empty over-bound second-fail mutate-leaf mutate-parent; do md_hash_fault_case sha "$md_fault"; done

# The inventory and checksum observations must reacquire both bytes and modes.
md_hash_fresh_case() {
    local md_hash_root="$scratch/hash-fresh" md_sha_capability=gnu md_sha_fault=pass md_stat_fault=pass
    md_hash_fixture "$md_hash_root" 8 | LC_ALL=C sort > "$scratch/hash-fresh.paths"
    md_hash_rows_legacy "$md_hash_root" "$scratch/hash-fresh.paths" > "$scratch/hash.fresh.old"
    md_hash_reset_logs
    (
        _prov_batch_supported() { return 0; }
        stat() { md_stat "$@"; }; sha256sum() { md_sha "$@"; }
        prov_file_hash_rows "$md_hash_root" "$metadata_scratch/hash-fresh.paths" > "$metadata_scratch/hash.fresh.first" || exit 1
        printf 'C\000D\n\376' > "$md_hash_root/a-binary"
        chmod 640 "$md_hash_root/c executable"
        prov_file_hash_rows "$md_hash_root" "$metadata_scratch/hash-fresh.paths" > "$metadata_scratch/hash.fresh.second"
    ) || md_fail 'independent fresh hash-row invocations failed'
    md_hash_rows_legacy "$md_hash_root" "$scratch/hash-fresh.paths" > "$scratch/hash.fresh.after"
    cmp -s "$scratch/hash.fresh.old" "$scratch/hash.fresh.first" || md_fail 'first inventory observation bytes'
    cmp -s "$scratch/hash.fresh.after" "$scratch/hash.fresh.second" || md_fail 'fresh checksum observation bytes'
    if cmp -s "$scratch/hash.fresh.first" "$scratch/hash.fresh.second"; then md_fail 'persistent same-size content/mode mutation concealed'; fi
    assert_equal 2 "$(grep -c '^version$' "$scratch/hash.calls")" 'fresh invocations repeated capability dispatch'
    assert_equal 2 "$(grep -c '^batch:' "$scratch/hash.calls")" 'fresh checksum did not reacquire hashes'
    assert_equal 2 "$(grep -c '^batch:' "$scratch/stat.calls")" 'fresh checksum did not reacquire modes'
    md_pass 'hash rows independent inventory/checksum reads detect persistent same-size content/mode change'
}
md_hash_fresh_case

printf 'provenance metadata differential oracle passed (%s assertions; original 14 retained)\n' "$passed"
