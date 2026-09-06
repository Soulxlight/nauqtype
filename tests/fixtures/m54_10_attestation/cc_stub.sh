#!/usr/bin/env bash
# Metadata-only UNIT STUB, hashed as a real executable; never compiles anything.
set -euo pipefail
role=proof
[[ "${0##*/}" != bootstrap* ]] || role=bootstrap
case "${1:-}" in
    --version)
        [[ "${NQ_ATTEST_CC_FAIL:-}" != version ]] || exit 17
        if [[ "$role" == bootstrap ]]; then
            printf '%s\n' "${NQ_ATTEST_BOOTSTRAP_VERSION:-attestation bootstrap stub 1}"
        else
            printf '%s\n' "${NQ_ATTEST_PROOF_VERSION:-attestation proof stub 1}"
        fi
        ;;
    -dumpmachine)
        [[ "${NQ_ATTEST_CC_FAIL:-}" != target ]] || exit 18
        if [[ "$role" == bootstrap ]]; then
            printf '%s\n' "${NQ_ATTEST_BOOTSTRAP_TARGET:-fixture-bootstrap-linux}"
        else
            printf '%s\n' "${NQ_ATTEST_PROOF_TARGET:-fixture-proof-linux}"
        fi
        ;;
    *) printf 'attestation CC stub refuses compilation\n' >&2; exit 99;;
esac
