#!/usr/bin/env bash
# UNIT LAYER ONLY: seed/cache derivation is covered by the provenance/full gate.
# Attestation, Git state, JSON, file hashes, and CC identity code are not stubbed.
set -euo pipefail
source "${NQ_ATTEST_IMPLEMENTATION:?attestation implementation required}"

seed_verify() {
    printf 'STUB seed_verify %s\n' "$1" >> "${NQ_ATTEST_STUB_LOG:?}"
    [[ "${NQ_ATTEST_STUB_SEED_FAIL:-0}" == 0 ]]
}

operation=${1:?operation required}
shift
case "$operation" in
    begin) attest_begin "$@";;
    finish) attest_finish "$@";;
    verify) attest_verify "$@";;
    close) attest_close "$@";;
    verify-close) attest_verify_close "$@";;
    exercise)
        attest_begin "$1"
        attest_finish "$1"
        attest_verify "$1"
        ;;
    fields) attest_fields;;
    close-fields) attest_close_fields;;
    parse)
        kind=$1 file=$2 output=$3
        fields=$(mktemp)
        trap 'rm -f -- "$fields"' EXIT
        case "$kind" in
            attestation) attest_fields > "$fields";;
            start) attest_start_fields > "$fields";;
            close) attest_close_fields > "$fields";;
            *) exit 2;;
        esac
        attest_json_read "$file" "$fields" "$output"
        ;;
    *) printf 'unknown attestation test operation: %s\n' "$operation" >&2; exit 2;;
esac
