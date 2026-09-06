# M54.10: Captured Source And Verification Provenance

Status: complete, 2026-09-06 UTC. Independent mixed-model audits and the
attested frozen gate passed. Close F07/F09/F10/F12 only; no M55/F14, source syntax, runtime
builtins, generic JSON library, stage3/stage4 chain, or cross-repository edits.

## Dependency Capture And Explicit Migration

Introduce `workspace-lock/v2`. Each dependency retains alias, workspace, path,
manifest_sha256 and includes validated legacy_source_sha256,
source_tree_format (`nauqtype-source-tree/v2`), and source_tree_sha256.
The authoritative source identity is SHA-256 over exactly:

```text
nauqtype-source-tree/v2\n
files:<decimal count>\n
path-bytes:<decimal byte length>\n<relative path bytes>\n
content-bytes:<decimal byte length>\n<captured content bytes>\n
```

Repeat the last two records for every regular `.nq` in unsigned-byte path
order, including empty files. Paths are slash-relative with no dot traversal,
backslashes, control bytes, or non-ASCII bytes in this bounded lock format.
Reject symlink roots/ancestors/files/directories, special files, duplicate
paths, failed metadata/enumeration/read/hash operations, malformed or extra
lock entries, and duplicate JSON keys. Do not follow, skip, or reinterpret.
Source content remains raw bytes. The legacy hash is computed from the same
captured sorted contents, never by reopening paths.

One command-local capture owns exact root/dependency manifest and lock bytes,
validated dependency records, module identities, original diagnostic paths,
and dependency source text. Dependency parsing, routing, and evidence consume that
capture, never a subsequent original-path read. The root project still uses
existing source loading; its manifest/identity metadata is captured. This is
not a parser or checked-handoff rewrite. Captured-source tests mutate the
original only after capture and prove parsing sees the verified text.

Reject legacy v1 dependency locks with a migration diagnostic; no silent
upgrade or weak fallback. Keep prior schemas and successful output shapes
unchanged. Facts v3 emits the validated legacy value as its existing
source_sha256, explicitly documented as a compatibility field. Add facts v4
with lock/version/framed digest fields. Add change-report v4 for explicit
framed dependency provenance under `before.dependencies` and
`after.dependencies`, each sorted by alias then workspace then path.
Old change-report v1-v3 comparison behavior
stays on `(path, manifest_sha256, validated legacy_source_sha256)`; those
formats are compatibility-only, not secure change attestations. v4 compares
`(path, manifest_sha256, source_tree_format, source_tree_sha256)` and excludes
the legacy checksum from its decision. Review-diff needs no new shape.
Facts v4 and change-report v4 dependency records have exactly: alias,
workspace, path, lock_version, manifest_sha256, legacy_source_sha256,
source_tree_format, source_tree_sha256. Migrate owned fixture locks only;
notify external consumers through coordination rather than editing their repos.

## Seed v2

Use a flat canonical `nauqtype-c-seed/v2` JSON object with unique bounded scalar
fields. Shell verification reconstructs its exact canonical bytes and rejects
missing, duplicate, unknown, malformed, or incoherent fields without Python/jq.
Check in the exact generating `selfhost/` sources under
`bootstrap/seed/source-snapshot/selfhost/` plus a sorted path/mode/hash inventory.
This verbatim archive disables Git text conversion and whitespace complaints
for snapshot paths only; inherited blank/trailing whitespace is retained, not
rewritten after generation. Active source whitespace rules stay unchanged.
An exact checksum set binds manifest, inventory, snapshot, seed C, and pinned
runtime C/H. Manifest identities bind predecessor seed, generator executable,
input/output C, observed generation record, source inventory/tree, generating
base revision/index/dirty state, and generating CC identity/target/flags.
These are reproducible provenance claims, not signatures or proof against a
malicious user rewriting all trust roots.

Bootstrap always validates lineage/inventory/artifacts before compilation.
The seed proof checks the recorded historical snapshot as well as current
source seed-to-stage1-to-stage2 normalized C. When historical and current
snapshot inputs are identical, reuse the exact same emission/comparison with
an explicit digest equality guard rather than repeat expensive work. Otherwise
run the historical comparison separately. No extra compiler generation chain.

## Immutable Builds And Gate Evidence

The builder captures all declared input paths/modes/content into a private
snapshot, checks it against a pre-capture inventory, builds only captured
inputs, and checks original inputs/toolchain still match before publication.
Historical seed C links its pinned runtime; current source links current
stdlib runtime. Remove the standalone cache `record` command. Only successful
builder derivation and identity smoke can publish stage1-cache/v2. Bind source
inventory, seed executable, emitted C, driver, resolved CC bytes/version/target,
and exact flags. Publish C/driver/receipt then cache manifest last. This is
staleness/derivation discipline, not tamper-proof storage under a hostile owner.

Add a strict versioned milestone attestation separate from timing summaries.
Bind candidate index/worktree/untracked identity before/after, seed, driver/C,
cache derivation, wrapper, both bootstrap CC and proof cc identities/targets/
flags, proof summary, release manifest/tree. A verifier rejects transplanted
or modified evidence. Unborn snapshots record null base revision, real index
tree, and explicit worktree/index equality. Nonpackaged completion-only docs
may add a disclosed closing delta; they cannot silently replace tested code.

Proof-summary v3 uses algorithm/value SHA-256 objects and explicit null for
unreached artifacts from this invocation. Do not inherit stale files. Preserve
all direct normalized C equality decisions and old schemas. No nqsum value is
an attestation; if retained it is named as triage only.

## Required Evidence

- Lock rename/empty file/resegmentation differences; positive dependency build
  and legacy facts golden; v1/malformed/extra/symlink/special/unreadable failures.
- Captured text is the text parsed after original-path mutation.
- Seed/manifest/checksums/runtime/snapshot/inventory/generator tampering rejects.
- Persistent source/toolchain mutation during build leaves no blessed cache;
  restored source mutation may publish because compilation used captured
  bytes. Transient toolchain substitution is outside the trusted-host model.
  Arbitrary preexisting binaries cannot be recorded independently.
- Wrong tree/seed/driver/CC/target/flags/proof/release evidence rejects; unborn
  case is honest; failed/skipped proof phases cannot use stale artifacts.
- Focused owned NQ/native shell provenance gate, independent Sol xhigh plus
  GPT-5.5 xhigh trailing PASS, then one frozen milestone gate and attestation
  verification. No duplicated equivalent heavy gates.

## Exact Encodings And Comparison Edges

All framing newlines are LF byte 0x0a. Decimal lengths/counts have no leading
zeroes except `0`. Dependency paths are relative to the captured dependency's
declared source root. All SHA-256 values are 64 lowercase hex; Git object
identities are 40 lowercase hex in this repository. Unknown fields reject.

Seed JSON is `{` LF, each fixed-order field as two spaces, quoted key, colon
space, scalar, comma except on the last field, LF, then `}` LF. No alternative
whitespace, escaping, CR, duplicate or reordered field is accepted. Strings
are fixed literals, safe relative paths, lowercase hex, or ASCII target atoms
`[A-Za-z0-9_.-]+`; booleans are true/false, absent base revision is null.
The ordered fields are:

```text
version = "nauqtype-c-seed/v2"
source_entry = "selfhost/main.nq"
source_tree_format = "nauqtype-selfhost-source/v1"
source_tree_sha256
source_inventory_sha256
source_base_revision = hex40|null
source_index_tree = hex40
source_dirty = bool
predecessor_seed_c_sha256
generator_exe_sha256
generator_input_c_sha256
generator_output_c_sha256
compiler_c_sha256
runtime_c_sha256
runtime_h_sha256
generator_cc_sha256
generator_cc_version_sha256
generator_cc_target
generator_flags_sha256
```

`source_index_tree` is the selfhost-only index tree captured before seed
promotion, not a circular hash of the manifest containing itself. Generator
input C equals output C and compiler C at the accepted fixed point; the
observed generator binary/CC values are historical records, not executable
authenticity claims on a different host. Enforced reproducibility comes from
the captured source-to-seed C comparison. Generator flags are the NUL-framed
relative arguments `-std=c11`, `-O2`, `-D_POSIX_C_SOURCE=200809L`, `-Istdlib`,
the generating C relative path, `stdlib/runtime.c`, `-o`, and the executable
relative path, recorded in a checksum-bound `generator-flags.txt` inventory.

The source inventory is `seed-source-inventory/v1` LF, `files:<N>` LF, then
each record `path-bytes:<P>` LF, raw safe `selfhost/...nq` path LF,
`mode:<100644|100755>` LF, `sha256:<hex64>` LF in byte-sorted path order.
Its file set must exactly equal the snapshot's regular `.nq` set; no symlink,
special, extra non-source file, missing or duplicate/reordered record.
`SHA256SUMS` has exactly compiler C, runtime C/H, manifest, generator-flags,
inventory, and every snapshot source, in sorted relative path order. It does
not hash itself. A verifier reconstructs the allowlist and checks contents.

Historical proof edge is `emit(snapshot) ~= checked-in seed C`; current proof
edge is `stage1 C ~= stage2 C`, both using the unchanged normalizer. Reuse is
permitted only for equal source format/digest, entry, source-loading metadata,
seed-emitter executable identity, and exact emit arguments; current stdlib
runtime is a compilation input, not a seed-emission input. The one stage1
emission must pass BOTH comparisons. Record the
reuse boolean and compared digests. Unequal snapshots require a separate
historical emission. Focused tests cover both branches with emission counts.

Cache manifest `stage1-cache/v2` is a fixed-order LF key=value text document:
`inputs_sha256`, `derivation_sha256`, `stage1_c_sha256`, `stage1_exe_sha256`.
The receipt path is `build/seed/stage1-derivation-v1.txt`; its first line is
`stage1-derivation/v1` followed by these fixed-order key=value fields:
`inputs_sha256`, `seed_manifest_sha256`, `seed_exe_sha256`, `stage1_c_sha256`,
`stage1_exe_sha256`, `cc_path`, `cc_sha256`, `cc_version_sha256`, `cc_target`,
`flags_sha256`. Paths must be absolute printable ASCII without LF/CR or `=`;
targets use the safe atom grammar. Flags use exact NUL-framed relative args.
The input inventory includes VERSION, every current selfhost `.nq`, both
current runtime files, every seed material file, and scripts invoked by the
builder/cache/bootstrap verifier, with modes and hashes. Recompute that exact
set; cache checks never merely trust stored expected hashes. Only the builder
writes the receipt and publishes C/exe/receipt/manifest in that order.

Attestation path is `build/verification/milestone-attestation-v1.json`.
Its canonical fixed-order object fields are version (`milestone-attestation/v1`),
command (`check-milestone`), status, head_state (`commit|unborn`), base_revision
(hex40|null), index_tree_before, index_tree_after, candidate_sha256_before,
candidate_sha256_after, untracked_sha256, worktree_matches_index (true),
seed_manifest_sha256, seed_c_sha256, seed_runtime_c_sha256,
seed_runtime_h_sha256, driver_sha256, stage1_c_sha256, cache_receipt_sha256,
wrapper_sha256, bootstrap_cc_path, bootstrap_cc_sha256,
bootstrap_cc_version_sha256, bootstrap_cc_target, bootstrap_flags_sha256,
proof_cc_path, proof_cc_sha256, proof_cc_version_sha256, proof_cc_target,
proof_flags_sha256, proof_summary_sha256, release_manifest_sha256,
release_tree_sha256. Candidate digest covers byte-sorted tracked and nonignored
untracked paths/modes/content; ignored build artifacts are excluded there and
bound separately by the artifact fields. The verifier recomputes each source,
toolchain and artifact identity, strict-parses the record, and rejects mismatch.
Persistent before/after source/toolchain drift rejects publication. Transient
source mutate-and-restore is safe because compilation uses captured bytes;
transient host-toolchain substitution is outside this trusted-host model, not
a promised detection feature. Tests distinguish persistent/restored changes.

Proof v3 artifact is null or exactly
`{"path":"...","hash":{"algorithm":"sha256","value":"<hex64>"}}`.
The producer tracks produced artifacts in command-local memory. Skipped or
unreached artifacts are null even if old files exist. `structural_c_equal` is
null if unperformed, false for performed mismatch, true only for direct
normalized equality. Failed-invocation artifacts may appear only if produced
in that invocation. Schema/goldens and stale-artifact tests lock these states.

All remaining file-set digests use SHA-256 of the following stream, with
unsigned-byte-sorted relative paths and exact raw file bytes:
domain LF, `files:<N>` LF, then for each file `path-bytes:<P>` LF, path LF,
`mode:<100644|100755>` LF, `content-bytes:<C>` LF, content LF. Executable-bit
presence selects 100755; otherwise regular files use 100644. Symlinks and
special files reject. Domains are `nauqtype-build-inputs/v2` for inputs,
`nauqtype-candidate/v1` for tracked plus nonignored untracked files,
`nauqtype-untracked/v1` for that untracked subset, and
`nauqtype-release-tree/v1` for every release-layout file. Empty sets include
`files:0` LF. Cache derivation_sha256 hashes the exact receipt bytes.

CC identity resolves the executable's absolute physical path, hashes its raw
bytes and exact successful `--version` stdout, and records successful
`-dumpmachine` stdout with only its terminating LF removed. Reject invalid
target atoms. Attested gates require `cc` to resolve and identify successfully,
so the ordinary driver's fallback cannot make proof_cc describe another
compiler. Bootstrap CC and proof cc remain independently recorded.

Supplemental closing evidence is outside the commit to avoid self-reference:
`build/verification/milestone-close-v1.json` has exactly version
(`milestone-close/v1`), attestation_sha256, final_commit, final_tree,
candidate_tree, documentation_delta_sha256, and status (`ok`). Its delta file
`milestone-close-delta-v1.txt` contains its matching header LF and sorted
`path-bytes:<P>` LF/path LF/`before:<sha256>` LF/`after:<sha256>` LF records.
Verify the final Git tree differs from the attested candidate tree ONLY in
M54_10_CONTRACTS.md, AUDIT_REMEDIATION.md, ROADMAP.md, TODO.md, or
NAUQTYPE_COORDINATION.md, and recompute both versions' bytes and the delta
digest. No README, source, schema, fixture, runtime, script, or packaged file
is allowed in that delta. The close verifier rejects any other change; the
tracked completion document cites the tested candidate and attestation hash,
not its own future commit hash. This supplemental close is not a replacement
for the strict attestation verifier on the original frozen candidate.

`bootstrap_flags_sha256` hashes NUL-framed domain
`nauqtype-bootstrap-flags/v1`, label `seed`, then the complete argument vector
`-std=c11`, `-O2`, `-D_POSIX_C_SOURCE=200809L`, `-Ibootstrap/seed`,
`bootstrap/seed/nauqc-seed.c`, `bootstrap/seed/runtime.c`, `-o`,
`build/seed/nauqc-seed`; then label `stage1`, then the complete vector
`-std=c11`, `-O2`, `-D_POSIX_C_SOURCE=200809L`, `-Istdlib`,
`build/seed/stage1.c`, `stdlib/runtime.c`, `-o`, `selfhost/build/nauqc`.
Each listed string, including the final one, is NUL-terminated. The private
captured build uses those stable relative roles; custom output only changes
publication, not compiler arguments. `proof_flags_sha256` records the fixed
host_c compiler-option vector only, excluding input/output artifact paths:
NUL-framed domain `nauqtype-proof-options/v1`, then `-std=c11`, `-O2`,
`-D_POSIX_C_SOURCE=200809L`, `-Istdlib`, each NUL-terminated. Focused route
tests assert that exact option vector against host_c.
This is option-policy identity, not a claim to log every proof compile argv.

Closing deltas permit modifications only: every allowlisted document must
exist in the attested candidate and final commit. Additions, deletions, mode
changes, and renames reject. `candidate_tree` must equal the original
attestation's `index_tree_after`. Both before/after digests therefore always
refer to existing regular files and are never null.

## Focused Candidate Evidence

The isolated candidate is `/tmp/nauqtype-m54-10-provenance-ZDhJCQ`.
Its owned compiler emission passed in 465.29 seconds (100,784 KiB peak RSS)
and current-runtime C11/O2 compilation passed in 31.85 seconds (428,152 KiB).
The resulting `build/m54_10/candidate test` passed in 25.35 seconds
(98,876 KiB), with exact `nauqtype test ok` stdout and empty compiler stderr.
`build/m54_10/candidate prove-corpus` passed all 42 cases in 27.74 seconds
(52,624 KiB), with exact `example corpus ok` stdout and empty compiler stderr.

Owned tests cover strict captured workspace inputs, malformed/duplicate/raw
byte cases, same-byte file renames and framing changes, continued parsing from
the captured text after original-file mutation, legacy and new evidence
goldens, and proof artifact null/mismatch states. New helper/test modules pass
`fmt --check`. Direct facts/change v4 outputs match their checked-in goldens.
The first bridge test exposed a stale assertion that rejected v4 as an unknown
format; the assertion now rejects v5. The final candidate reran that test.

`scripts/check_m54_10_provenance.sh` passed 81 assertions and
`scripts/check_m54_10_attestation.sh` passed 151, both with empty stderr.
These focused shell tests deliberately use explicit compiler/seed/cache stubs
around real hashing and attestation logic. They are not evidence for a real
compiler derivation or a full release gate.

The final candidate regenerated itself in 398.79 seconds (100,228 KiB).
`cmp build/m54_10/candidate.c build/m54_10/fixedpoint.c` passed exactly, and
`build/m54_10/candidate prove-seed` on those two paths passed with exact
`seed structural proof ok` stdout and empty stderr. Both C files and the
promoted seed have SHA-256
`49b486b2051a3dd63044a9993188e14c84f3ac8eb4d8d22153ea8a6d8ed99312`.
The generating executable has SHA-256
`183f181b902e16368dd9d4c3f1e4084488c1b5f3f7d6a3ecc25f7c6935a29d10`.

The seed v2 records the actual unborn source-preparation state rather than
inventing a source commit. Its source-only index tree is
`80eb516a28b1bef9c6360baa6bc283ac14573a79`, source SHA-256 is
`fa44769cdccdaf50159affdc47e863250a93021e2116e73ab5cfc07f9b34356a`,
and source-inventory SHA-256 is
`cbfff740f1e4f440a9e5f50b2dbeefa45d2c229da8743834dd5598bd8d683f9f`.
Strict `seed_verify` passes. Manifest SHA-256 is
`1b8a7ad5c993a00de76ddc3ec068f16fdb349d3a987b9ba0d94c10b9d5592233`;
the checksum-list file SHA-256 is
`895cdb2fc9ea4e028c27e6689e10bb3db5ce161d1cb465db70f8dd91cd4dbe64`.
The source snapshot preserves exact historical bytes, including whitespace.

Independent Sol xhigh and GPT-5.5 xhigh reviews found no remaining source or
seed defect. Sol required a pre-gate documentation repair for stale active
proof-v2 wording in README/performance guidance; that wording now names v3
and distinguishes historical schemas. Final documentation rebind and the
single attested real-compiler milestone gate were still required at that
focused checkpoint; the final results below supersede that pending state.

## Final Acceptance And Commit Binding

Sol xhigh and GPT-5.5 xhigh independently returned PASS on the repaired
documentation rebind and exact final source/seed candidate. The reviewed
binary-capable diff from M54.9 commit
`ace98f8c16c02f14b06b6ddfdcd8541da41e474e` has SHA-256
`03cbe61b2f58649b10fa84b3196691440adc2d777b416cef651a0835ab28fc49`.
Its index tree is `6d548d35de4c5f4fd64ffd3a84f6fc32e09e9a31`.

The first gate attempt's supervising process exited 143 during the proof
phase without publishing a final summary. Its cause was not established;
there was no recorded compiler stderr. The verified orphan proof processes
were stopped, partial logs retained, and that attempt does not count as
acceptance. No tracked file changed. A detached launcher then reran the same
`scripts/check_milestone.sh` with the same phase limits.

The completed run in `/tmp/nauqtype-m54-10-provenance-ZDhJCQ` passed in
2,716 seconds, from `2026-09-06T00:10:19Z` to `2026-09-06T00:55:35Z`.
Exit was 0, stderr empty, and all seven phases plus strict final attestation
verification passed. The final gate is slower than M54.9; this is correctness
and provenance closure, not a performance-improvement claim.

| Phase | Wall Seconds | Peak RSS KiB | Result |
| --- | ---: | ---: | --- |
| stage1.driver | 488.30 | 428364 | PASS |
| seed_bootstrap | 756.04 | 99292 | PASS |
| proof | 1255.21 | 428132 | PASS |
| linux_alpha | 15.30 | 52364 | PASS |
| stress_leg | 2.07 | 52040 | PASS |
| owned_tests | 162.63 | 98488 | PASS |
| ownership_sanitizers | 5.20 | 47308 | PASS |

The real seed report records `historical_reused=true` because historical and
current source snapshots match exactly; both required comparisons still
passed. Seed/historical/stage1/stage2 C all hash to `49b486b2...ed99312`.
The 12-phase proof summary v3 reports success and checked structural equality,
all 42 corpus cases pass, and the copied Linux release/stress leg passes.
Owned tests include the 81 provenance and 151 attestation assertions; all
nine ownership sanitizer cases pass. No Python gate or extra proof generation
is introduced, and no Windows/32-bit or stable-release claim is made.

The real attestation records the actual unborn isolated Git state, identical
before/after candidate tree and SHA-256, raw worktree/index equality, no
nonignored untracked inputs, both compiler identities/flags, cache derivation,
proof summary, and release tree. Canonical integration reproduced the exact
tested index tree before the five-document completion-only delta. The frozen
candidate remains unchanged for `scripts/milestone_attestation.sh verify`.
The final commit is additionally bound by `close <full-commit-id>` and
`verify-close`; their ignored supplemental records avoid self-reference.

Exact SHA-256 evidence is retained under ignored `build/m54_10_final/`, with
partial-attempt logs in `interrupted-run/` and gate records in `verification/`:

- milestone summary: `1a4b3322a09d5efc86f2a9d2b634881764d4dc949184e3a1542fb741ef9e67c9`
- performance summary: `c415558b8d564f4ca82e0535455fc0ac6ed6e17f3a857ca369672b9144ad9592`
- attestation: `d4e0974af0260fc1c112fa4b47411f8243f94c2d63f8f9a950b2502e8bef16c6`
- proof summary: `452bb4ba164ea3303e0cbe8006742a2cd8ae7ac9531fa3ee7997b7b1b63556df`
- derivation receipt: `37e11da54c87a7f173de0f62a42192ecdda7332f83f86279bdb5dc67d66f3986`
- seed comparison report: `4e230e2b00f7100d6aef08fd71e0c090a50a7afa3f552c3e78034362d355cb61`
- stage1 executable: `2b8d8b5d5feb751618c9763f5c1f60d60cb2cbb0301fc634458cb8df8d2c3fc7`
- release manifest: `a0964c1a47d1c6612d2e7741f9a78ab0ecb439c7d29d0a38bf153af7a7b19af8`
- framed release tree: `95b455f09213e73de96e63973af73381f51408f377fe7b1884b886d6e8009436`

External Libraries/AIML locks were not rewritten. Their owners must explicitly
migrate to workspace-lock v2 and re-evidence compatibility before upgrading.
F14 process interruption correctness remains the first M55 prerequisite;
M54.10 does not widen process/runtime authority or complete that repair.
