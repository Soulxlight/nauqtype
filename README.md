# Nauqtype

Nauqtype is a small compiled language for AI-authored software under human
supervision. Its aim is explicit behavior, visible authority, deterministic
compiler evidence, and changes that people can review.

## Current Status

Nauqtype is an organizational Linux alpha, not a stable, feature-complete
language or a distro package. Milestones through M57.1 are complete; the
checkout roadmap holds their evidence. The definition of v1.0 is the
[language charter](LANGUAGE_CHARTER.md): a complete, coherent language that
follows its own principles, reached through milestones M58-M69.

The active compiler, tests, and proof runner are written in Nauqtype. A
checked-in C seed and narrow C runtime remain part of the intentional
bootstrap/runtime boundary. Python is archived reference code, not the active workflow. The
current alpha does not claim general semantic completeness or broad adoption.

## Linux Quick Start

The supported development workflow is Linux with Bash, a C11 compiler (GCC is
the documented toolchain), and the host tools used by the repository scripts,
including standard shell utilities. Start from a Nauqtype source checkout.
Building the stage1 compiler from its checked-in C seed requires these tools;
the copied alpha layout also uses the host C compiler for program builds.

From the checkout root, bootstrap stage1 and then use the repository launcher:

```bash
scripts/build_stage1_from_seed.sh
bin/nauqc check examples/hello.nq
bin/nauqc run examples/hello.nq
```

These are **source-checkout commands**. `bin/nauqc` uses the stage1 driver and
runtime from the checkout. The launcher normalizes source and output paths
from the caller's working directory, so relative paths continue to mean paths
relative to the directory from which you invoked it.

`CC` selects the C compiler used by the seed bootstrap script. It does not
select the compiler for generated programs: `build` and `run` invoke `cc`.
See [LINUX.md](LINUX.md) for the checkout workflow, optional symlink installer,
and copied-layout commands.

The optional installer creates a symlink to the checkout's `bin/nauqc`
launcher (by default under `$HOME/.local/bin`). It is not a standalone
installation: the checkout, runtime, and stage1 driver must remain available.

## Copied Linux Layout

To assemble and verify a copied alpha layout, run these **source-checkout
commands** from the repository root:

```bash
scripts/make_linux_release.sh
scripts/verify_linux_release.sh build/linux-release/nauqtype
```

The copied public launcher is
`build/linux-release/nauqtype/bin/nauqc`; its internal stage1 driver and
runtime live under `lib/nauqtype/`. Its examples and schemas are under
`share/nauqtype/`. The packaged documentation directory contains exactly
`README.md`, `LINUX.md`, `LINUX_RELEASE_MANIFEST.md`, and `M55_CONTRACTS.md`.
See the [copied-layout manifest](LINUX_RELEASE_MANIFEST.md) for its file
inventory and [M55 contracts](M55_CONTRACTS.md) for process/time boundaries.
The copied guide should be usable without checkout-only documentation.

From the copied layout's root, the launcher can check its packaged example:

```bash
bin/nauqc version
bin/nauqc check share/nauqtype/examples/hello.nq
```

For your own project, invoke that launcher's full path from the project
directory; source and output paths remain relative to your calling directory.

The assembler creates a development layout, not a distro package. System-wide
install ownership, package-manager metadata, shell completion, and a bundled C
compiler are outside the current packaging boundary. The verifier checks the
copied files and locked public help/version behavior; it does not by itself
validate every README link or prove a stable release.

## Language At A Glance

Source files use `.nq`. A file is a module. Projects may use a manifest-backed
workspace or legacy flat-root layout. The supported surface includes:

- `bool`, `i32`, `i64`, `f64`, `str`, and `unit`; unsuffixed integer literals
  default to `i32` unless an expected `i64` type selects `i64`. `f64` is IEEE
  754 binary64 with one literal form (`1.0`, `2.5e-3`) and six explicit
  conversion/text builtins (`f64_from_i64`, `f64_trunc_i64`, `str_from_f64`,
  `f64_from_str`, ...). Numbers never convert implicitly.
- Nominal `type` and `enum`, top-level `const`, functions with explicit
  parameter and return types, named function arguments, and explicit module
  imports, aliases, and qualified function/data names.
- `option<T>`, `result<T, E>`, `list<T>`, and move-only `bytes`, with the
  documented narrow constructors, list literals, and ownership rules. Lists
  are updated in place with `list_push`, `list_replace`, and `list_pop`;
  `i64_from_i32` and `i32_from_i64` convert integers explicitly.
- `if`, `while`, list-only `for`, nearest-loop `break`/`continue`, statement
  and value `match` (both exhaustive), narrow `let-else`, and supported
  integer/constructor patterns. Copy-only record update names its base
  explicitly; direct field assignment works on owned mutable product locals
  and through `mutref` parameters (`examples/in_place_update.nq`).
- Explicit `ref`, `mutref`, and owned `let mut` mutation; checked moves,
  borrows, and deterministic clone/move/drop behavior for owned values.
- Statement-boundary `?` for unchanged `result` errors, optional context
  labels, and the narrow annotated-local `try { expression }` boundary.
- Fixed `audit` clauses (`intent`, `mutates`, `effects`, optional
  `propagates`) and fixed `print`/`io` effect atoms.
- A compile-to-C backend, narrow runtime, explicit Linux I/O, and M55 process
  and time facilities with bounded, documented contracts.

This is a summary, not the language specification. Generic inference and
constraints, float types beyond `f64`, methods, implicit conversions,
user-defined effect taxonomies, and numerous other features remain deferred. Exact syntax and restrictions are specified in the
source checkout's `SPEC.md` and `GRAMMAR.md`; those files are not packaged.

## Workspaces And Dependencies

Manifest mode uses `nauqtype.workspace.json` to declare a workspace identity,
source root, entrypoints, and explicit module paths. A local dependency is
routed through declared manifest metadata and a lock that captures its source
identity. The compiler does not fetch dependencies: there is no registry,
version solver, package-script execution, ambient dependency search, or hidden
prelude. Projects without a manifest retain legacy flat-root module loading.

The lock/provenance formats and migration details are defined by checkout-only
`WORKSPACE_CONTRACT.md` and `WORKSPACE_LOCK.md`. A manifest or lock is not a
claim that an external dependency is published or stable.

## Compiler Evidence

The `nauqc` commands expose distinct, versioned evidence surfaces. Formats are
per-command; there is no single global "latest" format. Unless specified,
`facts` and `review` default to v1. `review-diff` defaults to v1 and accepts
v1/v2. `change-report` requires an explicit `--format` and accepts v1-v4.

```bash
# Source-checkout examples; run after building stage1.
bin/nauqc check examples/hello.nq --diagnostics json
bin/nauqc facts examples/hello.nq
bin/nauqc facts examples/hello.nq --format v4
bin/nauqc review examples/review_contracts.nq --format v4
bin/nauqc review-diff tests/fixtures/supervised_workflow/before/main.nq tests/fixtures/supervised_workflow/after/main.nq --format v2
bin/nauqc change-report tests/fixtures/supervised_workflow/before/main.nq tests/fixtures/supervised_workflow/after/main.nq --policy tests/fixtures/supervised_workflow/policy.json --format v3
```

`facts` exports checked definitions, references, and calls; newer versions add
semantic and captured workspace/dependency provenance. v1 is the legacy
default, v2 adds source-level evidence, v3 adds workspace evidence, v4
uses captured provenance, and v5 adds generic templates and instances.
`review` reports
declared contracts and compiler-inferred mutation, effect, and propagation
facts. Review v3 is a compatibility format whose direct-write mutation
coverage is explicitly partial and a lower bound. Review v4 adds checked,
call-aware parameter may-write evidence; that is not a reachability, purity, or
general safety guarantee. An unmodeled builtin can make coverage partial.
Review v5 keeps v4's meaning and adds generic templates and per-instance
facts.

`review-diff` compares checked semantic identities. `change-report` combines
change evidence and can include a policy sidecar; v3 makes advisory policy
state explicit, and v4 carries captured workspace/dependency provenance.
Policy status is advisory:
it does not approve, enforce, repair, or mutate code. `policy-check` validates
the named sidecar against checked facts. `refactor-rename` emits an edit plan
only; it does not apply edits. Formatting is output-only (`fmt --check` can
check canonical formatting); it does not rewrite source files.

Evidence commands still require source-contract validation. A successful
report is evidence only for its documented input, version, and analysis
scope; it does not replace tests, proofs, independent review, or release
gates. Older formats remain for compatibility and may carry weaker or
historical meanings. See checkout-only `AI_CONTRACTS.md`, versioned schemas,
and `VERIFICATION.md` for exact fields and boundaries.

## Verification Ladder

Use the smallest check that answers the current question. These are choices,
not commands to run in sequence, and require the **source checkout**:

| Question | Command |
| --- | --- |
| Does one program check? | `bin/nauqc check examples/hello.nq` or the affected fixture |
| Does one compiler fixture group pass? | `scripts/check_fast.sh --suite compiler-index` (or another fixed suite) |
| Does one host-unit group pass? | `scripts/check_fast.sh --host-suite provenance` (or `attestation`, `budget`) |
| Does the complete owned fixture/tooling tier pass? | `scripts/check_fast.sh` |
| Does a reviewed milestone candidate close? | `scripts/check_milestone.sh` |
| Is the independent Linux alpha release gate green? | `scripts/check_linux_alpha.sh` |

`check` validates a program through the checked compiler path; it does not
compile or run generated host C. Unqualified `test` runs the complete owned
fixtures; `test --suite <name>` is explicitly partial feedback. Compiler
routes in `check_fast.sh` validate/rebuild the compiler cache; host-only routes
do not claim a checked compiler. Unqualified `check_fast.sh` retains the full
owned, provenance, attestation, and budget coverage.
Local fast feedback defaults to checked fixture-C reuse; set
`NQ_TEST_REUSE_C=0` for fresh compilation. Reuse never skips probe execution,
and the complete milestone gate forces fresh fixture compilation.
`prove` runs the owned proof path. The composed milestone gate includes these
obligations without repeating the same build/proof for each phase. The
independent Linux alpha gate rebuilds from the seed,
exercises the launcher, assembles the copied layout, and smoke-tests it outside
the checkout. Select the relevant gate from context; these commands have
different scope and are not interchangeable.
Do not pre-run all expensive gates before the milestone gate. Release and
stable-surface checkpoints still require the independent gates specified in
the verification contract.

For a compiler/runtime/release milestone, follow checkout-only
`VERIFICATION.md` and `AGENTS.md`: focused checks first, independent review of
the frozen candidate when required, then the prescribed full native Linux
gate. A Windows source edit or static check does not establish Linux
execution, release readiness, stability, or performance.

## Current Work And Limits

The PRE-M56 checkpoint met focused10s, explicit opt-in warm60s, and at least
50% cold-gate reduction targets without weakening proof or resource ceilings.
The10-minute cold working target remains unmet; default and release gates stay
serial. Those measurements are not timing promises for later compiler changes.

The M56 foundation adds explicit function/product/enum generics, for example
`identity::<i32>(7)` and `Parcel<i32>`. Concrete instances keep existing type,
ownership, audit and backend checks. No inference, traits, methods, overloads,
stored references or implicit conversion accompanies this foundation.
M56.1 adds `facts --format v5` and `review --format v5`, which report generic
templates and checked instances by source identity (for example
`fn:app::get<str,i32>`). All other evidence formats (facts/review v1-v4,
diff, change, policy, rename) still reject generic graphs with
`NQ-GENERIC-008` rather than invent source evidence for generated names.
M56.2 adds scalar `f64` (`examples/f64_basics.nq`); `f32`, unsigned integers
and `char` are reserved names, and math functions and fixed-precision
rendering remain library work. Formatter-lite
remains output-only. Examples `generic_reuse.nq` and `generic_values.nq` teach
the explicit form. Collections/data, FFI, bounded tasks and stable Linux
packaging remain roadmap work, not current capabilities.
The optional authoring-kit work is staged and unvalidated, not integrated
tooling or canonical teaching content. No paid model service is required for
ordinary compiler development.

For contributors, start with checkout-only `AGENTS.md` and
`NAUQTYPE_COORDINATION.md`. The source-only `docs/README.md` is an index for
the repository checkout; it is not installed with this guide. Historical
milestone records are maintained in their owning checkout documents rather
than duplicated here.
