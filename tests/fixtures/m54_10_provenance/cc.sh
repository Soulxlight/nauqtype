#!/usr/bin/env bash
set -euo pipefail
# Synthetic host-CC wrapper. Only fixture code interprets these test controls.
case "${1:-}" in
    --version)
        if [[ "${NQ_TEST_MUTATION:-}" == cache-source ]]; then printf 'mutated during CC query\n' > "$NQ_TEST_ROOT/selfhost/main.nq"; fi
        printf 'fixture cc v1\n'; exit 0;;
    -dumpmachine) printf '%s\n' "${NQ_TEST_TARGET:-fixture-linux}"; exit 0;;
    -Q)
        [[ $# == 2 && "$2" == --help=params ]]
        case "${NQ_TEST_CC_PROFILE:-gcc}" in
            gcc)
                printf '  --param=ggc-min-expand=      100\n'
                printf '  --param=ggc-min-heapsize=   131072\n';;
            portable) printf 'fixture compiler has no GCC parameter rows\n';;
            exit1) exit 1;;
            exit2) exit 2;;
            *) exit 70;;
        esac
        exit 0;;
esac
expected_count=8
if [[ "${NQ_TEST_CC_PROFILE:-gcc}" == gcc ]]; then expected_count=10; fi
[[ $# == "$expected_count" && "$1" == -std=c11 && "$2" == -O2 && "$3" == -D_POSIX_C_SOURCE=200809L && "$7" == -o ]]
if (( expected_count == 10 )); then
    [[ "$9" == --param=ggc-min-expand=20 && "${10}" == --param=ggc-min-heapsize=32768 ]]
fi
case "$4" in
    -Ibootstrap/seed)
        [[ "$5" == bootstrap/seed/nauqc-seed.c && "$6" == bootstrap/seed/runtime.c && "$8" == build/seed/nauqc-seed ]]
        [[ "$(< bootstrap/seed/runtime.c)" == pinned-runtime-c && "$(< bootstrap/seed/runtime.h)" == pinned-runtime-h ]]
        printf 'compile:seed\n' >> "$NQ_TEST_LOG"
        case "${NQ_TEST_MUTATION:-}" in
            argv-seed)
                for args_file in "$NQ_TEST_ROOT"/build/seed/.bootstrap.*/cc-args; do
                    [[ -f "$args_file" ]] || continue
                    printf '%s\0' -std=c11 -O0 -D_POSIX_C_SOURCE=200809L -Ibootstrap/seed \
                        bootstrap/seed/nauqc-seed.c bootstrap/seed/runtime.c -o build/seed/nauqc-seed \
                        --param=ggc-min-expand=20 --param=ggc-min-heapsize=32768 > "$args_file"
                done;;
            persistent|restored)
                cp "$NQ_TEST_ROOT/selfhost/main.nq" "$NQ_TEST_STATE/source-before"
                printf 'MUTATED original source\n' > "$NQ_TEST_ROOT/selfhost/main.nq";;
            toolchain) printf '\n# persistent compiler mutation\n' >> "$0";;
        esac;;
    -Istdlib)
        [[ "$5" == build/seed/stage1.c && "$6" == stdlib/runtime.c && "$8" == selfhost/build/nauqc ]]
        [[ "$(< stdlib/runtime.c)" == current-runtime-c && "$(< stdlib/runtime.h)" == current-runtime-h ]]
        printf 'compile:stage1\n' >> "$NQ_TEST_LOG"
        if [[ "${NQ_TEST_MUTATION:-}" == argv-stage1 ]]; then
            for args_file in "$NQ_TEST_ROOT"/build/seed/.stage1-build.*/stage1-args; do
                [[ -f "$args_file" ]] || continue
                printf '%s\0' -std=c11 -O0 -D_POSIX_C_SOURCE=200809L -Istdlib \
                    build/seed/stage1.c stdlib/runtime.c -o selfhost/build/nauqc \
                    --param=ggc-min-expand=20 --param=ggc-min-heapsize=32768 > "$args_file"
            done
        fi
        if [[ "${NQ_TEST_MUTATION:-}" == restored ]]; then cp "$NQ_TEST_STATE/source-before" "$NQ_TEST_ROOT/selfhost/main.nq"; fi
        if [[ "${NQ_TEST_MUTATION:-}" == fail ]]; then exit 42; fi;;
    *) exit 1;;
esac
cp -- "$NQ_TEST_DRIVER" "$8"
chmod +x -- "$8"
