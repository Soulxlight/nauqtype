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
report="$repo_root/build/seed/seed-bootstrap-proof-v1.txt"
phase_report="$repo_root/build/verification/seed-bootstrap-phases-v1.json"
rm -f -- "$report" "$phase_report"
mkdir -p "$repo_root/build/seed" "$repo_root/build/verification"
phase_tmp=$(mktemp "$repo_root/build/verification/.seed-bootstrap-phases.XXXXXX")
work_dir=""
inputs_hash=""
phase_ids=(historical_compare stage2_emit current_compare)
phase_status=(not_run not_run not_run)
phase_wall=(null null null)
phase_code=(null null null)
phase_active=-1
phase_started=0
phase_boundary=setup
phase_signal=""
phase_overall=running

# Diagnostic sidecar only: the aggregate run_budgeted.sh invocation still owns
# the wall/RSS ceilings. A signal is not proof of a timeout. SECONDS records
# elapsed wall time at one-second resolution; an untrappable kill leaves running.
write_phase_report() {
    local exit_code=${1:-null} index comma signal=null input=null
    [[ -z "$phase_signal" ]] || signal="\"$phase_signal\""
    [[ -z "$inputs_hash" ]] || input="\"$inputs_hash\""
    {
        printf '{\n  "version": 1,\n  "kind": "seed-bootstrap-phases",\n' || return 1
        printf '  "status": "%s",\n  "active_phase": "%s",\n' "$phase_overall" "$phase_boundary" || return 1
        printf '  "exit_code": %s,\n  "termination_signal": %s,\n' "$exit_code" "$signal" || return 1
        printf '  "inputs_sha256": %s,\n  "wall_seconds_resolution": 1,\n  "phases": [\n' "$input" || return 1
        for index in 0 1 2; do
            comma=,
            (( index != 2 )) || comma=""
            printf '    {"id": "%s", "status": "%s", "wall_seconds": %s, "command_exit_code": %s}%s\n' \
                "${phase_ids[$index]}" "${phase_status[$index]}" "${phase_wall[$index]}" "${phase_code[$index]}" "$comma" || return 1
        done
        printf '  ]\n}\n' || return 1
    } > "$phase_tmp" || return 1
    mv -fT -- "$phase_tmp" "$phase_report" || return 1
}

on_seed_exit() {
    local code=$?
    # A signal during final publication must invalidate the installed receipt
    # without aborting this cleanup handler before it finishes.
    trap 'phase_signal=TERM; phase_overall=interrupted; (( code != 0 )) || code=143; rm -f -- "$report" "$phase_report"' TERM
    trap 'phase_signal=INT; phase_overall=interrupted; (( code != 0 )) || code=130; rm -f -- "$report" "$phase_report"' INT
    trap 'phase_signal=HUP; phase_overall=interrupted; (( code != 0 )) || code=129; rm -f -- "$report" "$phase_report"' HUP
    trap - EXIT
    set +e
    if (( phase_active >= 0 )) && [[ "${phase_status[$phase_active]}" == running ]]; then
        phase_wall[$phase_active]=$((SECONDS - phase_started))
        phase_status[$phase_active]=failed
        [[ -z "$phase_signal" ]] || phase_status[$phase_active]=interrupted
        # The wrapper did not observe a command result on this path.
        phase_code[$phase_active]=null
    fi
    if [[ -n "$phase_signal" ]]; then
        phase_overall=interrupted
    elif (( code != 0 )); then
        phase_overall=failed
    fi
    if ! write_phase_report "$code"; then
        printf 'seed bootstrap: could not finalize phase evidence\n' >&2 || :
        # Preserve an existing command/signal failure, but never pass without
        # the final evidence when the proof itself otherwise succeeded.
        (( code != 0 )) || code=1
    fi
    # A signal may have arrived while the final sidecar was being written.
    if [[ -n "$phase_signal" ]]; then
        write_phase_report "$code" || { printf 'seed bootstrap: could not record final interruption\n' >&2 || :; }
    fi
    # A failed invocation must not retain a success receipt, including failure
    # of the final sidecar write after the receipt was already installed.
    if (( code != 0 )); then rm -f -- "$report"; fi
    rm -f -- "$phase_tmp"
    if [[ -n "$work_dir" ]]; then rm -rf -- "$work_dir"; fi
    exit "$code"
}
trap on_seed_exit EXIT
# GNU timeout signals the process group, including the foreground command.
# A TERM sent only to this shell can be deferred until its command returns.
trap 'phase_signal=TERM; rm -f -- "$report" "$phase_report" || :; exit 143' TERM
trap 'phase_signal=INT; rm -f -- "$report" "$phase_report" || :; exit 130' INT
trap 'phase_signal=HUP; rm -f -- "$report" "$phase_report" || :; exit 129' HUP
write_phase_report
work_dir=$(mktemp -d -t nauqtype-seed-proof-XXXXXX)

run_seed_phase() {
    local index=$1 code
    shift
    phase_active=$index
    phase_boundary=${phase_ids[$index]}
    phase_status[$index]=running
    phase_started=$SECONDS
    # No completed duration is known until the command returns or a trap runs.
    phase_wall[$index]=null
    write_phase_report
    printf 'seed bootstrap phase started: %s\n' "$phase_boundary" || :
    # Only the direct command is conditional; provenance functions retain -e.
    if (cd "$snapshot" && "$@"); then code=0; else code=$?; fi
    phase_wall[$index]=$((SECONDS - phase_started))
    phase_code[$index]=$code
    phase_status[$index]=ok
    (( code == 0 )) || phase_status[$index]=failed
    if ! write_phase_report; then
        printf 'seed bootstrap: could not publish phase result\n' >&2 || :
        (( code != 0 )) || return 1
    fi
    printf 'seed bootstrap phase finished: %s status=%s exit=%s wall_seconds=%s\n' \
        "$phase_boundary" "${phase_status[$index]}" "$code" "${phase_wall[$index]}" || :
    return "$code"
}
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
run_seed_phase 0 "$stage1_exe" prove-seed "$historical_c" bootstrap/seed/nauqc-seed.c
phase_active=-1
phase_boundary=stage2_preparation
write_phase_report
historical_c_hash=$(prov_sha256 "$historical_c")
prov_flat_loading "$snapshot"
run_seed_phase 1 "$stage1_exe" emit-c selfhost/main.nq -o build/seed/stage2.c
run_seed_phase 2 "$stage1_exe" prove-seed build/seed/stage1.c build/seed/stage2.c
phase_active=-1
phase_boundary=provenance
write_phase_report
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
phase_boundary=complete
phase_overall=ok
