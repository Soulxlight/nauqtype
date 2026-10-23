#!/usr/bin/env bash
# Shared, fail-closed byte encodings. Callers supply scratch paths, not hooks.

prov_error() { printf 'provenance: %s\n' "$*" >&2; return 1; }
prov_hex() { [[ "$1" =~ ^[0-9a-f]{64}$ ]]; }
prov_atom() { local LC_ALL=C; [[ "$1" =~ ^[A-Za-z0-9_.-]+$ ]]; }

prov_safe_relative() {
    local LC_ALL=C p=$1
    [[ -n "$p" && "$p" != /* && "$p" != */ && "$p" != *\\* && ! "$p" =~ [^\ -~] ]] || return 1
    case "/$p/" in *'//'*|*'/./'*|*'/../'*) return 1;; esac
}

prov_absolute() {
    local LC_ALL=C
    [[ "$1" == /* && "$1" != *'='* && ! "$1" =~ [^\ -~] ]]
}

prov_directory() {
    local p=$1
    [[ "$p" == /* ]] || return 1
    while [[ "$p" != / ]]; do
        [[ -d "$p" && ! -L "$p" ]] || return 1
        p=${p%/*}
        [[ -n "$p" ]] || p=/
    done
}

# Keep validation and the framed metadata in one observation, not cached state.
prov_file_metadata() {
    local p=$1 metadata mode size
    [[ -f "$p" && ! -L "$p" && -r "$p" ]] || return 1
    prov_directory "${p%/*}" || return 1
    metadata=$(stat -c '%a %s' -- "$p") || return 1
    [[ "$metadata" =~ ^([0-7]{1,4})\ (0|[1-9][0-9]*)$ ]] || return 1
    mode=${metadata%% *}; size=${metadata#* }
    (( (8#$mode & 0444) != 0 )) || return 1
    if (( (8#$mode & 0111) != 0 )); then mode=100755; else mode=100644; fi
    printf '%s %s\n' "$mode" "$size"
}

prov_regular() { prov_file_metadata "$1" > /dev/null; }

prov_mode() {
    local metadata
    metadata=$(prov_file_metadata "$1") || return 1
    printf '%s\n' "${metadata%% *}"
}

prov_sha256() {
    local digest
    prov_regular "$1" || return 1
    digest=$(sha256sum < "$1") || return 1
    digest=${digest%% *}
    prov_hex "$digest" || return 1
    printf '%s\n' "$digest"
}

prov_hash_stream() {
    local digest
    digest=$(sha256sum) || return 1
    digest=${digest%% *}
    prov_hex "$digest" || return 1
    printf '%s\n' "$digest"
}

# Enumerate every entry before filtering. Never silently skip unsafe entries.
# kind=source permits regular non-source outputs; snapshot permits .nq only.
_prov_tree_paths_legacy() (
    local root=$1 subtree=$2 kind=${3:-all} scratch p rel
    local LC_ALL=C
    prov_directory "$root" && prov_safe_relative "$subtree" || exit 1
    prov_directory "$root/$subtree" || exit 1
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    find "$root/$subtree" -print0 > "$scratch/entries" || exit 1
    : > "$scratch/paths"
    while IFS= read -r -d '' p; do
        rel=${p#"$root/"}
        prov_safe_relative "$rel" || exit 1
        [[ ! -L "$p" ]] || exit 1
        if [[ -d "$p" ]]; then continue; fi
        prov_regular "$p" || exit 1
        if [[ "$kind" != all && "$rel" != *.nq ]]; then
            [[ "$kind" == source ]] || exit 1
            continue
        fi
        printf '%s\n' "$rel" >> "$scratch/paths" || exit 1
    done < "$scratch/entries"
    LC_ALL=C sort "$scratch/paths"
)

prov_tree_paths() (
    local root=$1 subtree=$2 kind=${3:-all} scratch version type mode p rel
    local total consumed=0 records=0 code LC_ALL=C
    prov_directory "$root" && prov_safe_relative "$subtree" || exit 1
    prov_directory "$root/$subtree" || exit 1
    # Choose capability handling before the operation, never after its failure.
    version=$(find --version 2>/dev/null) || version=''
    if [[ "$version" != 'find (GNU findutils) '* ]]; then
        _prov_tree_paths_legacy "$root" "$subtree" "$kind"
        exit $?
    fi
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    find "$root/$subtree" -printf '%y\0%m\0%p\0' > "$scratch/entries" || exit 1
    total=$(wc -c < "$scratch/entries") || exit 1
    [[ "$total" =~ ^[1-9][0-9]*$ ]] || exit 1
    : > "$scratch/paths" || exit 1
    exec 3< "$scratch/entries" || exit 1
    while :; do
        type=''
        if IFS= read -r -d '' type <&3; then :;
        else code=$?; [[ "$code" == 1 && -z "$type" ]] || exit 1; break; fi
        IFS= read -r -d '' mode <&3 || exit 1
        IFS= read -r -d '' p <&3 || exit 1
        consumed=$((consumed + ${#type} + ${#mode} + ${#p} + 3))
        [[ "$mode" =~ ^[0-7]{1,4}$ && "$p" == "$root/$subtree"* ]] || exit 1
        if (( records == 0 )); then [[ "$p" == "$root/$subtree" && "$type" == d ]] || exit 1; fi
        [[ "$p" == "$root/$subtree" || "$p" == "$root/$subtree/"* ]] || exit 1
        records=$((records + 1))
        rel=${p#"$root/"}
        prov_safe_relative "$rel" && [[ ! -L "$p" ]] || exit 1
        if [[ "$type" == d ]]; then [[ -d "$p" ]] || exit 1; continue; fi
        [[ "$type" == f && -f "$p" && -r "$p" ]] || exit 1
        prov_directory "${p%/*}" || exit 1
        (( (8#$mode & 0444) != 0 )) || exit 1
        if [[ "$kind" != all && "$rel" != *.nq ]]; then
            [[ "$kind" == source ]] || exit 1
            continue
        fi
        printf '%s\n' "$rel" >> "$scratch/paths" || exit 1
    done
    [[ "$consumed" == "$total" && "$records" != 0 ]] || exit 1
    LC_ALL=C sort "$scratch/paths"
)

# PATHS_FILE is canonical LF, sorted, unique, safe relative paths (empty allowed).
_prov_validate_paths_legacy() (
    local list=$1 scratch p previous='' LC_ALL=C
    prov_regular "$list" || exit 1
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    while IFS= read -r p; do
        prov_safe_relative "$p" || exit 1
        [[ -z "$previous" || "$p" > "$previous" ]] || exit 1
        printf '%s\n' "$p" >> "$scratch" || exit 1
        previous=$p
    done < "$list"
    cmp -s "$list" "$scratch"
)

prov_validate_paths() (
    local list=$1 metadata size bytes again code p previous='' LC_ALL=C
    metadata=$(prov_file_metadata "$list") || exit 1
    size=${metadata#* }
    if (( ${#size} > 5 )) || (( 10#$size > 65536 )); then
        _prov_validate_paths_legacy "$list"
        exit $?
    fi
    # Delimiter/limit completion (status0) rejects NULs and growth. Only a
    # complete bounded EOF read may supply the immutable validation bytes.
    if IFS= read -r -d '' -n "$((size + 1))" bytes < "$list"; then exit 1;
    else code=$?; [[ "$code" == 1 && ${#bytes} == "$size" ]] || exit 1; fi
    if IFS= read -r -d '' -n "$((size + 1))" again < "$list"; then exit 1;
    else code=$?; [[ "$code" == 1 && ${#again} == "$size" && "$again" == "$bytes" ]] || exit 1; fi
    metadata=$(prov_file_metadata "$list") || exit 1
    [[ "${metadata#* }" == "$size" ]] || exit 1
    [[ -n "$bytes" ]] || exit 0
    [[ "$bytes" == *$'\n' ]] || exit 1
    while IFS= read -r p; do
        prov_safe_relative "$p" || exit 1
        [[ -z "$previous" || "$p" > "$previous" ]] || exit 1
        previous=$p
    done <<< "${bytes%$'\n'}"
)

# Linux's conservative argv budget includes worst-case environment pointer
# overhead. Unsupported capacity selects legacy operation before any batch.
_prov_batch_supported() {
    local limit environment LC_ALL=C
    [[ "$OSTYPE" == linux* ]] || return 1
    limit=$(getconf ARG_MAX 2>/dev/null) || return 1
    [[ "$limit" =~ ^[1-9][0-9]{0,9}$ ]] || return 1
    (( limit >= 131072 )) || return 1
    environment=$(set -o pipefail; env -0 | wc -c) 2>/dev/null || return 1
    [[ "$environment" =~ ^(0|[1-9][0-9]{0,4})$ ]] || return 1
    (( environment <= 32768 )) || return 1
    (( 16 * (environment + 80) + environment + 32768 + 16384 < limit ))
}

_prov_paths_fit_batches() {
    local root=$1 dest=$2 list=$3 p full parent LC_ALL=C
    while IFS= read -r p; do
        full="$root/$p"
        (( ${#full} + 1 <= 8192 )) || return 1
        if [[ -n "$dest" ]]; then
            parent=$dest
            [[ "$p" != */* ]] || parent="$dest/${p%/*}"
            (( ${#parent} + 2 <= 8192 )) || return 1
        fi
    done < "$list"
}

_prov_frame_files_scalar() {
    local root=$1 list=$2 p metadata mode size LC_ALL=C
    while IFS= read -r p; do
        metadata=$(prov_file_metadata "$root/$p") || return 1
        mode=${metadata%% *}; size=${metadata#* }
        printf 'path-bytes:%d\n%s\nmode:%s\ncontent-bytes:%s\n' "${#p}" "$p" "$mode" "$size" || return 1
        cat -- "$root/$p" || return 1
        printf '\n' || return 1
    done < "$list"
}

# Private provider records bind metadata to argv paths before consumers see it.
_prov_stat_rows() (
    local output=$1 p row rest mode size total consumed=0 code LC_ALL=C
    shift
    (( $# > 0 && $# <= 64 )) || exit 1
    stat --printf '%f %s %n\0' -- "$@" > "$output.raw" || exit 1
    total=$(wc -c < "$output.raw") || exit 1
    [[ "$total" =~ ^[1-9][0-9]{0,4}$ ]] && (( total <= 16384 )) || exit 1
    : > "$output" || exit 1
    exec 4< "$output.raw" || exit 1
    for p in "$@"; do
        IFS= read -r -d '' -n 16385 row <&4 || exit 1
        consumed=$((consumed + ${#row} + 1))
        mode=${row%% *}; rest=${row#* }; size=${rest%% *}
        [[ "$row" != "$rest" && "$rest" == *' '* && "${rest#* }" == "$p" ]] || exit 1
        [[ "$mode" =~ ^[0-9a-f]{1,8}$ && "$size" =~ ^(0|[1-9][0-9]*)$ ]] || exit 1
        printf '%s %s\n' "$mode" "$size" >> "$output" || exit 1
    done
    row=''
    if IFS= read -r -d '' -n 16385 row <&4; then exit 1;
    else code=$?; [[ "$code" == 1 && -z "$row" && "$consumed" == "$total" ]] || exit 1; fi
)

prov_files_frame() {
    local root=$1 domain=$2 list=$3 count LC_ALL=C
    prov_directory "$root" && prov_validate_paths "$list" || return 1
    [[ "$domain" =~ ^[a-z0-9-]+/v[0-9]+$ ]] || return 1
    count=$(wc -l < "$list") || return 1
    printf '%s\nfiles:%d\n' "$domain" "$count" || return 1
    if _prov_batch_supported && _prov_paths_fit_batches "$root" '' "$list"; then
        _prov_frame_files_batch "$root" "$list"
    else
        _prov_frame_files_scalar "$root" "$list"
    fi
}

_prov_frame_files_batch() (
    local root=$1 list=$2 scratch p full pending='' eof=false defect=false total=0 row mode size at LC_ALL=C
    local -a paths=() absolute=() rows=()
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    exec 3< "$list" || exit 1
    while :; do
        paths=(); absolute=(); total=0; defect=false
        while (( ${#paths[@]} < 64 )); do
            if [[ -n "$pending" ]]; then p=$pending; pending='';
            elif ! IFS= read -r p <&3; then eof=true; break; fi
            full="$root/$p"
            if (( total + ${#full} + 1 > 8192 )); then pending=$p; break; fi
            if [[ ! -f "$full" || -L "$full" || ! -r "$full" ]] || ! prov_directory "${full%/*}"; then defect=true; break; fi
            paths+=("$p"); absolute+=("$full"); total=$((total + ${#full} + 1))
        done
        if (( ${#paths[@]} == 0 )); then [[ "$defect" == false && "$eof" == true ]] || exit 1; exit 0; fi
        _prov_stat_rows "$scratch/stat" "${absolute[@]}" || exit 1
        mapfile -t rows < "$scratch/stat" || exit 1
        (( ${#rows[@]} == ${#paths[@]} )) || exit 1
        for ((at = 0; at < ${#paths[@]}; at++)); do
            row=${rows[at]}
            [[ "$row" =~ ^([0-9a-f]{1,8})\ (0|[1-9][0-9]*)$ ]] || exit 1
            mode=${BASH_REMATCH[1]}; size=${BASH_REMATCH[2]}
            (( (16#$mode & 8#170000) == 8#100000 && (16#$mode & 8#444) != 0 )) || exit 1
            if (( (16#$mode & 8#111) != 0 )); then mode=100755; else mode=100644; fi
            p=${paths[at]}; full=${absolute[at]}
            [[ -f "$full" && ! -L "$full" && -r "$full" ]] && prov_directory "${full%/*}" || exit 1
            printf 'path-bytes:%d\n%s\nmode:%s\ncontent-bytes:%s\n' "${#p}" "$p" "$mode" "$size" || exit 1
            cat -- "$full" || exit 1
            printf '\n' || exit 1
        done
        [[ "$defect" == false ]] || exit 1
        [[ "$eof" == false ]] || exit 0
    done
)

prov_files_digest() (
    set -o pipefail
    prov_files_frame "$@" | prov_hash_stream
)

_prov_file_hash_rows_scalar() {
    local root=$1 list=$2 p mode hash
    while IFS= read -r p; do
        mode=$(prov_mode "$root/$p") || return 1
        hash=$(prov_sha256 "$root/$p") || return 1
        printf '%s\t%s\t%s\n' "$mode" "$hash" "$p" || return 1
    done < "$list"
}

# Every call acquires fresh hashes. A final checksum pass calls this again;
# it never reuses the earlier inventory's observations as current content.
prov_file_hash_rows() (
    local root=$1 list=$2 version LC_ALL=C
    local -a sample=()
    prov_directory "$root" && prov_validate_paths "$list" || exit 1
    mapfile -t -n 8 sample < "$list" || exit 1
    if (( ${#sample[@]} >= 8 )) && _prov_batch_supported && _prov_paths_fit_batches "$root" '' "$list"; then
        version=$(sha256sum --version 2>/dev/null) || version=''
        if [[ "$version" == 'sha256sum (GNU coreutils) '* ]]; then
            _prov_file_hash_rows_batch "$root" "$list"
            exit $?
        fi
    fi
    _prov_file_hash_rows_scalar "$root" "$list"
)

_prov_file_hash_rows_batch() (
    local root=$1 list=$2 scratch p full pending='' eof=false total=0 at mode size
    local row hash bytes consumed code LC_ALL=C
    local -a paths=() absolute=() metadata=() modes=()
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    exec 3< "$list" || exit 1
    while :; do
        paths=(); absolute=(); modes=(); total=0
        while (( ${#paths[@]} < 64 )); do
            if [[ -n "$pending" ]]; then p=$pending; pending='';
            elif ! IFS= read -r p <&3; then eof=true; break; fi
            full="$root/$p"
            if (( total + ${#full} + 1 > 8192 )); then pending=$p; break; fi
            [[ -f "$full" && ! -L "$full" && -r "$full" ]] && prov_directory "${full%/*}" || exit 1
            paths+=("$p"); absolute+=("$full"); total=$((total + ${#full} + 1))
        done
        if (( ${#paths[@]} == 0 )); then [[ "$eof" == true ]] || exit 1; exit 0; fi
        _prov_stat_rows "$scratch/stat" "${absolute[@]}" || exit 1
        mapfile -t metadata < "$scratch/stat" || exit 1
        (( ${#metadata[@]} == ${#paths[@]} )) || exit 1
        for ((at=0; at < ${#paths[@]}; at++)); do
            row=${metadata[at]}; mode=${row%% *}; size=${row#* }
            (( (16#$mode & 8#170000) == 8#100000 && (16#$mode & 8#444) != 0 )) || exit 1
            if (( (16#$mode & 8#111) != 0 )); then modes+=(100755); else modes+=(100644); fi
            full=${absolute[at]}
            [[ -f "$full" && ! -L "$full" && -r "$full" ]] && prov_directory "${full%/*}" || exit 1
        done
        sha256sum --zero -- "${absolute[@]}" > "$scratch/hashes" || exit 1
        bytes=$(wc -c < "$scratch/hashes") || exit 1
        [[ "$bytes" =~ ^[1-9][0-9]{0,4}$ ]] && (( bytes <= 16384 )) || exit 1
        consumed=0
        exec 4< "$scratch/hashes" || exit 1
        : > "$scratch/rows" || exit 1
        for ((at=0; at < ${#paths[@]}; at++)); do
            IFS= read -r -d '' -n 16385 row <&4 || exit 1
            consumed=$((consumed + ${#row} + 1))
            hash=${row:0:64}
            prov_hex "$hash" && [[ "${row:64:2}" == '  ' && "${row:66}" == "${absolute[at]}" ]] || exit 1
            full=${absolute[at]}
            [[ -f "$full" && ! -L "$full" && -r "$full" ]] && prov_directory "${full%/*}" || exit 1
            printf '%s\t%s\t%s\n' "${modes[at]}" "$hash" "${paths[at]}" >> "$scratch/rows" || exit 1
        done
        row=''
        if IFS= read -r -d '' -n 16385 row <&4; then exit 1;
        else code=$?; [[ "$code" == 1 && -z "$row" && "$consumed" == "$bytes" ]] || exit 1; fi
        exec 4<&-
        cat "$scratch/rows" || exit 1
        [[ "$eof" == false ]] || exit 0
    done
)

prov_producer_scripts() {
    printf '%s\n' scripts/bootstrap_seed.sh scripts/build_stage1_from_seed.sh \
        scripts/provenance.sh scripts/seed_manifest.sh scripts/stage1_cache.sh
}

# Source loading is the existing flat selfhost route, never ambient manifests.
prov_flat_loading() {
    local root=$1 directory p
    prov_directory "$root" || return 1
    directory="$root/selfhost"
    # Relative emit arguments currently stop at cwd. Also reject physical
    # ancestor metadata so an absolute-path loader cannot widen the capture.
    while true; do
        for p in nauqtype.workspace.json nauqtype.workspace.lock.json; do
            [[ ! -e "$directory/$p" && ! -L "$directory/$p" ]] || prov_error "unexpected selfhost loading metadata: $directory/$p" || return 1
        done
        [[ "$directory" != / ]] || break
        directory=${directory%/*}
        [[ -n "$directory" ]] || directory=/
    done
}

prov_input_paths() (
    local root=$1 scratch
    prov_flat_loading "$root" || exit 1
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    prov_tree_paths "$root" selfhost source > "$scratch/selfhost" || exit 1
    [[ -s "$scratch/selfhost" && -f "$root/selfhost/main.nq" ]] || exit 1
    prov_tree_paths "$root" bootstrap/seed all > "$scratch/seed" || exit 1
    {
        printf '%s\n' VERSION stdlib/runtime.c stdlib/runtime.h || exit 1
        prov_producer_scripts || exit 1
        cat "$scratch/selfhost" "$scratch/seed" || exit 1
    } > "$scratch/paths" || exit 1
    LC_ALL=C sort "$scratch/paths" > "$scratch/sorted" || exit 1
    prov_validate_paths "$scratch/sorted" || exit 1
    cat "$scratch/sorted"
)

prov_inputs_sha256() (
    local scratch
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    prov_input_paths "$1" > "$scratch" || exit 1
    prov_files_digest "$1" nauqtype-build-inputs/v2 "$scratch"
)

# Snapshot must start empty. Verify the captured set and originals separately.
prov_capture_inputs() {
    local root=$1 dest=$2 list=$3 expected=$4 p actual parent='' next_parent full bytes=0
    local -a files=()
    prov_validate_paths "$list" || return 1
    mkdir -p -- "$dest" || return 1
    prov_directory "$dest" || return 1
    if _prov_batch_supported && _prov_paths_fit_batches "$root" "$dest" "$list"; then
        while IFS= read -r p; do
            next_parent=''
            [[ "$p" != */* ]] || next_parent=${p%/*}
            full="$root/$p"
            prov_regular "$full" || return 1
            if (( ${#files[@]} > 0 )) && { [[ "$next_parent" != "$parent" ]] || (( ${#files[@]} == 64 || bytes + ${#full} + 1 > 8192 )); }; then
                mkdir -p -- "$dest/$parent" || return 1
                cp --preserve=mode -- "${files[@]}" "$dest/$parent/" || return 1
                files=(); bytes=0
            fi
            parent=$next_parent
            files+=("$full"); bytes=$((bytes + ${#full} + 1))
        done < "$list"
        if (( ${#files[@]} > 0 )); then
            mkdir -p -- "$dest/$parent" || return 1
            cp --preserve=mode -- "${files[@]}" "$dest/$parent/" || return 1
        fi
    else
        while IFS= read -r p; do
            prov_regular "$root/$p" || return 1
            if [[ "$p" == */* ]]; then mkdir -p -- "$dest/${p%/*}" || return 1; fi
            cp --preserve=mode -- "$root/$p" "$dest/$p" || return 1
        done < "$list"
    fi
    actual=$(prov_inputs_sha256 "$dest") || return 1
    [[ "$actual" == "$expected" ]] || prov_error 'captured inputs differ from pre-capture inventory' || return 1
    actual=$(prov_inputs_sha256 "$root") || return 1
    [[ "$actual" == "$expected" ]] || prov_error 'inputs changed during capture' || return 1
}

prov_cc_identity() (
    local requested=$1 output=$2 cc scratch target hash version_hash
    local LC_ALL=C
    [[ -n "$requested" && ! "$requested" =~ [^\ -~] ]] || exit 1
    cc=$(command -v -- "$requested") || exit 1
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    realpath -e -- "$cc" > "$scratch/path" || exit 1
    cc=$(< "$scratch/path")
    prov_absolute "$cc" && prov_regular "$cc" && [[ -x "$cc" ]] || exit 1
    printf '%s\n' "$cc" > "$scratch/expected-path" || exit 1
    cmp -s "$scratch/path" "$scratch/expected-path" || exit 1
    hash=$(prov_sha256 "$cc") || exit 1
    "$cc" --version > "$scratch/version" || exit 1
    "$cc" -dumpmachine > "$scratch/target" || exit 1
    version_hash=$(prov_sha256 "$scratch/version") || exit 1
    target=$(< "$scratch/target")
    prov_atom "$target" || exit 1
    printf '%s\n' "$target" > "$scratch/expected-target" || exit 1
    cmp -s "$scratch/target" "$scratch/expected-target" || exit 1
    [[ "$(prov_sha256 "$cc")" == "$hash" ]] || exit 1
    printf 'cc_path=%s\ncc_sha256=%s\ncc_version_sha256=%s\ncc_target=%s\n' \
        "$cc" "$hash" "$version_hash" "$target" > "$output"
)

prov_cc_gc_profile_valid() {
    [[ "$1" == portable || "$1" == gcc-20-32768 ]]
}

# Probe only an already identity-checked compiler. Exit 1/2 and clean,
# unsupported output select the portable recipe; capture/timeout/identity
# failures remain hard errors.
prov_cc_gc_profile_select() (
    local requested=$1 expected_identity=$2 output=$3 scratch cc metadata size status file_limit=68 had_errexit=false
    local LC_ALL=C
    prov_regular "$expected_identity" || exit 1
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    prov_cc_identity "$requested" "$scratch/cc-before" || exit 1
    cmp -s "$expected_identity" "$scratch/cc-before" || exit 1
    cc=$(sed -n 's/^cc_path=//p' "$scratch/cc-before")
    prov_absolute "$cc" || exit 1
    command -v timeout >/dev/null 2>&1 || exit 1
    [[ "$(timeout --version 2>/dev/null | sed -n '1p')" == 'timeout (GNU coreutils) '* ]] || exit 1
    : > "$scratch/stdout" || exit 1
    : > "$scratch/stderr" || exit 1
    exec 3> "$scratch/stdout" || exit 1
    exec 4> "$scratch/stderr" || exit 1
    [[ $- == *e* ]] && had_errexit=true
    set +e
    # Bash uses 512-byte file-limit units in POSIX mode, 1024 otherwise.
    if [[ -o posix ]]; then file_limit=136; fi
    # Leave physical headroom above the accepted 64 KiB so EFBIG/SIGXFSZ
    # cannot turn a truncated capture plus exit 1/2 into portable fallback.
    ( ulimit -f "$file_limit" || exit 125; timeout --signal=TERM --kill-after=1s 3s "$cc" -Q --help=params ) >&3 2>&4
    status=$?
    [[ "$had_errexit" == false ]] || set -e
    exec 3>&- 4>&-
    prov_cc_identity "$requested" "$scratch/cc-after" || exit 1
    cmp -s "$expected_identity" "$scratch/cc-after" || exit 1
    for cc in stdout stderr; do
        metadata=$(prov_file_metadata "$scratch/$cc") || exit 1
        size=${metadata#* }
        [[ "$size" =~ ^(0|[1-9][0-9]*)$ ]] && (( size <= 65536 )) || exit 1
    done
    if (( status == 1 || status == 2 )); then
        printf 'portable\n' > "$output" || exit 1
        exit 0
    fi
    (( status == 0 )) || exit 1
    if [[ -s "$scratch/stderr" ]]; then
        printf 'portable\n' > "$output" || exit 1
        exit 0
    fi
    set +e
    awk '
        index($0, "--param=ggc-min-expand=") {
            expand++
            if ($0 !~ /^[[:space:]]*--param=ggc-min-expand=[[:space:]]+[0-9]+[[:space:]]*$/) bad=1
        }
        index($0, "--param=ggc-min-heapsize=") {
            heapsize++
            if ($0 !~ /^[[:space:]]*--param=ggc-min-heapsize=[[:space:]]+[0-9]+[[:space:]]*$/) bad=1
        }
        END { exit (expand == 1 && heapsize == 1 && !bad) ? 0 : 1 }
    ' "$scratch/stdout"
    status=$?
    [[ "$had_errexit" == false ]] || set -e
    case "$status" in
        0) printf 'gcc-20-32768\n' > "$output" || exit 1;;
        1) printf 'portable\n' > "$output" || exit 1;;
        *) exit 1;;
    esac
)

# The transport can confirm a parent's frozen choice, never choose one.
prov_cc_gc_profile_transport_validate() {
    local selected=$1
    prov_cc_gc_profile_valid "$selected" || return 1
    if [[ -v NQ_BOOTSTRAP_CC_GC_PROFILE ]]; then
        prov_cc_gc_profile_valid "$NQ_BOOTSTRAP_CC_GC_PROFILE" || return 1
        [[ "$NQ_BOOTSTRAP_CC_GC_PROFILE" == "$selected" ]] || return 1
    fi
}

prov_cc_gc_profile_freeze() (
    local requested=$1 expected_identity=$2 output=$3 scratch selected
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    prov_cc_gc_profile_select "$requested" "$expected_identity" "$scratch/selected" || exit 1
    selected=$(< "$scratch/selected")
    prov_cc_gc_profile_valid "$selected" || exit 1
    prov_cc_gc_profile_transport_validate "$selected" || exit 1
    printf '%s\n' "$selected" > "$output"
)

prov_seed_args() {
    local profile=$1
    prov_cc_gc_profile_valid "$profile" || return 1
    printf '%s\0' -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Ibootstrap/seed \
        bootstrap/seed/nauqc-seed.c bootstrap/seed/runtime.c -o build/seed/nauqc-seed || return 1
    [[ "$profile" == portable ]] || printf '%s\0' --param=ggc-min-expand=20 --param=ggc-min-heapsize=32768
}

prov_stage1_args() {
    local profile=$1
    prov_cc_gc_profile_valid "$profile" || return 1
    printf '%s\0' -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib \
        build/seed/stage1.c stdlib/runtime.c -o selfhost/build/nauqc || return 1
    [[ "$profile" == portable ]] || printf '%s\0' --param=ggc-min-expand=20 --param=ggc-min-heapsize=32768
}

prov_seed_emit_args() { printf '%s\0' emit-c selfhost/main.nq -o build/seed/stage1.c; }

prov_cc_args_count() {
    prov_cc_gc_profile_valid "$1" || return 1
    if [[ "$1" == portable ]]; then printf '8\n'; else printf '10\n'; fi
}

prov_argv_file_validate() (
    local file=$1 expected_count=$2 scratch metadata size arg
    local -a args=()
    [[ "$expected_count" =~ ^[1-9][0-9]*$ ]] || exit 1
    metadata=$(prov_file_metadata "$file") || exit 1
    size=${metadata#* }
    (( size > 0 && size <= 4096 )) || exit 1
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    while IFS= read -r -d '' arg; do args+=("$arg"); done < "$file"
    (( ${#args[@]} == expected_count )) || exit 1
    printf '%s\0' "${args[@]}" > "$scratch" || exit 1
    cmp -s "$file" "$scratch"
)

# Capture status explicitly: process substitution and conditional contexts can
# otherwise turn a producer's partial output into apparently valid argv.
prov_argv_materialize() (
    local output=$1 expected_count=$2 producer=$3 scratch status had_errexit=false
    shift 3
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    [[ $- == *e* ]] && had_errexit=true
    set +e
    "$producer" "$@" > "$scratch/argv"
    status=$?
    [[ "$had_errexit" == false ]] || set -e
    (( status == 0 )) || exit "$status"
    prov_argv_file_validate "$scratch/argv" "$expected_count" || exit 1
    cp -- "$scratch/argv" "$output" || exit 1
    prov_argv_file_validate "$output" "$expected_count"
)

prov_argv_load() {
    local file=$1 expected_count=$2 target_name=$3 expected_hash=${4:-} loaded_hash
    local -n target=$target_name
    prov_argv_file_validate "$file" "$expected_count" || return 1
    target=()
    mapfile -d '' -t target < "$file" || return 1
    (( ${#target[@]} == expected_count )) || return 1
    if [[ -n "$expected_hash" ]]; then
        prov_hex "$expected_hash" || return 1
        loaded_hash=$(set -o pipefail; printf '%s\0' "${target[@]}" | prov_hash_stream) || return 1
        [[ "$loaded_hash" == "$expected_hash" ]] || return 1
    fi
}

prov_bootstrap_args_materialize() {
    local profile=$1 directory=$2 count
    count=$(prov_cc_args_count "$profile") || return 1
    prov_directory "$directory" || return 1
    prov_argv_materialize "$directory/seed-args" "$count" prov_seed_args "$profile" || return 1
    prov_argv_materialize "$directory/stage1-args" "$count" prov_stage1_args "$profile"
}

prov_bootstrap_flags_sha256_from_files() (
    set -o pipefail
    local profile=$1 seed_args=$2 stage1_args=$3 count
    count=$(prov_cc_args_count "$profile") || exit 1
    prov_argv_file_validate "$seed_args" "$count" || exit 1
    prov_argv_file_validate "$stage1_args" "$count" || exit 1
    { printf '%s\0' nauqtype-bootstrap-flags/v1 seed || exit 1; cat -- "$seed_args" || exit 1; printf 'stage1\0' || exit 1; cat -- "$stage1_args" || exit 1; } | prov_hash_stream
)

# Compatibility entrypoint for attestation and other read-only consumers.
# It always ignores private transport and freshly selects the current profile.
prov_bootstrap_flags_sha256() (
    local scratch profile
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    prov_cc_identity "${CC:-cc}" "$scratch/cc" || exit 1
    prov_cc_gc_profile_select "${CC:-cc}" "$scratch/cc" "$scratch/profile" || exit 1
    profile=$(< "$scratch/profile")
    prov_bootstrap_args_materialize "$profile" "$scratch" || exit 1
    prov_bootstrap_flags_sha256_from_files "$profile" "$scratch/seed-args" "$scratch/stage1-args"
)

prov_proof_flags_sha256() (
    set -o pipefail
    printf '%s\0' nauqtype-proof-options/v1 -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib | prov_hash_stream
)

# Bounded scalar key=value reader. No eval/source of evidence and no lost NULs.
# SPEC arguments are ordered key:type; OUTPUT receives the verified exact bytes.
prov_read_record() (
    local file=$1 header=$2 output=$3 scratch key type line value spec
    shift 3
    prov_regular "$file" || exit 1
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    exec 3< "$file" || exit 1
    IFS= read -r line <&3 && [[ "$line" == "$header" ]] || exit 1
    printf '%s\n' "$header" > "$scratch" || exit 1
    for spec in "$@"; do
        key=${spec%:*}; type=${spec##*:}
        IFS= read -r line <&3 || exit 1
        [[ "$line" == "$key="* ]] || exit 1
        value=${line#*=}
        case "$type" in
            hash) prov_hex "$value" || exit 1;;
            path) prov_absolute "$value" || exit 1;;
            atom) prov_atom "$value" || exit 1;;
            *) exit 1;;
        esac
        printf '%s=%s\n' "$key" "$value" >> "$scratch" || exit 1
    done
    cmp -s "$file" "$scratch" || exit 1
    cp -- "$scratch" "$output"
)
