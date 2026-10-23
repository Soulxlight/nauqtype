#!/usr/bin/env bash
# Sourced helper; historical generator identities are records, not signatures.

seed_manifest_fields() {
    printf '%s\n' version source_entry source_tree_format source_tree_sha256 \
        source_inventory_sha256 source_base_revision source_index_tree source_dirty \
        predecessor_seed_c_sha256 generator_exe_sha256 generator_input_c_sha256 \
        generator_output_c_sha256 compiler_c_sha256 runtime_c_sha256 runtime_h_sha256 \
        generator_cc_sha256 generator_cc_version_sha256 generator_cc_target generator_flags_sha256
}

# Reads only the fixed canonical JSON spelling. OUTPUT is validated key=value.
seed_manifest_read() (
    local file=$1 output=$2 scratch key line value scalar suffix LC_ALL=C
    local -a keys
    prov_regular "$file" || exit 1
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    seed_manifest_fields > "$scratch/keys" || exit 1
    mapfile -t keys < "$scratch/keys" || exit 1
    exec 3< "$file" || exit 1
    IFS= read -r line <&3 && [[ "$line" == '{' ]] || exit 1
    printf '{\n' > "$scratch/canonical" || exit 1
    : > "$scratch/values"
    for key in "${keys[@]}"; do
        IFS= read -r line <&3 || exit 1
        suffix=,
        [[ "$key" != generator_flags_sha256 ]] || suffix=''
        [[ "$line" == "  \"$key\": "*"$suffix" ]] || exit 1
        scalar=${line#"  \"$key\": "}
        [[ -z "$suffix" ]] || scalar=${scalar%,}
        case "$key" in
            source_dirty) [[ "$scalar" == true || "$scalar" == false ]] || exit 1; value=$scalar;;
            source_base_revision)
                if [[ "$scalar" == null ]]; then value=null;
                else [[ "$scalar" =~ ^\"[0-9a-f]{40}\"$ ]] || exit 1; value=${scalar:1:40}; fi;;
            *)
                [[ "$scalar" == \"*\" ]] || exit 1
                value=${scalar:1:${#scalar}-2}
                case "$key" in
                    version) [[ "$value" == nauqtype-c-seed/v2 ]] || exit 1;;
                    source_entry) [[ "$value" == selfhost/main.nq ]] || exit 1;;
                    source_tree_format) [[ "$value" == nauqtype-selfhost-source/v1 ]] || exit 1;;
                    source_index_tree) [[ "$value" =~ ^[0-9a-f]{40}$ ]] || exit 1;;
                    generator_cc_target) prov_atom "$value" || exit 1;;
                    *) prov_hex "$value" || exit 1;;
                esac;;
        esac
        printf '  "%s": %s%s\n' "$key" "$scalar" "$suffix" >> "$scratch/canonical" || exit 1
        printf '%s=%s\n' "$key" "$value" >> "$scratch/values" || exit 1
    done
    printf '}\n' >> "$scratch/canonical" || exit 1
    cmp -s "$file" "$scratch/canonical" || exit 1
    cp -- "$scratch/values" "$output"
)

seed_source_paths() {
    prov_tree_paths "$1" selfhost "${2:-snapshot}"
}

seed_source_inventory() (
    local root=$1 scratch
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    seed_source_paths "$root" > "$scratch" || exit 1
    seed_source_inventory_from_paths "$root" "$scratch"
)

# Build the unchanged public inventory encoding from one already enumerated
# source-path set. Callers still receive fresh mode and content observations.
seed_source_inventory_from_paths() (
    local root=$1 paths=$2 scratch path count mode hash previous='' LC_ALL=C
    prov_directory "$root" && prov_validate_paths "$paths" || exit 1
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    : > "$scratch" || exit 1
    while IFS= read -r path; do
        [[ "$path" == *.nq && ( -z "$previous" || "$path" > "$previous" ) ]] || exit 1
        printf '%s\n' "$path" >> "$scratch" || exit 1
        previous=$path
    done < "$paths"
    [[ -s "$scratch" && -f "$root/selfhost/main.nq" ]] || exit 1
    grep -Fqx 'selfhost/main.nq' "$scratch" || exit 1
    count=$(wc -l < "$scratch") || exit 1
    printf 'seed-source-inventory/v1\nfiles:%d\n' "$count" || exit 1
    trap 'rm -f -- "$scratch" "$scratch.rows"' EXIT
    prov_file_hash_rows "$root" "$scratch" > "$scratch.rows" || exit 1
    while IFS=$'\t' read -r mode hash path; do
        printf 'path-bytes:%d\n%s\nmode:%s\nsha256:%s\n' "${#path}" "$path" "$mode" "$hash" || exit 1
    done < "$scratch.rows"
)

# Parse one canonical inventory into a sorted path view and a tabular
# path/mode/hash view. Source paths are ASCII-safe, so lengths are byte counts.
seed_source_inventory_views() (
    set -o pipefail
    local inventory=$1 paths_out=$2 entries_out=$3 line path mode hash length previous='' declared seen=0 last_byte has_main=false LC_ALL=C
    prov_regular "$inventory" || exit 1
    tr -d '\000' < "$inventory" | cmp -s "$inventory" - || exit 1
    last_byte=$(tail -c 1 -- "$inventory" | od -An -tu1 | tr -d '[:space:]') || exit 1
    [[ "$last_byte" == 10 ]] || exit 1
    exec 3< "$inventory" || exit 1
    IFS= read -r line <&3 && [[ "$line" == seed-source-inventory/v1 ]] || exit 1
    IFS= read -r line <&3 && [[ "$line" =~ ^files:(0|[1-9][0-9]*)$ ]] || exit 1
    declared=${line#files:}
    [[ "$declared" != 0 ]] || exit 1
    : > "$paths_out" || exit 1
    : > "$entries_out" || exit 1
    while IFS= read -r line <&3; do
        [[ "$line" =~ ^path-bytes:(0|[1-9][0-9]*)$ ]] || exit 1
        length=${line#path-bytes:}
        IFS= read -r path <&3 || exit 1
        IFS= read -r line <&3 && [[ "$line" == mode:* ]] || exit 1
        mode=${line#mode:}
        IFS= read -r line <&3 && [[ "$line" == sha256:* ]] || exit 1
        hash=${line#sha256:}
        prov_safe_relative "$path" && [[ "$path" == *.nq && ${#path} == "$length" ]] || exit 1
        [[ -z "$previous" || "$path" > "$previous" ]] || exit 1
        [[ "$path" != selfhost/main.nq ]] || has_main=true
        [[ "$mode" == 100644 || "$mode" == 100755 ]] || exit 1
        prov_hex "$hash" || exit 1
        printf '%s\n' "$path" >> "$paths_out" || exit 1
        printf '%s\t%s\t%s\n' "$path" "$mode" "$hash" >> "$entries_out" || exit 1
        previous=$path
        seen=$((seen + 1))
    done
    [[ "$seen" == "$declared" && "$has_main" == true ]] || exit 1
    if IFS= read -r line <&3; then exit 1; fi
)

seed_source_tree_sha256_from_inventory() (
    set -o pipefail
    local inventory=$1 scratch path mode hash
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    seed_source_inventory_views "$inventory" "$scratch/paths" "$scratch/entries" || exit 1
    _seed_source_tree_sha256_from_validated_entries "$scratch/entries"
)

# These views are invocation-owned outputs of seed_source_inventory_views,
# not declared inventory or a persistent cache.
_seed_source_tree_sha256_from_validated_entries() (
    set -o pipefail
    local entries=$1 path mode hash
    {
        printf 'nauqtype-selfhost-source/v1\0' || exit 1
        while IFS=$'\t' read -r path mode hash; do
            printf '%s\0%s\0' "$path" "$hash" || exit 1
        done < "$entries"
    } | prov_hash_stream
)

seed_checksum_paths_from_inventory() (
    set -o pipefail
    local inventory=$1 scratch path mode hash
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    seed_source_inventory_views "$inventory" "$scratch/paths" "$scratch/entries" || exit 1
    _seed_checksum_paths_from_validated_paths "$scratch/paths"
)

_seed_checksum_paths_from_validated_paths() (
    set -o pipefail
    local paths=$1 path
    {
        printf '%s\n' bootstrap/seed/generator-flags.txt bootstrap/seed/manifest.json \
            bootstrap/seed/nauqc-seed.c bootstrap/seed/runtime.c bootstrap/seed/runtime.h \
            bootstrap/seed/source-inventory-v1.txt || exit 1
        while IFS= read -r path; do printf 'bootstrap/seed/source-snapshot/%s\n' "$path" || exit 1; done < "$paths"
    } | LC_ALL=C sort
)

# Preserve the already published selfhost/v1 path-NUL-hash-NUL definition.
seed_source_tree_sha256() (
    set -o pipefail
    local root=$1 scratch path hash
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    seed_source_paths "$root" "${2:-snapshot}" > "$scratch" || exit 1
    [[ -s "$scratch" && -f "$root/selfhost/main.nq" ]] || exit 1
    {
        printf 'nauqtype-selfhost-source/v1\0' || exit 1
        while IFS= read -r path; do
            hash=$(prov_sha256 "$root/$path") || exit 1
            printf '%s\0%s\0' "$path" "$hash" || exit 1
        done < "$scratch"
    } | prov_hash_stream
)

# Preserve the public fresh-reading checksum path helper.
seed_checksum_paths() (
    set -o pipefail
    local root=$1 scratch path
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    seed_source_paths "$root/bootstrap/seed/source-snapshot" > "$scratch" || exit 1
    {
        printf '%s\n' bootstrap/seed/generator-flags.txt bootstrap/seed/manifest.json \
            bootstrap/seed/nauqc-seed.c bootstrap/seed/runtime.c bootstrap/seed/runtime.h \
            bootstrap/seed/source-inventory-v1.txt || exit 1
        while IFS= read -r path; do printf 'bootstrap/seed/source-snapshot/%s\n' "$path" || exit 1; done < "$scratch"
    } | LC_ALL=C sort
)

seed_flags_verify() (
    local file=$1 scratch arg
    local -a args=()
    prov_regular "$file" || exit 1
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    while IFS= read -r -d '' arg; do args+=("$arg"); done < "$file"
    [[ ${#args[@]} == 8 || ${#args[@]} == 10 ]] || exit 1
    [[ "${args[0]}" == -std=c11 && "${args[1]}" == -O2 && "${args[2]}" == -D_POSIX_C_SOURCE=200809L && "${args[3]}" == -Istdlib ]] || exit 1
    prov_safe_relative "${args[4]}" && [[ "${args[4]}" == *.c ]] || exit 1
    [[ "${args[5]}" == stdlib/runtime.c && "${args[6]}" == -o ]] || exit 1
    prov_safe_relative "${args[7]}" || exit 1
    if (( ${#args[@]} == 10 )); then
        [[ "${args[8]}" == --param=ggc-min-expand=20 && "${args[9]}" == --param=ggc-min-heapsize=32768 ]] || exit 1
    fi
    printf '%s\0' "${args[@]}" > "$scratch" || exit 1
    cmp -s "$file" "$scratch"
)

seed_verify() (
    local root=$1 scratch key value path hash mode source_path source_mode source_hash
    local -A fields=()
    prov_directory "$root" || exit 1
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    seed_manifest_read "$root/bootstrap/seed/manifest.json" "$scratch/fields" || { prov_error 'expected strict canonical seed v2 manifest'; exit 1; }
    while IFS='=' read -r key value; do fields[$key]=$value; done < "$scratch/fields"
    [[ "${fields[generator_input_c_sha256]}" == "${fields[compiler_c_sha256]}" && "${fields[generator_output_c_sha256]}" == "${fields[compiler_c_sha256]}" ]] || exit 1
    # Inventory reconstruction binds both bytes and exact membership/order/mode.
    prov_flat_loading "$root/bootstrap/seed/source-snapshot" || exit 1
    seed_source_paths "$root/bootstrap/seed/source-snapshot" > "$scratch/source-paths" || exit 1
    seed_source_inventory_from_paths "$root/bootstrap/seed/source-snapshot" "$scratch/source-paths" > "$scratch/inventory" || exit 1
    prov_regular "$root/bootstrap/seed/source-inventory-v1.txt" || exit 1
    cmp -s "$scratch/inventory" "$root/bootstrap/seed/source-inventory-v1.txt" || exit 1
    hash=$(prov_sha256 "$scratch/inventory") || exit 1
    [[ "$hash" == "${fields[source_inventory_sha256]}" ]] || exit 1
    seed_source_inventory_views "$scratch/inventory" "$scratch/validated-source-paths" "$scratch/validated-source-entries" || exit 1
    hash=$(_seed_source_tree_sha256_from_validated_entries "$scratch/validated-source-entries") || exit 1
    [[ "$hash" == "${fields[source_tree_sha256]}" ]] || exit 1
    for key in compiler_c runtime_c runtime_h; do
        case "$key" in compiler_c) path=nauqc-seed.c;; runtime_c) path=runtime.c;; runtime_h) path=runtime.h;; esac
        hash=$(prov_sha256 "$root/bootstrap/seed/$path") || exit 1
        [[ "$hash" == "${fields[${key}_sha256]}" ]] || exit 1
    done
    seed_flags_verify "$root/bootstrap/seed/generator-flags.txt" || exit 1
    hash=$(prov_sha256 "$root/bootstrap/seed/generator-flags.txt") || exit 1
    [[ "$hash" == "${fields[generator_flags_sha256]}" ]] || exit 1
    _seed_checksum_paths_from_validated_paths "$scratch/validated-source-paths" > "$scratch/expected-paths" || exit 1
    prov_validate_paths "$scratch/expected-paths" || exit 1
    prov_tree_paths "$root" bootstrap/seed all > "$scratch/actual-paths" || exit 1
    { printf 'bootstrap/seed/SHA256SUMS\n' || exit 1; cat "$scratch/expected-paths" || exit 1; } > "$scratch/all-paths" || exit 1
    cmp -s "$scratch/actual-paths" "$scratch/all-paths" || exit 1
    : > "$scratch/sums" || exit 1
    prov_file_hash_rows "$root" "$scratch/expected-paths" > "$scratch/checksum-rows" || exit 1
    exec 4< "$scratch/validated-source-entries" || exit 1
    while IFS=$'\t' read -r mode hash path; do
        case "$path" in
            bootstrap/seed/source-snapshot/*)
                IFS=$'\t' read -r source_path source_mode source_hash <&4 || exit 1
                [[ "${path#bootstrap/seed/source-snapshot/}" == "$source_path" && "$hash" == "$source_hash" ]] || exit 1
                ;;
        esac
        printf '%s  %s\n' "$hash" "$path" >> "$scratch/sums" || exit 1
    done < "$scratch/checksum-rows"
    if IFS= read -r source_path <&4; then exit 1; fi
    prov_regular "$root/bootstrap/seed/SHA256SUMS" || exit 1
    cmp -s "$scratch/sums" "$root/bootstrap/seed/SHA256SUMS" || exit 1
)
