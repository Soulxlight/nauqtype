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

prov_regular() {
    local p=$1 mode
    [[ -f "$p" && ! -L "$p" && -r "$p" ]] || return 1
    prov_directory "${p%/*}" || return 1
    mode=$(stat -c '%a' -- "$p") || return 1
    [[ "$mode" =~ ^[0-7]{1,4}$ ]] && (( (8#$mode & 0444) != 0 ))
}

prov_mode() {
    local mode
    prov_regular "$1" || return 1
    mode=$(stat -c '%a' -- "$1") || return 1
    if (( (8#$mode & 0111) != 0 )); then printf '100755\n'; else printf '100644\n'; fi
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
prov_tree_paths() (
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

# PATHS_FILE is canonical LF, sorted, unique, safe relative paths (empty allowed).
prov_validate_paths() (
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

prov_files_frame() {
    local root=$1 domain=$2 list=$3 p count mode size LC_ALL=C
    prov_directory "$root" && prov_validate_paths "$list" || return 1
    [[ "$domain" =~ ^[a-z0-9-]+/v[0-9]+$ ]] || return 1
    count=$(wc -l < "$list") || return 1
    printf '%s\nfiles:%d\n' "$domain" "$count" || return 1
    while IFS= read -r p; do
        mode=$(prov_mode "$root/$p") || return 1
        size=$(stat -c '%s' -- "$root/$p") || return 1
        [[ "$size" =~ ^(0|[1-9][0-9]*)$ ]] || return 1
        printf 'path-bytes:%d\n%s\nmode:%s\ncontent-bytes:%s\n' "${#p}" "$p" "$mode" "$size" || return 1
        cat -- "$root/$p" || return 1
        printf '\n' || return 1
    done < "$list"
}

prov_files_digest() (
    set -o pipefail
    prov_files_frame "$@" | prov_hash_stream
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
    local root=$1 dest=$2 list=$3 expected=$4 p actual
    prov_validate_paths "$list" || return 1
    mkdir -p -- "$dest" || return 1
    while IFS= read -r p; do
        prov_regular "$root/$p" || return 1
        if [[ "$p" == */* ]]; then mkdir -p -- "$dest/${p%/*}" || return 1; fi
        cp --preserve=mode -- "$root/$p" "$dest/$p" || return 1
    done < "$list"
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

prov_seed_args() {
    printf '%s\0' -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Ibootstrap/seed \
        bootstrap/seed/nauqc-seed.c bootstrap/seed/runtime.c -o build/seed/nauqc-seed
}

prov_stage1_args() {
    printf '%s\0' -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib \
        build/seed/stage1.c stdlib/runtime.c -o selfhost/build/nauqc
}

prov_seed_emit_args() { printf '%s\0' emit-c selfhost/main.nq -o build/seed/stage1.c; }

prov_bootstrap_flags_sha256() (
    set -o pipefail
    { printf '%s\0' nauqtype-bootstrap-flags/v1 seed || exit 1; prov_seed_args || exit 1; printf 'stage1\0' || exit 1; prov_stage1_args || exit 1; } | prov_hash_stream
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
