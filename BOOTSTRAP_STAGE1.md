# Nauqtype Stage1 Bootstrap

## Active Status

The active Linux compiler, test runner, and proof runner are Nauqtype-owned.
Python stage0 and its tests are archived references, not an active bootstrap
or correctness fallback. Build from the checked C seed with
`scripts/build_stage1_from_seed.sh`; use `bin/nauqc` for daily commands.

The operational pipeline is parse/resolve/typecheck -> checked handoff ->
value plan/borrow -> IR -> C emission. It supports manifest-governed nested
workspace modules and locked local dependencies as well as legacy flat-root
sources. [ARCHITECTURE.md](ARCHITECTURE.md) maps the actual files and remaining
shared-truth gaps.

Self-build consistency is proven for the copied in-repo selfhost target. It
does not prove general semantic correctness: the Astra audit found
expression grouping, match priority, C naming, evidence, numeric, and
provenance gaps. [AUDIT_REMEDIATION.md](AUDIT_REMEDIATION.md) tracks corrective
closure before further language/runtime growth.

## Standing Proof Contract

The owned `selfhost/proof.nq` runner preserves this target:

1. Copy the in-repo selfhost workspace.
2. Run the active stage1 compiler there and capture emitted `build/main.c`.
3. Compile it with host C and the matching runtime into stage2.
4. Run stage2 in the same copied workspace, retaining the first C artifact
   before `write_file` overwrites the output.
5. Compare emitted C under the existing structural normalization and require
   matching success behavior, including `stage1 front-end ok\n` and no
   limitation/C-error diagnostics.

Normalization may remove insignificant whitespace and incidental binding/temp
numbers, not operators, source-derived names, types, or control flow. The
runner also locks expected behavior for the example/regression corpus and
supervision outputs. Spec-derived negative and runtime cases complement the
fixed point; they must not be generated from a potentially defective compiler.

The active seed chain is host C -> checked C seed -> stage1 C/executable ->
stage2 C. Seed promotion requires recorded lineage, hashes, independent audit,
fixed-point comparison, and clean-source reproduction under
[BOOTSTRAP_RETIREMENT.md](BOOTSTRAP_RETIREMENT.md). Runtime-native ABI names
must stay aligned with the matching seed runtime.

Current commands and resource limits are in [VERIFICATION.md](VERIFICATION.md).
The supported copied Linux layout is in
[LINUX_RELEASE_MANIFEST.md](LINUX_RELEASE_MANIFEST.md). Historical Windows/Zig
and Python-harness instructions are not active build requirements.

## Preserved Architecture Decision

The flat fact pipeline remains the current semantic front end. Its retention
is not permission to build ownership or backend passes directly on flat
facts. The structured checked handoff supplies binding identity, recursive
types, resolved targets, expressions, patterns, and control-flow structure.
Borrow analysis consumes it and the value plan; IR lowering consumes checked
data; C emission consumes IR only.

See [SELFHOST_HANDOFF.md](SELFHOST_HANDOFF.md). Incremental migration of
span-reconstructed expressions toward parser-owned structures is a later
reviewed project, not a prerequisite rewrite for the immediate audit repairs.

## Historical Bootstrap Unlocks

The first selfhost front end was enabled in this order: acyclic flat-root
imports, `read_file` returning `result<str, io_err>`, then builtin
`list<T>` and minimal string helpers. The first differential comparison used
Python stage0 as reference by accept/reject family, not exact diagnostic text.

Later milestones added the checked handoff, borrow checking, IR, C emission,
copied self-build proof, and the Nauqtype-owned driver/test/proof workflow.
M40 retired Python from required build, test, proof, release, and CI paths.
Those completed steps explain the current architecture; they are not pending
work or permission to resume Python feature development.
