#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
source "$script_dir/provenance.sh"
source "$script_dir/seed_manifest.sh"
usage() { printf 'Usage: scripts/check_seed_bootstrap.sh [--reuse-stage1]\n'; }
reuse_stage1=false
case "${1:-}" in
    --reuse-stage1) reuse_stage1=true; shift;;
    -h|--help) usage; exit 0;;
esac
(( $# == 0 )) || { usage >&2; exit 2; }
mkdir -p "$repo_root/build/seed"
report="$repo_root/build/seed/seed-bootstrap-proof-v1.txt"
rm -f -- "$report"
work_dir=$(mktemp -d -t nauqtype-seed-proof-XXXXXX)
trap 'rm -rf -- "$work_dir"' EXIT
seed_verify "$repo_root"
prov_input_paths "$repo_root" > "$work_dir/paths"
inputs_hash=$(prov_files_digest "$repo_root" nauqtype-build-inputs/v2 "$work_dir/paths")
prov_cc_identity "${CC:-cc}" "$work_dir/cc-before"
snapshot="$work_dir/input"
prov_capture_inputs "$repo_root" "$snapshot" "$work_dir/paths" "$inputs_hash"
mkdir -p "$snapshot/build/seed" "$snapshot/selfhost/build"
if [[ "$reuse_stage1" == true ]]; then
    bash "$repo_root/scripts/stage1_cache.sh" require
    for path in build/seed/nauqc-seed build/seed/stage1.c selfhost/build/nauqc build/seed/stage1-derivation-v1.txt build/seed/stage1-cache-v2.txt; do
        prov_regular "$repo_root/$path"
        cp --preserve=mode -- "$repo_root/$path" "$snapshot/$path"
    done
    bash "$snapshot/scripts/stage1_cache.sh" require
else
    bash "$snapshot/scripts/build_stage1_from_seed.sh" >/dev/null
fi
seed_exe="$snapshot/build/seed/nauqc-seed"
stage1_c="$snapshot/build/seed/stage1.c"
stage1_exe="$snapshot/selfhost/build/nauqc"
historical_root="$snapshot/bootstrap/seed/source-snapshot"
historical_hash=$(seed_source_tree_sha256 "$historical_root")
current_hash=$(seed_source_tree_sha256 "$snapshot" source)
seed_manifest_read "$snapshot/bootstrap/seed/manifest.json" "$work_dir/seed-fields"
declare -A seed_fields=()
while IFS='=' read -r key value; do seed_fields[$key]=$value; done < "$work_dir/seed-fields"
historical_c="$historical_root/build/seed/stage1.c"
historical_reused=false
# Both invocations use this very seed emitter and identical relative argv.
# Flat loading explicitly excludes manifests; runtimes are compilation-only.
prov_flat_loading "$snapshot"
prov_flat_loading "$historical_root"
mapfile -d '' -t emit_args < <(prov_seed_emit_args)
emitter_hash=$(prov_sha256 "$seed_exe")
receipt_emitter=$(sed -n 's/^seed_exe_sha256=//p' "$snapshot/build/seed/stage1-derivation-v1.txt")
if [[ "${seed_fields[source_tree_format]}" == nauqtype-selfhost-source/v1 &&
      "${seed_fields[source_entry]}" == "${emit_args[1]}" &&
      "${seed_fields[source_tree_sha256]}" == "$historical_hash" &&
      "$current_hash" == "$historical_hash" && "$emitter_hash" == "$receipt_emitter" ]]; then
    historical_c="$stage1_c"
    historical_reused=true
else
    mkdir -p "$historical_root/build/seed"
    (cd "$historical_root" && "$seed_exe" "${emit_args[@]}")
fi
# Keep BOTH direct normalized comparisons, including in the reuse branch.
(cd "$snapshot" && "$stage1_exe" prove-seed "$historical_c" bootstrap/seed/nauqc-seed.c)
historical_c_hash=$(prov_sha256 "$historical_c")
(
    cd "$snapshot"
    prov_flat_loading "$snapshot"
    "$stage1_exe" emit-c selfhost/main.nq -o build/seed/stage2.c
    "$stage1_exe" prove-seed build/seed/stage1.c build/seed/stage2.c
)
# Historical proof output is not historical source material.
if [[ "$historical_reused" == false ]]; then rm -rf -- "$historical_root/build"; fi
prov_cc_identity "${CC:-cc}" "$work_dir/cc-after"
cmp -s "$work_dir/cc-before" "$work_dir/cc-after"
[[ "$(prov_inputs_sha256 "$snapshot")" == "$inputs_hash" ]]
[[ "$(prov_inputs_sha256 "$repo_root")" == "$inputs_hash" ]]
if [[ "$reuse_stage1" == true ]]; then bash "$repo_root/scripts/stage1_cache.sh" require; fi
{
    printf 'seed-bootstrap-proof/v1\nhistorical_reused=%s\n' "$historical_reused"
    printf 'historical_source_sha256=%s\ncurrent_source_sha256=%s\n' "$historical_hash" "$current_hash"
    printf 'seed_emitter_sha256=%s\n' "$emitter_hash"
    printf 'historical_c_sha256=%s\nseed_c_sha256=%s\n' "${historical_c_hash:?}" "$(prov_sha256 "$snapshot/bootstrap/seed/nauqc-seed.c")"
    printf 'stage1_c_sha256=%s\nstage2_c_sha256=%s\n' "$(prov_sha256 "$stage1_c")" "$(prov_sha256 "$snapshot/build/seed/stage2.c")"
    printf 'historical_c_equal=true\ncurrent_c_equal=true\n'
} > "$work_dir/report"
mv -f -- "$work_dir/report" "$report"
printf 'seed bootstrap proof ok (historical_reused=%s)\n' "$historical_reused"
