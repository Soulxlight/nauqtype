#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

usage() {
    cat <<'EOF'
Usage: scripts/check_fast.sh [unittest-module ...]

Run the focused, non-selfhost Python confidence tier. Optional unittest modules
are appended for the feature currently under development.

This tier intentionally excludes proof, copied-selfhost, and release-layout
tests. Those remain in check_milestone.sh and the M37 final gate.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

base_tests=(
    tests.test_ai_audit
    tests.test_bootstrap
    tests.test_borrow
    tests.test_codegen
    tests.test_contracts
    tests.test_diagnostics_json
    tests.test_field_assignment
    tests.test_golden
    tests.test_imports
    tests.test_lexer
    tests.test_parser
    tests.test_patterns
    tests.test_resolution
    tests.test_review
    tests.test_teaching_corpus
    tests.test_types
    tests.test_verification_scripts
)

python3 -m unittest -v "${base_tests[@]}" "$@"
