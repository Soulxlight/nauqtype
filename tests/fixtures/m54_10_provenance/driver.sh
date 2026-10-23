#!/usr/bin/env bash
set -euo pipefail
# This is deliberately not a compiler; tests assert shell provenance only.
probe_phase() {
    local phase=$1
    [[ "${NQ_TEST_PHASE:-}" == "$phase" ]] || return 0
    case "${NQ_TEST_PHASE_ACTION:-}" in
        fail) exit 7;;
        exit124) exit 124;;
        block)
            printf 'phase-blocked:%s\n' "$phase" >> "$NQ_TEST_LOG"
            while :; do sleep 1; done;;
        mutate) printf 'changed captured source\n' > selfhost/main.nq;;
        mutate-generic) printf 'changed captured generic source\n' > examples/generic_values.nq;;
        generic-manifest) printf '{}\n' > examples/nauqtype.workspace.json;;
        generic-lock) printf '{}\n' > examples/nauqtype.workspace.lock.json;;
        original-generic-manifest) printf '{}\n' > "$NQ_TEST_ROOT/examples/nauqtype.workspace.json";;
        original-generic-lock) printf '{}\n' > "$NQ_TEST_ROOT/examples/nauqtype.workspace.lock.json";;
        evidence-dir)
            rm -f -- "$NQ_TEST_ROOT/build/verification/seed-bootstrap-phases-v1.json"
            mkdir "$NQ_TEST_ROOT/build/verification/seed-bootstrap-phases-v1.json";;
    esac
}
case "${1:-}" in
    version) printf 'nauqc %s\n' "${NQ_TEST_VERSION:-fixture-version}";;
    emit-c)
        [[ $# == 4 && "$2" == selfhost/main.nq && "$3" == -o ]]
        printf 'emit:%s\n' "$4" >> "$NQ_TEST_LOG"
        if [[ "$4" == build/seed/stage2.c ]]; then probe_phase stage2_emit; fi
        cp -- "$2" "$4";;
    prove-seed)
        [[ $# == 3 ]]
        printf 'compare\n' >> "$NQ_TEST_LOG"
        if [[ "$3" == build/seed/stage2.c ]]; then probe_phase current_compare; else probe_phase historical_compare; fi
        cmp -s -- "$2" "$3";;
    run)
        [[ $# == 4 && "$2" == examples/generic_reuse.nq && "$3" == -o && "$4" == "$PWD/build/seed/generic-smoke" ]]
        [[ -f examples/generic_values.nq ]]
        printf 'generic-smoke\n' >> "$NQ_TEST_LOG"
        probe_phase generic_composition
        printf 'generic reuse: ready\n';;
    *) exit 2;;
esac
