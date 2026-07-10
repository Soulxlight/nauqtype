#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

usage() {
    cat <<'EOF'
Usage: scripts/check_milestone.sh [unittest-module ...]

Run one full milestone confidence pass without repeating the same selfhost proof
and Linux release build in every sub-gate. Optional unittest modules should be
the feature-specific suites for the current milestone.

The M37 final gate still runs the full test suite and standalone release gates.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

summary_dir="$repo_root/build/verification"
summary_path="$summary_dir/milestone-summary.json"
mkdir -p "$summary_dir"

phase_ids=()
phase_seconds=()
active_phase="setup"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
run_started="$SECONDS"

write_summary() {
    local status="$1"
    local finished_at
    local total_seconds
    local index
    finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    total_seconds=$((SECONDS - run_started))
    {
        printf '{\n'
        printf '  "version": 1,\n'
        printf '  "command": "check-milestone",\n'
        printf '  "status": "%s",\n' "$status"
        printf '  "started_at": "%s",\n' "$started_at"
        printf '  "finished_at": "%s",\n' "$finished_at"
        printf '  "total_seconds": %s,\n' "$total_seconds"
        printf '  "failed_phase": '
        if [[ "$status" == "ok" ]]; then
            printf 'null,\n'
        else
            printf '"%s",\n' "$active_phase"
        fi
        printf '  "phases": [\n'
        for index in "${!phase_ids[@]}"; do
            printf '    {"id": "%s", "seconds": %s}' "${phase_ids[$index]}" "${phase_seconds[$index]}"
            if (( index + 1 < ${#phase_ids[@]} )); then
                printf ','
            fi
            printf '\n'
        done
        printf '  ]\n'
        printf '}\n'
    } > "$summary_path"
}

on_exit() {
    local code="$?"
    if (( code == 0 )); then
        write_summary ok
        printf 'milestone verification ok: %s\n' "$summary_path"
    else
        write_summary failed
        printf 'milestone verification failed during %s: %s\n' "$active_phase" "$summary_path" >&2
    fi
}
trap on_exit EXIT

run_phase() {
    local name="$1"
    local phase_started
    shift
    active_phase="$name"
    phase_started="$SECONDS"
    "$@"
    phase_ids+=("$name")
    phase_seconds+=("$((SECONDS - phase_started))")
}

run_phase stage1.bootstrap python3 -m compiler.main run selfhost/main.nq
run_phase stage1.driver python3 -m compiler.main build selfhost/main.nq -o selfhost/build/nauqc
run_phase proof bin/nauqc prove
run_phase linux_alpha scripts/check_linux_alpha.sh --reuse-stage1 --skip-prove
run_phase stress_leg scripts/run_stress_leg.sh --release-root build/linux-release/nauqtype
run_phase focused_tests scripts/check_fast.sh "$@"
