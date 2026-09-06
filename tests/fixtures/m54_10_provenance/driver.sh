#!/usr/bin/env bash
set -euo pipefail
# This is deliberately not a compiler; tests assert shell provenance only.
case "${1:-}" in
    version) printf 'nauqc %s\n' "${NQ_TEST_VERSION:-fixture-version}";;
    emit-c)
        [[ $# == 4 && "$2" == selfhost/main.nq && "$3" == -o ]]
        printf 'emit:%s\n' "$4" >> "$NQ_TEST_LOG"
        cp -- "$2" "$4";;
    prove-seed)
        [[ $# == 3 ]]
        printf 'compare\n' >> "$NQ_TEST_LOG"
        cmp -s -- "$2" "$3";;
    *) exit 2;;
esac
