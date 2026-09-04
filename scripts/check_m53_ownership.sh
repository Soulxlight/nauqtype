#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

usage() {
    cat <<'EOF'
Usage: scripts/check_m53_ownership.sh

Emit, compile, and run the dense foundational value/runtime ownership fixtures
under the Linux address and leak sanitizers. The active stage1 driver must
already exist and match its checked source/artifact cache.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi
if (( $# > 0 )); then
    printf 'check_m53_ownership: no arguments are accepted\n' >&2
    exit 2
fi
scripts/stage1_cache.sh require
if ! command -v "${CC:-cc}" >/dev/null 2>&1; then
    printf 'check_m53_ownership: C compiler not found: %s\n' "${CC:-cc}" >&2
    exit 1
fi

work_dir="$(mktemp -d -t nauqtype-m53-ownership-XXXXXX)"
trap 'rm -rf "$work_dir"' EXIT

printf 'int main(void) { return 0; }\n' | "${CC:-cc}" \
    -x c - -fno-omit-frame-pointer -fsanitize=address \
    -o "$work_dir/sanitizer-probe"

fixtures=(
    tests/fixtures/m53_values/cleanup_control_flow.nq
    tests/fixtures/m53_ownership/copy_transfer_replacement.nq
    tests/fixtures/m53_ownership/control_boundaries.nq
    tests/fixtures/m53_ownership/bytes_cleanup.nq
    tests/fixtures/m53_ownership/temporary_field_snapshot.nq
    tests/fixtures/m54_runtime.nq
)

for fixture in "${fixtures[@]}"; do
    name="$(basename -- "$fixture" .nq)"
    emitted_c="$work_dir/$name.c"
    executable="$work_dir/$name"
    bin/nauqc emit-c "$fixture" -o "$emitted_c"
    "${CC:-cc}" \
        -std=c11 \
        -D_POSIX_C_SOURCE=200809L \
        -fno-omit-frame-pointer \
        -fsanitize=address \
        -Istdlib \
        "$emitted_c" \
        stdlib/runtime.c \
        -o "$executable"
    ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 \
        LSAN_OPTIONS=exitcode=23 \
        "$executable"
done

printf 'm53 ownership sanitizer ok\n'
