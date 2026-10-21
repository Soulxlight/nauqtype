# P2 C-Emission Membership Slice

Independent Gate A amendment to P1-P4, approved by both assigned auditors
before implementation. This is not acceptance or a language milestone.
No source syntax, runtime, CLI, schema, ownership, or flag changes.

## Measured Selection

The captured V10 C program, built with production flags plus diagnostic `-pg`,
emits the unchanged e9d3 reference source with byte-identical reference C.
Instrumented run400.57s/111152KiB is attribution only. Flat self samples:
block cleanup24.90s, child-ID collection23.12s, parameter-local lookup11.18s,
block statements10.57s, indexed child lookup7.61s, final cleanup2.45s and
prelude2.44s. These additive sampled self costs are about half the profile;
they are not predicted production savings. Retain raw profiles and hashes.

## Bounded Representation

Build one invocation-owned C-emission lookup context at `emit_c_program`
entry, consuming ONLY its exact IR collections. Compact sorted integer-key
rows/ranges reference original source positions for:

- locals by function, including callee parameters from every function;
- locals by function and owner block;
- expression-child links by parent expression;
- statements by block, with precisely the old block-ID predicate.

Original source index is the tie-breaker. Keep child collection order, first
matching child-index/parameter semantics, duplicate/sparse/negative IDs, and
missing behavior. Do not assume dense IDs. Rebuild for filtered collections;
never reuse a context with another collection or fall back to flat facts.
No general persistent indexing service or richer C AST is introduced.

Thread the borrowed context only through affected private helpers. Preserve
the public emitter signature and every output order and failure guard.
Function/parameter queries must retain access to ALL callee metadata, not
just the current caller's locals. Cleanup visits exactly the old selected
locals in REVERSE original order; parent traversal, loop exit targets, owned
value predicates, and emitted drop operations remain unchanged.

## Ownership And Proof

After both independent approvals, one Sol High worker may edit only
`selfhost/c_emit.nq`, new IR-only `selfhost/c_emit_index.nq`, and a narrow
`selfhost/c_emit_index_probe.nq`. The lead owns proof registration, integration,
measurements, seed, audits and Git. No descendants, commits or pushes.

Keep independent linear selection oracles and compare full ordered records,
IDs and produced cleanup lines, not merely position counts. Cover empty,
interleaved, duplicate, sparse, negative and missing keys; filtered collections;
all-callee parameter lookup; copy isolation; reverse nested scope/match/loop
cleanup and its exit targets; missing required child data remains a failure.
Keep the 82-command compatibility matrix, selected C byte comparisons and
whole reference selfhost C comparison. No golden or diagnostic weakening.

Use focused probes before a final ordinary same-input emitter measurement.
Do not mix `-pg` time with production timing. Propagate the exact resulting
compiler through the seed, obtain mixed trailing audits and run the unchanged
seven-phase close once on the reviewed candidate. Original performance goals
remain open, including60s warm fixtures unless the owner explicitly revises it.
