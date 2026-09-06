#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

usage() {
    cat <<'EOF'
Usage: scripts/check_milestone.sh

Run one full milestone confidence pass without repeating the same selfhost proof
and Linux release build in every sub-gate. The active fixture/tooling test
surface is Nauqtype-owned and runs through `nauqc test`; copied-selfhost and
corpus claims run once through `nauqc prove`.

Every existing phase runs once under checked-in wall-time and peak-RSS budgets.
Performance evidence is separate from the proof summary.

The M37 final gate still runs the full test suite and standalone release gates.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

summary_dir="$repo_root/build/verification"
summary_path="$summary_dir/milestone-summary.json"
performance_summary_path="$summary_dir/performance-summary.json"
performance_result_dir="$summary_dir/performance-results"
mkdir -p "$summary_dir"
mkdir -p "$performance_result_dir"

# shellcheck source=performance_budgets.sh
source "$script_dir/performance_budgets.sh"

phase_ids=()
phase_seconds=()
performance_phase_ids=()
performance_statuses=()
performance_failures=()
performance_wall_seconds=()
performance_wall_limits=()
performance_peak_rss_kib=()
performance_peak_rss_limits=()
performance_command_exit_codes=()
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

json_string_field() {
    local field="$1"
    local path="$2"
    sed -n "s/^  \"$field\": \"\\([^\"]*\\)\",*$/\\1/p" "$path"
}

json_number_field() {
    local field="$1"
    local path="$2"
    sed -n "s/^  \"$field\": \\([0-9.]*\\),*$/\\1/p" "$path"
}

record_performance_result() {
    local name="$1"
    local result_path="$2"
    local wall_limit="$3"
    local rss_limit="$4"
    local result_status=""
    local result_failure=""
    local result_wall_seconds=""
    local result_peak_rss_kib=""
    local result_command_exit_code=""
    performance_phase_ids+=("$name")
    if [[ -f "$result_path" ]]; then
        result_status="$(json_string_field status "$result_path")"
        result_failure="$(json_string_field failure "$result_path")"
        result_wall_seconds="$(json_number_field wall_seconds "$result_path")"
        result_peak_rss_kib="$(json_number_field peak_rss_kib "$result_path")"
        result_command_exit_code="$(json_number_field command_exit_code "$result_path")"
    fi
    if [[ -z "$result_status" || -z "$result_failure" || \
          -z "$result_wall_seconds" || -z "$result_peak_rss_kib" || \
          -z "$result_command_exit_code" ]]; then
        performance_statuses+=("failed")
        performance_failures+=("infrastructure")
        performance_wall_seconds+=("0")
        performance_peak_rss_kib+=("0")
        performance_command_exit_codes+=("-1")
    else
        performance_statuses+=("$result_status")
        performance_failures+=("$result_failure")
        performance_wall_seconds+=("$result_wall_seconds")
        performance_peak_rss_kib+=("$result_peak_rss_kib")
        performance_command_exit_codes+=("$result_command_exit_code")
    fi
    performance_wall_limits+=("$wall_limit")
    performance_peak_rss_limits+=("$rss_limit")
}

write_performance_summary() {
    local status="$1"
    local index
    {
        printf '{\n'
        printf '  "version": %s,\n' "$PERFORMANCE_BUDGET_VERSION"
        printf '  "command": "check-milestone",\n'
        printf '  "status": "%s",\n' "$status"
        printf '  "failed_phase": '
        if [[ "$status" == "ok" ]]; then
            printf 'null,\n'
        else
            printf '"%s",\n' "$active_phase"
        fi
        printf '  "phases": [\n'
        for index in "${!performance_phase_ids[@]}"; do
            printf '    {"id": "%s", "status": "%s", "failure": "%s", ' \
                "${performance_phase_ids[$index]}" \
                "${performance_statuses[$index]}" \
                "${performance_failures[$index]}"
            printf '"command_exit_code": %s, ' \
                "${performance_command_exit_codes[$index]}"
            printf '"wall_seconds": %s, "wall_limit_seconds": %s, ' \
                "${performance_wall_seconds[$index]}" \
                "${performance_wall_limits[$index]}"
            printf '"peak_rss_kib": %s, "peak_rss_limit_kib": %s}' \
                "${performance_peak_rss_kib[$index]}" \
                "${performance_peak_rss_limits[$index]}"
            if (( index + 1 < ${#performance_phase_ids[@]} )); then
                printf ','
            fi
            printf '\n'
        done
        printf '  ]\n'
        printf '}\n'
    } > "$performance_summary_path"
}

on_exit() {
    local code="$?"
    if (( code == 0 )); then
        write_summary ok
        write_performance_summary ok
        printf 'milestone verification ok: %s\n' "$summary_path"
    else
        write_summary failed
        write_performance_summary failed
        printf 'milestone verification failed during %s: %s\n' "$active_phase" "$summary_path" >&2
    fi
}
trap on_exit EXIT

run_phase() {
    local name="$1"
    local phase_started
    local wall_limit
    local rss_limit
    local result_path
    local code=0
    shift
    active_phase="$name"
    phase_started="$SECONDS"
    read -r wall_limit rss_limit < <(performance_budget_for "$name")
    result_path="$performance_result_dir/$name.json"
    : > "$result_path"
    "$script_dir/run_budgeted.sh" \
        --id "$name" \
        --wall-seconds "$wall_limit" \
        --rss-kib "$rss_limit" \
        --result "$result_path" \
        -- "$@" || code=$?
    record_performance_result "$name" "$result_path" "$wall_limit" "$rss_limit"
    if (( code != 0 )); then
        return "$code"
    fi
    phase_ids+=("$name")
    phase_seconds+=("$((SECONDS - phase_started))")
}

active_phase="candidate_capture"
scripts/milestone_attestation.sh begin
run_phase stage1.driver scripts/build_stage1_from_seed.sh
run_phase seed_bootstrap scripts/check_seed_bootstrap.sh --reuse-stage1
run_phase proof bin/nauqc prove
run_phase linux_alpha scripts/check_linux_alpha.sh --reuse-stage1 --skip-prove
run_phase stress_leg scripts/run_stress_leg.sh --release-root build/linux-release/nauqtype
run_phase owned_tests scripts/check_fast.sh
run_phase ownership_sanitizers scripts/check_m53_ownership.sh
active_phase="attestation"
scripts/milestone_attestation.sh finish
scripts/milestone_attestation.sh verify
