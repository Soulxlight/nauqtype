# Active Python Responsibility And Migration Map

Status: M38 inventory baseline, recorded after the M37 v0.2 supervised alpha gate. This map covers active responsibilities, not historical comparison assets.

## Baseline

- Python stage0 compiler: 23 files under `compiler/`.
- Python test harness: 26 test suites and 240 test methods under `tests/`.
- Active shell and CI gates still invoke Python to build the first stage1 executable.
- M39 replaces observable claims with Nauqtype-owned fixtures. It does not port Python implementation-private test layout one-for-one.

## Compiler And Tooling Responsibilities

| Active Python responsibility | Current path | M39/M40 replacement evidence |
| --- | --- | --- |
| Lex, parse, resolve, typecheck, borrow, IR, and C emit seed | `compiler/` | C seed -> stage1 -> stage2 structural proof |
| First compiler CLI | `compiler/main.py` | `bootstrap/seed/` compiler built by host `cc` |
| Project loading and flat-root imports | `compiler/project/` | `nauqc test` project fixture group plus seed proof |
| Python test support and copied workspaces | `tests/test_support.py` | Stage1-owned fixture runner and deterministic temporary workspace helpers |
| Dependency bootstrap | `scripts/setup_deps.py` | Host C seed bootstrap; historical audit-only dependencies leave active setup |
| AI audit comparison generator | `scripts/run_ai_audit.py` | Historical comparison asset, not an active compiler gate |
| Milestone and Linux gate bootstrap | `scripts/check_milestone.sh`, `scripts/check_linux_alpha.sh` | Shell gates invoking `nauqc test`, `nauqc prove`, and seed bootstrap only |
| CI Python installation | `.github/workflows/linux-alpha.yml` | Host-C seed and Nauqtype-owned verification commands |

## Test Claim Migration

| Python suite | Cases | Observable claim to preserve | First Nauqtype-owned target |
| --- | ---: | --- | --- |
| `test_ai_audit.py` | 1 | Historical audit report shape | Archive with explicit historical rationale |
| `test_bootstrap.py` | 1 | Bootstrap prerequisites | M40 seed bootstrap smoke |
| `test_borrow.py` | 8 | Move and borrow diagnostics | Expected-diagnostic fixtures |
| `test_codegen.py` | 2 | C statement and runtime shape | Normalized C goldens |
| `test_contracts.py` | 10 | Audit contract diagnostics | Review/diagnostic fixtures |
| `test_diagnostics_json.py` | 4 | Diagnostics JSON schema and exits | Stage1 JSON golden fixture plus schema-shape driver check |
| `test_field_assignment.py` | 5 | Restricted field-write behavior | Run and expected-failure fixtures |
| `test_golden.py` | 8 | C and diagnostic snapshots | Existing golden fixture groups |
| `test_imports.py` | 6 | Import graph behavior | Multi-module fixture group |
| `test_integration.py` | 43 | End-to-end stage0/stage1 claims | Selfhost probe and run fixture groups |
| `test_lexer.py` | 3 | Lexical token behavior | Selfhost lexer probe fixtures |
| `test_parser.py` | 5 | Parser and audit-block shape | Selfhost parser probe fixtures |
| `test_patterns.py` | 5 | Refined pattern behavior | Run and expected-diagnostic fixtures |
| `test_resolution.py` | 2 | Name-resolution diagnostics | Expected-diagnostic fixtures |
| `test_review.py` | 2 | Review golden output | Review fixture group |
| `test_selfhost_borrow.py` | 9 | Handoff-driven borrow parity | Existing selfhost probe group |
| `test_selfhost_c_emit.py` | 12 | Stage1 C output and runtime | C emit and run fixture groups |
| `test_selfhost_differential.py` | 3 | Stage0/stage1 family parity | Seed/stage1 comparison fixture group |
| `test_selfhost_handoff.py` | 9 | Checked handoff structure | Existing selfhost probe group |
| `test_selfhost_ir.py` | 6 | IR structure and metadata | Existing selfhost probe group |
| `test_selfhost_proof.py` | 1 | Stage1-to-stage2 self-build | Existing `prove-selfhost` gate |
| `test_stage1_driver.py` | 82 | Active CLI, evidence, policy, and proof contract | CLI fixture and golden groups |
| `test_stage1_runtime.py` | 8 | File, list, and process runtime behavior | Runtime run fixture group |
| `test_teaching_corpus.py` | 1 | Corpus index completeness | Corpus manifest fixture group |
| `test_types.py` | 2 | Core type diagnostics | Expected-diagnostic fixtures |
| `test_verification_scripts.py` | 2 | Shell verification contract | Shell gate smoke plus documented archive rationale |

The suite counts total 240. `tests/fixtures/m39_fixture_manifest.txt` names every suite and carries either an owned gate or an explicit historical-reference rationale. `nauqc test` validates its version and all 26 suite mappings before executing active fixtures.

## M39 Fixture Requirements

The Nauqtype-owned runner must support deterministic case IDs and these assertions:

- source check success or failure
- exit code, stdout, and stderr
- text diagnostics and diagnostics JSON goldens, including expected nonzero exits
- facts, review, review-diff, change-report, policy-check, and refactor-plan goldens
- normalized structural-C comparison
- emitted-C compile/run behavior
- copied-workspace selfhost proof

It must consume a small explicit manifest and existing fixtures/goldens. It must not require a general JSON Schema engine or a second unrelated test framework.

## M40 Exit Criteria

Python can leave active build, test, proof, release, and CI commands only when all conditions hold:

1. A clean checkout builds a checked-in C seed with host `cc`.
2. The seed builds stage1, stage1 builds stage2, and the resulting C agrees under structural normalization.
3. `nauqc test` covers every active suite claim in this map or records an accepted historical-only rationale.
4. Linux release and CI execute the seed and Nauqtype-owned gates without Python or pip.
5. The archived Python reference records its final commit and capability scope.
