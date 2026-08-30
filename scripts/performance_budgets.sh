#!/usr/bin/env bash

# Initial Linux release ceilings. Values are intentionally above the measured
# M53 ownership-aware baseline so ordinary runner variance does not turn the
# first budget lock into noise. Tightening requires a controlled baseline and
# review.
readonly PERFORMANCE_BUDGET_VERSION=1

declare -Ar PERFORMANCE_WALL_SECONDS=(
    [seed_bootstrap]=900
    [stage1.driver]=900
    [proof]=2400
    [linux_alpha]=300
    [stress_leg]=300
    [owned_tests]=600
    [ownership_sanitizers]=300
)

declare -Ar PERFORMANCE_PEAK_RSS_KIB=(
    [seed_bootstrap]=1048576
    [stage1.driver]=524288
    [proof]=3145728
    [linux_alpha]=1572864
    [stress_leg]=1572864
    [owned_tests]=2097152
    [ownership_sanitizers]=1048576
)

performance_budget_for() {
    local phase_id="$1"
    if [[ -z "${PERFORMANCE_WALL_SECONDS[$phase_id]+defined}" ]]; then
        printf 'no performance budget is defined for phase %s\n' "$phase_id" >&2
        return 1
    fi
    printf '%s %s\n' \
        "${PERFORMANCE_WALL_SECONDS[$phase_id]}" \
        "${PERFORMANCE_PEAK_RSS_KIB[$phase_id]}"
}
