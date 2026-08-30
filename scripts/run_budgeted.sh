#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/run_budgeted.sh --id <phase-id> --wall-seconds <seconds>
       --rss-kib <kibibytes> --result <path> -- <command> [args...]

Run one command under GNU timeout and /usr/bin/time. The command's stdout and
stderr remain visible, while deterministic measurement evidence is written to
the requested JSON result path. Exit 97 means the command completed but
exceeded its peak-RSS budget; timeout retains GNU timeout's exit 124.
EOF
}

phase_id=""
wall_limit=""
rss_limit=""
result_path=""

while (( $# > 0 )); do
    case "$1" in
        --id)
            phase_id="${2:-}"
            shift 2
            ;;
        --wall-seconds)
            wall_limit="${2:-}"
            shift 2
            ;;
        --rss-kib)
            rss_limit="${2:-}"
            shift 2
            ;;
        --result)
            result_path="${2:-}"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        *)
            printf 'run_budgeted: unknown option %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ ! "$phase_id" =~ ^[A-Za-z0-9._-]+$ ]]; then
    printf 'run_budgeted: --id must be a non-empty stable phase id\n' >&2
    exit 2
fi
if [[ ! "$wall_limit" =~ ^[1-9][0-9]*$ ]]; then
    printf 'run_budgeted: --wall-seconds must be a positive integer\n' >&2
    exit 2
fi
if [[ ! "$rss_limit" =~ ^[1-9][0-9]*$ ]]; then
    printf 'run_budgeted: --rss-kib must be a positive integer\n' >&2
    exit 2
fi
if [[ -z "$result_path" || $# -eq 0 ]]; then
    printf 'run_budgeted: --result and a command after -- are required\n' >&2
    exit 2
fi
if [[ ! -x /usr/bin/time ]]; then
    printf 'run_budgeted: GNU /usr/bin/time is required\n' >&2
    exit 2
fi
if [[ "$(/usr/bin/time --version 2>/dev/null | sed -n '1p')" != *"GNU Time"* ]]; then
    printf 'run_budgeted: GNU /usr/bin/time is required\n' >&2
    exit 2
fi
if ! command -v timeout >/dev/null 2>&1; then
    printf 'run_budgeted: GNU timeout is required\n' >&2
    exit 2
fi
if [[ "$(timeout --version 2>/dev/null | sed -n '1p')" != *"GNU coreutils"* ]]; then
    printf 'run_budgeted: GNU timeout is required\n' >&2
    exit 2
fi

result_dir="$(dirname -- "$result_path")"
mkdir -p "$result_dir"
metrics_path="$(mktemp "$result_dir/.budget-metrics.XXXXXX")"
result_tmp="$(mktemp "$result_dir/.budget-result.XXXXXX")"
cleanup() {
    rm -f -- "$metrics_path" "$result_tmp"
}
trap cleanup EXIT

set +e
LC_ALL=C /usr/bin/time \
    -f 'wall_seconds=%e\npeak_rss_kib=%M' \
    -o "$metrics_path" \
    timeout --signal=TERM --kill-after=5s -- "${wall_limit}s" "$@"
command_exit_code=$?
set -e

wall_seconds="$(sed -n 's/^wall_seconds=//p' "$metrics_path")"
peak_rss_kib="$(sed -n 's/^peak_rss_kib=//p' "$metrics_path")"
if [[ ! "$wall_seconds" =~ ^[0-9]+([.][0-9]+)?$ || ! "$peak_rss_kib" =~ ^[0-9]+$ ]]; then
    printf 'run_budgeted: GNU time did not produce valid metrics for %s\n' "$phase_id" >&2
    exit 2
fi

status="ok"
failure="none"
runner_exit_code=0
if (( command_exit_code == 124 )); then
    status="failed"
    failure="wall_time"
    runner_exit_code=124
elif (( command_exit_code != 0 )); then
    status="failed"
    failure="command"
    runner_exit_code="$command_exit_code"
elif (( peak_rss_kib > rss_limit )); then
    status="failed"
    failure="peak_rss"
    runner_exit_code=97
fi

{
    printf '{\n'
    printf '  "version": 1,\n'
    printf '  "id": "%s",\n' "$phase_id"
    printf '  "status": "%s",\n' "$status"
    printf '  "failure": "%s",\n' "$failure"
    printf '  "command_exit_code": %s,\n' "$command_exit_code"
    printf '  "wall_seconds": %s,\n' "$wall_seconds"
    printf '  "wall_limit_seconds": %s,\n' "$wall_limit"
    printf '  "peak_rss_kib": %s,\n' "$peak_rss_kib"
    printf '  "peak_rss_limit_kib": %s\n' "$rss_limit"
    printf '}\n'
} > "$result_tmp"
mv -- "$result_tmp" "$result_path"

case "$failure" in
    wall_time)
        printf 'performance budget exceeded: %s ran longer than %ss\n' \
            "$phase_id" "$wall_limit" >&2
        ;;
    peak_rss)
        printf 'performance budget exceeded: %s used %s KiB (limit %s KiB)\n' \
            "$phase_id" "$peak_rss_kib" "$rss_limit" >&2
        ;;
    command)
        printf 'budgeted command failed: %s exited %s\n' \
            "$phase_id" "$command_exit_code" >&2
        ;;
esac

exit "$runner_exit_code"
