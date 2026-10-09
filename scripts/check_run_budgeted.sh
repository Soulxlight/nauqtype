#!/usr/bin/env bash
# Focused host-runner checks; these do not certify a compiler or proof.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
scratch=$(mktemp -d -t nauqtype-budget-tests-XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
passed=0

check_case() {
    local id=$1 expected_code=$2 expected_failure=$3 code=0
    shift 3
    bash "$script_dir/run_budgeted.sh" --id "$id" --wall-seconds 1 \
        --rss-kib 262144 --result "$scratch/$id.json" -- "$@" \
        > "$scratch/$id.stdout" 2> "$scratch/$id.stderr" || code=$?
    [[ "$code" == "$expected_code" ]]
    grep -Fqx "  \"failure\": \"$expected_failure\"," "$scratch/$id.json"
    grep -Fqx "  \"command_exit_code\": $expected_code," "$scratch/$id.json"
    passed=$((passed + 1))
    printf 'PASS %s\n' "$id"
}

check_case success 0 none bash -c 'printf stdout-ok; printf stderr-ok >&2'
[[ "$(< "$scratch/success.stdout")" == stdout-ok ]]
[[ "$(< "$scratch/success.stderr")" == stderr-ok ]]
check_case command7 7 command bash -c 'exit 7'
check_case command124 124 command bash -c 'exit 124'
check_case spoof124 124 command bash -c 'printf "timeout: sending signal TERM to command fake\n" >&2; exit 124'
check_case timeout124 124 wall_time sleep 2
grep -q 'ran longer than 1s' "$scratch/timeout124.stderr"

printf 'printf "timeout: sending signal TERM to command hook\\n" >&2\n' > "$scratch/hook"
BASH_ENV="$scratch/hook" check_case hook124 124 command bash -c 'exit 124'

code=0
bash "$script_dir/run_budgeted.sh" --id early-term --wall-seconds 60 \
    --rss-kib 262144 --result "$scratch/early-term.json" -- \
    bash -c 'trap "exit 124" TERM; ps -o ppid= -p "$PPID" | tr -d " " > "$1"; while :; do sleep 1; done' \
    _ "$scratch/ready" > "$scratch/early-term.stdout" 2> "$scratch/early-term.stderr" &
runner=$!
for (( attempt=0; attempt<100; attempt++ )); do
    [[ ! -s "$scratch/ready" ]] || break
    sleep 0.01
done
[[ -s "$scratch/ready" ]]
kill -TERM "$(< "$scratch/ready")"
wait "$runner" || code=$?
[[ "$code" == 124 ]]
grep -Fqx '  "failure": "command",' "$scratch/early-term.json"
passed=$((passed + 1))
printf 'PASS early-term\n'

check_case timeout137 137 command bash -c 'trap "" TERM; exec sleep 10'
check_case timeout-handler124 124 command bash -c 'trap "exit 124" TERM; sleep 2'
check_case not-a-builtin 127 command exit 7
printf '#!/bin/sh\nexit 7\n' > "$scratch/-budget-command"
chmod 755 "$scratch/-budget-command"
PATH="$scratch:$PATH" check_case dash-command 7 command -budget-command
printf '#!/bin/sh\nexit 6\n' > "$scratch/BUDGET_LITERAL=value"
chmod 755 "$scratch/BUDGET_LITERAL=value"
PATH="$scratch:$PATH" check_case assignment-command 6 command BUDGET_LITERAL=value
check_case assignment-path 6 command "$scratch/BUDGET_LITERAL=value"

code=0
bash "$script_dir/run_budgeted.sh" --id rss --wall-seconds 1 \
    --rss-kib 1 --result "$scratch/rss.json" -- true \
    > "$scratch/rss.stdout" 2> "$scratch/rss.stderr" || code=$?
[[ "$code" == 97 ]]
grep -Fqx '  "failure": "peak_rss",' "$scratch/rss.json"
grep -Fqx '  "command_exit_code": 0,' "$scratch/rss.json"
passed=$((passed + 1))
printf 'PASS rss\n'

printf 'budget runner fixtures passed (%s cases)\n' "$passed"
