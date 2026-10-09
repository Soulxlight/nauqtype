#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
root=$(cd -- "$script_dir/.." && pwd -P)
(( $# == 2 )) || { printf 'Usage: scripts/check_normalizer_index.sh <verified-reference-driver> <retained-output-dir>\n' >&2; exit 2; }
reference=$(realpath -- "$1")
out=$(realpath -m -- "$2")
[[ -x "$reference" && ! -e "$out" ]] || exit 2
mkdir -p "$out"
cp -- "$root/selfhost/text.nq" "$out/text.nq"
{
    printf 'use text;\n'
    awk '/^type norm_/ { types=1 } /^type corpus_case/ { types=0 } types { print }' "$root/selfhost/proof.nq"
    awk '/^fn make_norm_mapping/ { helpers=1 } /^fn make_corpus_case/ { helpers=0 } /^fn make_norm_token/ { helpers=1 } /^fn normalize_newlines/ { helpers=0 } helpers { print }' "$root/selfhost/proof.nq"
    cat "$root/tests/fixtures/p2_normalizer/probe_main.nq"
} > "$out/main.nq"
sha256sum "$root/selfhost/proof.nq" "$root/selfhost/text.nq" "$root/tests/fixtures/p2_normalizer/probe_main.nq" "$root/stdlib/runtime.c" "$root/stdlib/runtime.h" "$script_dir/check_normalizer_index.sh" "$script_dir/check_p2_normalizer.sh" "$script_dir/check_e1_normalizer.sh" "$reference" /usr/bin/cc > "$out/identities-before.txt"
printf '%s\0' -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -I "$root/stdlib" "$out/main.c" "$root/stdlib/runtime.c" -o "$out/probe" > "$out/flags.txt"
"$reference" emit-c "$out/main.nq" -o "$out/main.c" > "$out/emit.stdout.log" 2> "$out/emit.stderr.log"
cc -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -I "$root/stdlib" "$out/main.c" "$root/stdlib/runtime.c" -o "$out/probe"
bash "$script_dir/check_p2_normalizer.sh" "$reference" "$out/probe" > "$out/oracle.stdout.log" 2> "$out/oracle.stderr.log"
printf '%s\0' -std=c11 -O1 -D_POSIX_C_SOURCE=200809L -fsanitize=address,undefined -fno-omit-frame-pointer -I "$root/stdlib" "$out/main.c" "$root/stdlib/runtime.c" -o "$out/probe-sanitized" > "$out/sanitizer-flags.txt"
cc -std=c11 -O1 -D_POSIX_C_SOURCE=200809L -fsanitize=address,undefined -fno-omit-frame-pointer -I "$root/stdlib" "$out/main.c" "$root/stdlib/runtime.c" -o "$out/probe-sanitized"
ASAN_OPTIONS=detect_leaks=1 bash "$script_dir/check_p2_normalizer.sh" "$reference" "$out/probe-sanitized" > "$out/sanitizer.stdout.log" 2> "$out/sanitizer.stderr.log"
sha256sum -c "$out/identities-before.txt"
sha256sum "$out/main.nq" "$out/main.c" "$out/probe" "$out/probe-sanitized" "$out/flags.txt" "$out/sanitizer-flags.txt" > "$out/identities-after.txt"
cat "$out/oracle.stdout.log"
