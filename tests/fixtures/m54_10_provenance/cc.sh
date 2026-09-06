#!/usr/bin/env bash
set -euo pipefail
# Synthetic host-CC wrapper. Only fixture code interprets these test controls.
case "${1:-}" in
    --version)
        if [[ "${NQ_TEST_MUTATION:-}" == cache-source ]]; then printf 'mutated during CC query\n' > "$NQ_TEST_ROOT/selfhost/main.nq"; fi
        printf 'fixture cc v1\n'; exit 0;;
    -dumpmachine) printf '%s\n' "${NQ_TEST_TARGET:-fixture-linux}"; exit 0;;
esac
[[ $# == 8 && "$1" == -std=c11 && "$2" == -O2 && "$3" == -D_POSIX_C_SOURCE=200809L && "$7" == -o ]]
case "$4" in
    -Ibootstrap/seed)
        [[ "$5" == bootstrap/seed/nauqc-seed.c && "$6" == bootstrap/seed/runtime.c && "$8" == build/seed/nauqc-seed ]]
        [[ "$(< bootstrap/seed/runtime.c)" == pinned-runtime-c && "$(< bootstrap/seed/runtime.h)" == pinned-runtime-h ]]
        printf 'compile:seed\n' >> "$NQ_TEST_LOG"
        case "${NQ_TEST_MUTATION:-}" in
            persistent|restored)
                cp "$NQ_TEST_ROOT/selfhost/main.nq" "$NQ_TEST_STATE/source-before"
                printf 'MUTATED original source\n' > "$NQ_TEST_ROOT/selfhost/main.nq";;
            toolchain) printf '\n# persistent compiler mutation\n' >> "$0";;
        esac;;
    -Istdlib)
        [[ "$5" == build/seed/stage1.c && "$6" == stdlib/runtime.c && "$8" == selfhost/build/nauqc ]]
        [[ "$(< stdlib/runtime.c)" == current-runtime-c && "$(< stdlib/runtime.h)" == current-runtime-h ]]
        printf 'compile:stage1\n' >> "$NQ_TEST_LOG"
        if [[ "${NQ_TEST_MUTATION:-}" == restored ]]; then cp "$NQ_TEST_STATE/source-before" "$NQ_TEST_ROOT/selfhost/main.nq"; fi
        if [[ "${NQ_TEST_MUTATION:-}" == fail ]]; then exit 42; fi;;
    *) exit 1;;
esac
cp -- "$NQ_TEST_DRIVER" "$8"
chmod +x -- "$8"
