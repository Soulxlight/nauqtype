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

timeout_shim="$scratch/timeout-shim"
mkdir "$timeout_shim"
printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -u' \
    'if [[ "$#" == 1 && "${1-}" == --version ]]; then exec /usr/bin/timeout "$@"; fi' \
    'args=("$@")' \
    'delimiter=-1' \
    'policy=-1' \
    'verbose=false' \
    'signal=false' \
    'for ((i=0; i<${#args[@]}; i++)); do' \
    '    case "${args[i]}" in' \
    '        --) delimiter=$i; break ;;' \
    '        --verbose) [[ "$verbose" == false ]] || exit 2; verbose=true ;;' \
    '        --signal=TERM) [[ "$signal" == false ]] || exit 2; signal=true ;;' \
    '        --kill-after=5s) [[ "$policy" == -1 ]] || exit 2; policy=$i ;;' \
    '        *) exit 2 ;;' \
    '    esac' \
    'done' \
    '(( delimiter >= 0 && policy >= 0 )) || exit 2' \
    'witness=${TIMEOUT_SHIM_WITNESS:-}' \
    '[[ -n "$witness" && ! -e "$witness" && ! -L "$witness" ]] || exit 2' \
    'if ! printf "%s\n" "${args[policy]}" > "$witness"; then exit 2; fi' \
    'args[policy]=--kill-after=0.01s' \
    'exec /usr/bin/timeout "${args[@]}"' \
    > "$timeout_shim/timeout"
chmod 755 "$timeout_shim/timeout"

expect_timeout_shim_reject() {
    local id=$1 code=0
    shift
    TIMEOUT_SHIM_WITNESS="$scratch/reject-$id.witness" \
        "$timeout_shim/timeout" "$@" -- 1s /usr/bin/touch "$scratch/reject-$id.executed" \
        > "$scratch/reject-$id.stdout" 2> "$scratch/reject-$id.stderr" || code=$?
    [[ "$code" == 2 && ! -e "$scratch/reject-$id.executed" ]]
}

expect_timeout_shim_reject missing --verbose --signal=TERM
expect_timeout_shim_reject duplicate --verbose --signal=TERM --kill-after=5s --kill-after=5s
expect_timeout_shim_reject wrong --verbose --signal=TERM --kill-after=2s
expect_timeout_shim_reject alias-short --verbose --signal=TERM -k 5s --kill-after=5s
expect_timeout_shim_reject alias-joined --verbose --signal=TERM -k5s --kill-after=5s
expect_timeout_shim_reject alias-long --verbose --signal=TERM --kill-after 5s --kill-after=5s
expect_timeout_shim_reject alias-abbreviated --verbose --signal=TERM --kill-af=2s --kill-after=5s
expect_timeout_shim_reject alias-bundled --verbose --signal=TERM -vk2s --kill-after=5s

mkdir "$scratch/witness-is-directory"
code=0
TIMEOUT_SHIM_WITNESS="$scratch/witness-is-directory" \
    "$timeout_shim/timeout" --verbose --signal=TERM --kill-after=5s -- \
    1s /usr/bin/touch "$scratch/witness-failure.executed" \
    > "$scratch/witness-failure.stdout" 2> "$scratch/witness-failure.stderr" || code=$?
[[ "$code" == 2 && ! -e "$scratch/witness-failure.executed" ]]

code=0
TIMEOUT_SHIM_WITNESS="$scratch/missing-parent/witness" \
    "$timeout_shim/timeout" --verbose --signal=TERM --kill-after=5s -- \
    1s /usr/bin/touch "$scratch/missing-parent.executed" \
    > "$scratch/missing-parent.stdout" 2> "$scratch/missing-parent.stderr" || code=$?
[[ "$code" == 2 && ! -e "$scratch/missing-parent.executed" ]]

printf '%s\n' 'stale witness' > "$scratch/stale.witness"
code=0
TIMEOUT_SHIM_WITNESS="$scratch/stale.witness" \
    "$timeout_shim/timeout" --verbose --signal=TERM --kill-after=5s -- \
    1s /usr/bin/touch "$scratch/stale-witness.executed" \
    > "$scratch/stale-witness.stdout" 2> "$scratch/stale-witness.stderr" || code=$?
[[ "$code" == 2 && ! -e "$scratch/stale-witness.executed" ]]
grep -Fqx 'stale witness' "$scratch/stale.witness"

TIMEOUT_SHIM_WITNESS="$scratch/version.witness" \
    "$timeout_shim/timeout" --version > "$scratch/shim-version.stdout" 2> "$scratch/shim-version.stderr"
/usr/bin/timeout --version > "$scratch/real-timeout-version.stdout" 2> "$scratch/real-timeout-version.stderr"
cmp -s "$scratch/shim-version.stdout" "$scratch/real-timeout-version.stdout"
cmp -s "$scratch/shim-version.stderr" "$scratch/real-timeout-version.stderr"
[[ ! -e "$scratch/version.witness" ]]

TIMEOUT_SHIM_WITNESS="$scratch/passthrough.witness" \
    "$timeout_shim/timeout" --verbose --signal=TERM --kill-after=5s -- \
    1s /usr/bin/printf '%s|%s' '--kill-after=5s' '--kill-after=2s' \
    > "$scratch/passthrough.stdout" 2> "$scratch/passthrough.stderr"
[[ "$(< "$scratch/passthrough.stdout")" == '--kill-after=5s|--kill-after=2s' ]]
[[ "$(< "$scratch/passthrough.witness")" == --kill-after=5s ]]

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

path_before_timeout137=$PATH
[[ ! -e "$scratch/timeout137.witness" && ! -L "$scratch/timeout137.witness" ]]
# Unit-only scaling preserves real TERM/KILL escalation; it is not a 5s elapsed-grace proof.
TIMEOUT_SHIM_WITNESS="$scratch/timeout137.witness" PATH="$timeout_shim:$PATH" \
    check_case timeout137 137 command bash -c 'trap "" TERM; exec sleep 10'
[[ "$PATH" == "$path_before_timeout137" ]]
grep -Fqx -- '--kill-after=5s' "$scratch/timeout137.witness"
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
