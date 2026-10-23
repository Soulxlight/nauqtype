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
prov_cc_gc_profile_freeze "$cc_request" "$scratch/cc-before" "$scratch/cc-profile"
cc_profile=$(< "$scratch/cc-profile")
cc_arg_count=$(prov_cc_args_count "$cc_profile")
prov_argv_materialize "$scratch/cc-args" "$cc_arg_count" prov_seed_args "$cc_profile"
cc_args_hash=$(prov_sha256 "$scratch/cc-args")
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
prov_argv_load "$scratch/cc-args" "$cc_arg_count" cc_args "$cc_args_hash"
(cd "$snapshot" && "$cc_bin" "${cc_args[@]}")
[[ "$(prov_sha256 "$scratch/cc-args")" == "$cc_args_hash" ]] || { prov_error 'seed compiler argv changed during build'; exit 1; }
prov_regular "$snapshot/build/seed/nauqc-seed"
[[ -x "$snapshot/build/seed/nauqc-seed" ]]
prov_cc_identity "$cc_request" "$scratch/cc-after"
cmp -s "$scratch/cc-before" "$scratch/cc-after"
prov_cc_gc_profile_select "$cc_request" "$scratch/cc-before" "$scratch/cc-profile-after"
cmp -s "$scratch/cc-profile" "$scratch/cc-profile-after"
prov_tree_paths "$repo_root" bootstrap/seed all > "$scratch/paths-after"
cmp -s "$scratch/paths" "$scratch/paths-after"
[[ "$(prov_files_digest "$repo_root" nauqtype-build-inputs/v2 "$scratch/paths")" == "$before" ]]
[[ "$(prov_files_digest "$snapshot" nauqtype-build-inputs/v2 "$scratch/paths")" == "$before" ]]
[[ "$(prov_sha256 "$scratch/cc-args")" == "$cc_args_hash" ]] || { prov_error 'seed compiler argv changed before publication'; exit 1; }
mkdir -p -- "$(dirname -- "$output_path")"
mv -f -- "$snapshot/build/seed/nauqc-seed" "$output_path"
printf '%s\n' "$output_path"
