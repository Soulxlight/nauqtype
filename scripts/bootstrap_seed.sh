#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
source "$script_dir/provenance.sh"
source "$script_dir/seed_manifest.sh"
(( $# <= 1 )) || { printf 'Usage: scripts/bootstrap_seed.sh [output]\n' >&2; exit 2; }
output_path="${1:-$repo_root/build/seed/nauqc-seed}"
cc_request="${CC:-cc}"

seed_verify "$repo_root"
mkdir -p "$repo_root/build/seed"
scratch=$(mktemp -d "$repo_root/build/seed/.bootstrap.XXXXXX")
trap 'rm -rf -- "$scratch"' EXIT
prov_cc_identity "$cc_request" "$scratch/cc-before"
cc_bin=$(sed -n 's/^cc_path=//p' "$scratch/cc-before")
prov_tree_paths "$repo_root" bootstrap/seed all > "$scratch/paths"
before=$(prov_files_digest "$repo_root" nauqtype-build-inputs/v2 "$scratch/paths")
snapshot="$scratch/input"
while IFS= read -r path; do
    mkdir -p -- "$snapshot/${path%/*}"
    cp --preserve=mode -- "$repo_root/$path" "$snapshot/$path"
done < "$scratch/paths"
[[ "$(prov_files_digest "$snapshot" nauqtype-build-inputs/v2 "$scratch/paths")" == "$before" ]]
seed_verify "$snapshot"
mkdir -p "$snapshot/build/seed"
mapfile -d '' -t cc_args < <(prov_seed_args)
(cd "$snapshot" && "$cc_bin" "${cc_args[@]}")
prov_regular "$snapshot/build/seed/nauqc-seed"
[[ -x "$snapshot/build/seed/nauqc-seed" ]]
prov_cc_identity "$cc_request" "$scratch/cc-after"
cmp -s "$scratch/cc-before" "$scratch/cc-after"
prov_tree_paths "$repo_root" bootstrap/seed all > "$scratch/paths-after"
cmp -s "$scratch/paths" "$scratch/paths-after"
[[ "$(prov_files_digest "$repo_root" nauqtype-build-inputs/v2 "$scratch/paths")" == "$before" ]]
[[ "$(prov_files_digest "$snapshot" nauqtype-build-inputs/v2 "$scratch/paths")" == "$before" ]]
mkdir -p -- "$(dirname -- "$output_path")"
mv -f -- "$snapshot/build/seed/nauqc-seed" "$output_path"
printf '%s\n' "$output_path"
