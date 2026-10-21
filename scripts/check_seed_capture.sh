#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
source "$repo_root/scripts/provenance.sh"
source "$repo_root/scripts/seed_manifest.sh"

scratch=$(mktemp -d -t nauqtype-seed-capture-XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
fixture="$scratch/fixture"
snapshot="$fixture/bootstrap/seed/source-snapshot"
mkdir -p "$snapshot/selfhost" "$fixture/bootstrap/seed"
printf 'fn main() -> i32 { return 0; }\n' > "$snapshot/selfhost/main.nq"
printf 'captured helper source\n' > "$snapshot/selfhost/helper.nq"
printf 'empty file is still a source\n' > "$snapshot/selfhost/empty.nq"
printf 'seed C\n' > "$fixture/bootstrap/seed/nauqc-seed.c"
printf 'runtime C\n' > "$fixture/bootstrap/seed/runtime.c"
printf 'runtime header\n' > "$fixture/bootstrap/seed/runtime.h"
printf '%s\0' -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib bootstrap/seed/nauqc-seed.c stdlib/runtime.c -o build/seed/stage1.c > "$fixture/bootstrap/seed/generator-flags.txt"
chmod 644 "$snapshot/selfhost/"*.nq "$fixture/bootstrap/seed/"*.c "$fixture/bootstrap/seed/runtime.h"
chmod 755 "$snapshot/selfhost/main.nq"

legacy_directory() {
    local p=$1
    [[ "$p" == /* ]] || return 1
    while [[ "$p" != / ]]; do
        [[ -d "$p" && ! -L "$p" ]] || return 1
        p=${p%/*}
        [[ -n "$p" ]] || p=/
    done
}

legacy_regular() {
    local p=$1 mode
    [[ -f "$p" && ! -L "$p" && -r "$p" ]] || return 1
    legacy_directory "${p%/*}" || return 1
    mode=$(stat -c '%a' -- "$p") || return 1
    [[ "$mode" =~ ^[0-7]{1,4}$ ]] && (( (8#$mode & 0444) != 0 ))
}

legacy_mode() {
    local mode
    legacy_regular "$1" || return 1
    mode=$(stat -c '%a' -- "$1") || return 1
    if (( (8#$mode & 0111) != 0 )); then printf '100755\n'; else printf '100644\n'; fi
}

legacy_sha256() {
    local digest
    legacy_regular "$1" || return 1
    digest=$(sha256sum < "$1") || return 1
    digest=${digest%% *}
    prov_hex "$digest" || return 1
    printf '%s\n' "$digest"
}

legacy_source_paths() {
    prov_tree_paths "$1" selfhost snapshot
}

legacy_source_inventory() (
    local root=$1 paths=$2 path count mode hash LC_ALL=C
    [[ -s "$paths" && -f "$root/selfhost/main.nq" ]] || exit 1
    count=$(wc -l < "$paths") || exit 1
    printf 'seed-source-inventory/v1\nfiles:%d\n' "$count" || exit 1
    while IFS= read -r path; do
        mode=$(legacy_mode "$root/$path") || exit 1
        hash=$(legacy_sha256 "$root/$path") || exit 1
        printf 'path-bytes:%d\n%s\nmode:%s\nsha256:%s\n' "${#path}" "$path" "$mode" "$hash" || exit 1
    done < "$paths"
)

legacy_tree_digest() (
    set -o pipefail
    local root=$1 paths=$2 path hash
    {
        printf 'nauqtype-selfhost-source/v1\0' || exit 1
        while IFS= read -r path; do
            hash=$(legacy_sha256 "$root/$path") || exit 1
            printf '%s\0%s\0' "$path" "$hash" || exit 1
        done < "$paths"
    } | prov_hash_stream
)

legacy_checksum_paths() (
    set -o pipefail
    local root=$1 paths=$2 path
    {
        printf '%s\n' bootstrap/seed/generator-flags.txt bootstrap/seed/manifest.json \
            bootstrap/seed/nauqc-seed.c bootstrap/seed/runtime.c bootstrap/seed/runtime.h \
            bootstrap/seed/source-inventory-v1.txt || exit 1
        while IFS= read -r path; do printf 'bootstrap/seed/source-snapshot/%s\n' "$path" || exit 1; done < "$paths"
    } | LC_ALL=C sort
)

assert_equal() {
    local expected=$1 actual=$2 label=$3
    if [[ "$expected" != "$actual" ]]; then
        printf 'FAIL %s: expected <%s>, got <%s>\n' "$label" "$expected" "$actual" >&2
        exit 1
    fi
}

reject() {
    local label=$1
    shift
    if "$@" > "$scratch/reject.stdout" 2> "$scratch/reject.stderr"; then
        printf 'FAIL accepted %s\n' "$label" >&2
        exit 1
    fi
}

passed=0
legacy_source_paths "$snapshot" > "$scratch/paths"
seed_source_paths "$snapshot" > "$scratch/new-paths"
cmp -s "$scratch/paths" "$scratch/new-paths"
legacy_source_inventory "$snapshot" "$scratch/paths" > "$scratch/legacy.inventory"
seed_source_inventory_from_paths "$snapshot" "$scratch/new-paths" > "$scratch/new.inventory"
cmp -s "$scratch/legacy.inventory" "$scratch/new.inventory"
((passed += 1))

legacy_tree_digest "$snapshot" "$scratch/paths" > "$scratch/legacy.tree"
seed_source_tree_sha256 "$snapshot" > "$scratch/public.tree"
seed_source_tree_sha256_from_inventory "$scratch/new.inventory" > "$scratch/inventory.tree"
cmp -s "$scratch/legacy.tree" "$scratch/public.tree"
cmp -s "$scratch/public.tree" "$scratch/inventory.tree"
((passed += 1))

legacy_checksum_paths "$fixture" "$scratch/paths" > "$scratch/legacy.checksum-paths"
seed_checksum_paths "$fixture" > "$scratch/public.checksum-paths"
seed_checksum_paths_from_inventory "$scratch/new.inventory" > "$scratch/inventory.checksum-paths"
cmp -s "$scratch/legacy.checksum-paths" "$scratch/public.checksum-paths"
cmp -s "$scratch/public.checksum-paths" "$scratch/inventory.checksum-paths"
((passed += 1))

# Exercise strict inventory validation independent of the source-tree walk.
for kind in count order duplicate length mode hash extension traversal nul no-final-lf; do
    cp "$scratch/new.inventory" "$scratch/bad.inventory"
    case "$kind" in
        count) sed -i 's/^files:3$/files:4/' "$scratch/bad.inventory";;
        order) sed -i 's@selfhost/helper.nq@selfhost/0elper.nq@' "$scratch/bad.inventory";;
        duplicate) sed -i 's@selfhost/helper.nq@selfhost/empty.nq@' "$scratch/bad.inventory";;
        length) sed -i '0,/^path-bytes:[0-9][0-9]*$/s//path-bytes:999/' "$scratch/bad.inventory";;
        mode) sed -i 's/^mode:100644$/mode:100640/' "$scratch/bad.inventory";;
        hash) sed -i 's/^sha256:[0-9a-f]/sha256:Z/' "$scratch/bad.inventory";;
        extension) sed -i 's@selfhost/helper.nq@selfhost/helper.txt@' "$scratch/bad.inventory";;
        traversal) sed -i 's@selfhost/helper.nq@selfhost/../x.nq@' "$scratch/bad.inventory";;
        nul) printf '\0' >> "$scratch/bad.inventory";;
        no-final-lf) truncate -s -1 "$scratch/bad.inventory";;
    esac
    reject "inventory $kind" seed_source_tree_sha256_from_inventory "$scratch/bad.inventory"
    ((passed += 1))
done

# Fresh-path helper must reject unsafe actual source membership and modes.
ln -s main.nq "$snapshot/selfhost/link.nq"
reject 'symlink source member' seed_source_paths "$snapshot"
rm "$snapshot/selfhost/link.nq"
chmod 000 "$snapshot/selfhost/helper.nq"
reject 'unreadable source mode' seed_source_inventory_from_paths "$snapshot" "$scratch/paths"
chmod 644 "$snapshot/selfhost/helper.nq"
((passed += 1))

make_manifest() {
    local source_tree=$1 inventory_hash=$2 compiler_hash=$3 flags_hash=$4
    printf '{\n'
    printf '  "version": "nauqtype-c-seed/v2",\n'
    printf '  "source_entry": "selfhost/main.nq",\n'
    printf '  "source_tree_format": "nauqtype-selfhost-source/v1",\n'
    printf '  "source_tree_sha256": "%s",\n' "$source_tree"
    printf '  "source_inventory_sha256": "%s",\n' "$inventory_hash"
    printf '  "source_base_revision": null,\n'
    printf '  "source_index_tree": "0123456789abcdef0123456789abcdef01234567",\n'
    printf '  "source_dirty": false,\n'
    printf '  "predecessor_seed_c_sha256": "%s",\n' "$compiler_hash"
    printf '  "generator_exe_sha256": "%s",\n' "$compiler_hash"
    printf '  "generator_input_c_sha256": "%s",\n' "$compiler_hash"
    printf '  "generator_output_c_sha256": "%s",\n' "$compiler_hash"
    printf '  "compiler_c_sha256": "%s",\n' "$compiler_hash"
    printf '  "runtime_c_sha256": "%s",\n' "$(legacy_sha256 "$fixture/bootstrap/seed/runtime.c")"
    printf '  "runtime_h_sha256": "%s",\n' "$(legacy_sha256 "$fixture/bootstrap/seed/runtime.h")"
    printf '  "generator_cc_sha256": "%s",\n' "$compiler_hash"
    printf '  "generator_cc_version_sha256": "%s",\n' "$compiler_hash"
    printf '  "generator_cc_target": "x86_64-linux-gnu",\n'
    printf '  "generator_flags_sha256": "%s"\n' "$flags_hash"
    printf '}\n'
}

seed_source_inventory_from_paths "$snapshot" "$scratch/paths" > "$fixture/bootstrap/seed/source-inventory-v1.txt"
inventory_hash=$(legacy_sha256 "$fixture/bootstrap/seed/source-inventory-v1.txt")
tree_hash=$(legacy_tree_digest "$snapshot" "$scratch/paths")
compiler_hash=$(legacy_sha256 "$fixture/bootstrap/seed/nauqc-seed.c")
flags_hash=$(legacy_sha256 "$fixture/bootstrap/seed/generator-flags.txt")
make_manifest "$tree_hash" "$inventory_hash" "$compiler_hash" "$flags_hash" > "$fixture/bootstrap/seed/manifest.json"
legacy_checksum_paths "$fixture" "$scratch/paths" > "$scratch/checksum-paths"
while IFS= read -r path; do
    hash=$(legacy_sha256 "$fixture/$path")
    printf '%s  %s\n' "$hash" "$path" >> "$fixture/bootstrap/seed/SHA256SUMS"
done < "$scratch/checksum-paths"
seed_verify "$fixture"
((passed += 1))

# Save the actual implementation under a test-local name, then shadow only the
# capture function to mutate source bytes and reseal SHA256SUMS after capture.
eval "$(declare -f seed_source_inventory_from_paths | sed '1s/seed_source_inventory_from_paths/seed_source_inventory_from_paths_unshadowed/')"
seed_source_inventory_from_paths() {
    local root=$1 paths=$2 captured="$scratch/shadow.inventory" path hash
    seed_source_inventory_from_paths_unshadowed "$root" "$paths" > "$captured" || return 1
    if [[ "${NQ_TEST_PAIRED_MUTATION:-0}" == 1 ]]; then
        printf 'persistent post-capture mutation\n' >> "$fixture/bootstrap/seed/source-snapshot/selfhost/helper.nq"
        legacy_source_paths "$fixture/bootstrap/seed/source-snapshot" > "$scratch/mutated.paths" || return 1
        legacy_checksum_paths "$fixture" "$scratch/mutated.paths" > "$scratch/mutated.checksum-paths" || return 1
        : > "$fixture/bootstrap/seed/SHA256SUMS"
        while IFS= read -r path; do
            hash=$(legacy_sha256 "$fixture/$path") || return 1
            printf '%s  %s\n' "$hash" "$path" >> "$fixture/bootstrap/seed/SHA256SUMS" || return 1
        done < "$scratch/mutated.checksum-paths"
    fi
    cat -- "$captured"
}
if NQ_TEST_PAIRED_MUTATION=1 seed_verify "$fixture" > "$scratch/paired.stdout" 2> "$scratch/paired.stderr"; then
    printf 'FAIL accepted paired post-capture source/checksum mutation\n' >&2
    exit 1
fi
[[ ! -s "$scratch/paired.stdout" ]]
((passed += 1))

printf 'seed capture differential oracle passed (%s assertions)\n' "$passed"
