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
    local root=$1 scratch path count mode hash LC_ALL=C
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    seed_source_paths "$root" > "$scratch" || exit 1
    [[ -s "$scratch" && -f "$root/selfhost/main.nq" ]] || exit 1
    count=$(wc -l < "$scratch") || exit 1
    printf 'seed-source-inventory/v1\nfiles:%d\n' "$count" || exit 1
    while IFS= read -r path; do
        mode=$(prov_mode "$root/$path") || exit 1
        hash=$(prov_sha256 "$root/$path") || exit 1
        printf 'path-bytes:%d\n%s\nmode:%s\nsha256:%s\n' "${#path}" "$path" "$mode" "$hash" || exit 1
    done < "$scratch"
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
    [[ ${#args[@]} == 8 ]] || exit 1
    [[ "${args[0]}" == -std=c11 && "${args[1]}" == -O2 && "${args[2]}" == -D_POSIX_C_SOURCE=200809L && "${args[3]}" == -Istdlib ]] || exit 1
    prov_safe_relative "${args[4]}" && [[ "${args[4]}" == *.c ]] || exit 1
    [[ "${args[5]}" == stdlib/runtime.c && "${args[6]}" == -o ]] || exit 1
    prov_safe_relative "${args[7]}" || exit 1
    printf '%s\0' "${args[@]}" > "$scratch" || exit 1
    cmp -s "$file" "$scratch"
)

seed_verify() (
    local root=$1 scratch key value path hash
    local -A fields=()
    prov_directory "$root" || exit 1
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    seed_manifest_read "$root/bootstrap/seed/manifest.json" "$scratch/fields" || { prov_error 'expected strict canonical seed v2 manifest'; exit 1; }
    while IFS='=' read -r key value; do fields[$key]=$value; done < "$scratch/fields"
    [[ "${fields[generator_input_c_sha256]}" == "${fields[compiler_c_sha256]}" && "${fields[generator_output_c_sha256]}" == "${fields[compiler_c_sha256]}" ]] || exit 1
    # Inventory reconstruction binds both bytes and exact membership/order/mode.
    prov_flat_loading "$root/bootstrap/seed/source-snapshot" || exit 1
    seed_source_inventory "$root/bootstrap/seed/source-snapshot" > "$scratch/inventory" || exit 1
    prov_regular "$root/bootstrap/seed/source-inventory-v1.txt" || exit 1
    cmp -s "$scratch/inventory" "$root/bootstrap/seed/source-inventory-v1.txt" || exit 1
    hash=$(prov_sha256 "$scratch/inventory") || exit 1
    [[ "$hash" == "${fields[source_inventory_sha256]}" ]] || exit 1
    hash=$(seed_source_tree_sha256 "$root/bootstrap/seed/source-snapshot") || exit 1
    [[ "$hash" == "${fields[source_tree_sha256]}" ]] || exit 1
    for key in compiler_c runtime_c runtime_h; do
        case "$key" in compiler_c) path=nauqc-seed.c;; runtime_c) path=runtime.c;; runtime_h) path=runtime.h;; esac
        hash=$(prov_sha256 "$root/bootstrap/seed/$path") || exit 1
        [[ "$hash" == "${fields[${key}_sha256]}" ]] || exit 1
    done
    seed_flags_verify "$root/bootstrap/seed/generator-flags.txt" || exit 1
    hash=$(prov_sha256 "$root/bootstrap/seed/generator-flags.txt") || exit 1
    [[ "$hash" == "${fields[generator_flags_sha256]}" ]] || exit 1
    seed_checksum_paths "$root" > "$scratch/expected-paths" || exit 1
    prov_validate_paths "$scratch/expected-paths" || exit 1
    prov_tree_paths "$root" bootstrap/seed all > "$scratch/actual-paths" || exit 1
    { printf 'bootstrap/seed/SHA256SUMS\n' || exit 1; cat "$scratch/expected-paths" || exit 1; } > "$scratch/all-paths" || exit 1
    cmp -s "$scratch/actual-paths" "$scratch/all-paths" || exit 1
    : > "$scratch/sums"
    while IFS= read -r path; do
        hash=$(prov_sha256 "$root/$path") || exit 1
        printf '%s  %s\n' "$hash" "$path" >> "$scratch/sums" || exit 1
    done < "$scratch/expected-paths"
    prov_regular "$root/bootstrap/seed/SHA256SUMS" || exit 1
    cmp -s "$scratch/sums" "$root/bootstrap/seed/SHA256SUMS" || exit 1
)
