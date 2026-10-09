#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

usage() {
    cat <<'EOF'
Usage: scripts/check_str_join.sh [--cached-driver | --driver PATH]

Always run the focused native runtime ownership/allocation probes. Optional
driver modes copy the focused runner and text helper into a temporary
workspace, emit and execute run_str_join_gate, then time the benchmark using
either the verified stage1 cache or an explicitly caller-pinned test driver.
EOF
}

driver_mode="runtime-only"
driver=""
if (( $# == 1 )) && [[ "$1" == "--help" || "$1" == "-h" ]]; then usage; exit 0; fi
if (( $# == 1 )) && [[ "$1" == "--cached-driver" ]]; then
    scripts/stage1_cache.sh require
    driver="$repo_root/selfhost/build/nauqc"
    driver_mode="cached"
elif (( $# == 2 )) && [[ "$1" == "--driver" ]]; then
    driver="$(realpath -- "$2")"
    [[ -x "$driver" ]] || { printf 'not an executable caller-pinned driver: %s\n' "$driver" >&2; exit 2; }
    driver_mode="caller-pinned"
elif (( $# != 0 )); then
    usage >&2
    exit 2
fi

cc="${CC:-cc}"
command -v "$cc" >/dev/null 2>&1 || { printf 'C compiler not found: %s\n' "$cc" >&2; exit 1; }
work_dir="$(mktemp -d -t nauqtype-str-join-XXXXXX)"
trap 'rm -rf -- "$work_dir"' EXIT
cp -a stdlib "$work_dir/stdlib"
flags=(-std=c11 -D_POSIX_C_SOURCE=200809L "-I$work_dir/stdlib" -pedantic-errors -Wall -Wextra -Werror -O2 -fsanitize=address,undefined -fno-sanitize-recover=all -DNQ_TEST_MAX_SEQUENCE_LENGTH=128 -DNQ_TEST_MAX_ALLOCATION_BYTES=128)

"$cc" "${flags[@]}" -DNQ_TEST_ALLOC_FAIL_AFTER=1000000 tests/fixtures/str_join/probe.c -o "$work_dir/runtime"
"$work_dir/runtime" semantics
"$work_dir/runtime" sequence
for mode in sequence-limit payload-limit; do
    code=0
    "$work_dir/runtime" "$mode" >"$work_dir/$mode.out" 2>"$work_dir/$mode.err" || code=$?
    [[ "$code" == 1 && ! -s "$work_dir/$mode.out" ]]
    grep -Fxq 'nauqtype runtime: size limit exceeded' "$work_dir/$mode.err"
done

for fail_after in 0 1; do
    "$cc" "${flags[@]}" "-DNQ_TEST_ALLOC_FAIL_AFTER=$fail_after" tests/fixtures/str_join/probe.c -o "$work_dir/oom-$fail_after"
    code=0
    "$work_dir/oom-$fail_after" oom >"$work_dir/oom-$fail_after.out" 2>"$work_dir/oom-$fail_after.err" || code=$?
    [[ "$code" == 1 && ! -s "$work_dir/oom-$fail_after.out" ]]
    grep -Fxq 'nauqtype runtime: out of memory' "$work_dir/oom-$fail_after.err"
done
printf 'str_join native runtime probes passed\n'

if [[ -n "$driver" ]]; then
    if [[ "$driver_mode" == caller-pinned ]]; then
        printf 'driver is caller-pinned test input; no release/cache identity is claimed\n'
    else
        printf 'driver identity verified by scripts/stage1_cache.sh require\n'
    fi
    probe_dir="$work_dir/nq-probe"
    mkdir -p "$probe_dir"
    cp selfhost/*.nq tests/fixtures/str_join/probe_main.nq "$probe_dir/"
    "$driver" emit-c "$probe_dir/probe_main.nq" -o "$work_dir/str-join-gate.c"
    "$cc" -std=c11 -D_POSIX_C_SOURCE=200809L "-I$work_dir/stdlib" -O2 "$work_dir/str-join-gate.c" "$work_dir/stdlib/runtime.c" -o "$work_dir/str-join-gate"
    "$work_dir/str-join-gate" "$driver"
    printf 'str_join gate entry executed through caller-selected driver\n'

    "$driver" check tests/fixtures/str_join/benchmark.nq
    "$driver" emit-c tests/fixtures/str_join/benchmark.nq -o "$work_dir/benchmark.c"
    "$cc" -std=c11 -D_POSIX_C_SOURCE=200809L "-I$work_dir/stdlib" -O2 "$work_dir/benchmark.c" "$work_dir/stdlib/runtime.c" -o "$work_dir/benchmark"
    concat_length=$("$work_dir/benchmark" concat)
    join_length=$("$work_dir/benchmark" join)
    [[ "$concat_length" == 160000 && "$join_length" == "$concat_length" ]]
    printf 'benchmark outputs match: %s bytes\n' "$concat_length"
    for mode in concat join; do
        printf 'timing %s: ' "$mode"
        /usr/bin/time -f 'wall=%e s max_rss=%M KiB' "$work_dir/benchmark" "$mode"
    done
fi
