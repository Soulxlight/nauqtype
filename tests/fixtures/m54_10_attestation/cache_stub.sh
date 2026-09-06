#!/usr/bin/env bash
# Explicit UNIT STUB. No compiler, seed, cache receipt, or build is validated.
set -euo pipefail
[[ "${1:-}" == require && $# == 1 ]] || exit 2
printf 'STUB stage1_cache require\n' >> "${NQ_ATTEST_STUB_LOG:?}"
[[ "${NQ_ATTEST_STUB_CACHE_FAIL:-0}" == 0 ]]
