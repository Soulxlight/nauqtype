#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
source "$script_dir/provenance.sh"
source "$script_dir/seed_manifest.sh"
(( $# <= 1 )) || { printf 'Usage: scripts/build_stage1_from_seed.sh [output]\n' >&2; exit 2; }
work_dir="$repo_root/build/seed"
stage1_exe="${1:-$repo_root/selfhost/build/nauqc}"
default_stage1_exe="$repo_root/selfhost/build/nauqc"
manifest="$work_dir/stage1-cache-v2.txt"
cc_request="${CC:-cc}"
mkdir -p "$work_dir"
# A failed replacement must never leave a blessed manifest from an older run.
rm -f -- "$manifest"
scratch=$(mktemp -d "$work_dir/.stage1-build.XXXXXX")
trap 'rm -rf -- "$scratch"' EXIT
seed_verify "$repo_root"
prov_input_paths "$repo_root" > "$scratch/paths"
inputs_hash=$(prov_files_digest "$repo_root" nauqtype-build-inputs/v2 "$scratch/paths")
prov_cc_identity "$cc_request" "$scratch/cc-before"
cc_bin=$(sed -n 's/^cc_path=//p' "$scratch/cc-before")
prov_cc_gc_profile_select "$cc_request" "$scratch/cc-before" "$scratch/cc-profile"
cc_profile=$(< "$scratch/cc-profile")
prov_cc_gc_profile_transport_validate "$cc_profile"
cc_arg_count=$(prov_cc_args_count "$cc_profile")
prov_bootstrap_args_materialize "$cc_profile" "$scratch"
seed_args_hash=$(prov_sha256 "$scratch/seed-args")
stage1_args_hash=$(prov_sha256 "$scratch/stage1-args")
flags_hash=$(prov_bootstrap_flags_sha256_from_files "$cc_profile" "$scratch/seed-args" "$scratch/stage1-args")
argv_pins_match() {
    [[ "$(prov_sha256 "$scratch/seed-args")" == "$seed_args_hash" &&
       "$(prov_sha256 "$scratch/stage1-args")" == "$stage1_args_hash" &&
       "$(prov_bootstrap_flags_sha256_from_files "$cc_profile" "$scratch/seed-args" "$scratch/stage1-args")" == "$flags_hash" ]]
}
snapshot="$scratch/input"
prov_capture_inputs "$repo_root" "$snapshot" "$scratch/paths" "$inputs_hash"
seed_verify "$snapshot"
NQ_BOOTSTRAP_CC_GC_PROFILE="$cc_profile" CC="$cc_bin" bash "$snapshot/scripts/bootstrap_seed.sh" >/dev/null
argv_pins_match || { prov_error 'bootstrap argv changed during seed build'; exit 1; }
prov_flat_loading "$snapshot"
mkdir -p "$snapshot/selfhost/build"
(
    cd "$snapshot"
    mapfile -d '' -t emit_args < <(prov_seed_emit_args)
    build/seed/nauqc-seed "${emit_args[@]}"
    prov_argv_load "$scratch/stage1-args" "$cc_arg_count" cc_args "$stage1_args_hash"
    "$cc_bin" "${cc_args[@]}"
    argv_pins_match || { prov_error 'bootstrap argv changed during stage1 compilation'; exit 1; }
    selfhost/build/nauqc version > "$scratch/version-actual"
)
version=$(< "$snapshot/VERSION")
printf 'nauqc %s\n' "$version" > "$scratch/version-expected"
cmp -s "$scratch/version-expected" "$scratch/version-actual"
seed_exe_hash=$(prov_sha256 "$snapshot/build/seed/nauqc-seed")
stage1_c_hash=$(prov_sha256 "$snapshot/build/seed/stage1.c")
stage1_exe_hash=$(prov_sha256 "$snapshot/selfhost/build/nauqc")
seed_manifest_hash=$(prov_sha256 "$snapshot/bootstrap/seed/manifest.json")
{
    printf 'stage1-derivation/v1\n'
    printf 'inputs_sha256=%s\nseed_manifest_sha256=%s\nseed_exe_sha256=%s\nstage1_c_sha256=%s\nstage1_exe_sha256=%s\n' \
        "$inputs_hash" "$seed_manifest_hash" "$seed_exe_hash" "$stage1_c_hash" "$stage1_exe_hash"
    cat "$scratch/cc-before"
    printf 'flags_sha256=%s\n' "$flags_hash"
} > "$scratch/receipt"
receipt_hash=$(prov_sha256 "$scratch/receipt")
{
    printf 'stage1-cache/v2\ninputs_sha256=%s\nderivation_sha256=%s\nstage1_c_sha256=%s\nstage1_exe_sha256=%s\n' \
        "$inputs_hash" "$receipt_hash" "$stage1_c_hash" "$stage1_exe_hash"
} > "$scratch/manifest"
prov_cc_identity "$cc_request" "$scratch/cc-after"
cmp -s "$scratch/cc-before" "$scratch/cc-after"
prov_cc_gc_profile_select "$cc_request" "$scratch/cc-before" "$scratch/cc-profile-after"
cmp -s "$scratch/cc-profile" "$scratch/cc-profile-after"
[[ "$(prov_inputs_sha256 "$repo_root")" == "$inputs_hash" ]] || { prov_error 'original inputs changed during build'; exit 1; }
[[ "$(prov_inputs_sha256 "$snapshot")" == "$inputs_hash" ]] || { prov_error 'captured inputs changed during build'; exit 1; }
argv_pins_match || { prov_error 'bootstrap argv changed before publication'; exit 1; }
mkdir -p -- "$(dirname -- "$stage1_exe")"
mv -f -- "$snapshot/build/seed/nauqc-seed" "$work_dir/nauqc-seed"
mv -f -- "$snapshot/build/seed/stage1.c" "$work_dir/stage1.c"
mv -f -- "$snapshot/selfhost/build/nauqc" "$stage1_exe"
mv -f -- "$scratch/receipt" "$work_dir/stage1-derivation-v1.txt"
if [[ "$stage1_exe" == "$default_stage1_exe" ]]; then
    mv -f -- "$scratch/manifest" "$manifest"
fi
printf '%s\n' "$stage1_exe"
