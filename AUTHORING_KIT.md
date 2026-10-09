# NauqType Model Authoring Kit

## Status And Purpose

Design accepted for staged evaluation on 2026-09-20; implementation and model
benchmarks are not complete. Adopt the useful direction from the reviewed Kimi
kit, not its prototype code or claims of measured savings.

The goal is fewer invalid or misleading generated programs and fewer repair
rounds for humans and agents. NauqType remains a deterministic compiler of
source and checked evidence, not a model-driven correctness system. This kit
cannot replace compiler checks, behavioral tests, human supervision, or the
independent audits required by [AGENTS.md](AGENTS.md).

The reviewed input is `Kimi_Agent_Nauqtype Repo Review(1).zip` from Kimi
Migration, with SHA-256
`402ead050624259059e82297b8643db6a0049e2017926308cdd234d3466e5c1d`.
It is external research, not a vendored dependency. No files from that archive
are adopted by this documentation checkpoint.

## What To Carry Forward

- A compact authoring guide grounded in [SPEC.md](SPEC.md),
  [GRAMMAR.md](GRAMMAR.md), and [SYNTAX_IDENTITY.md](SYNTAX_IDENTITY.md).
  Name its supported subset and compiler revision rather than claiming it is
  a complete language reference.
- Compiler-checked examples drawn from the
  [teaching corpus](TEACHING_CORPUS.md), including negative diagnostics and
  boundary behavior. Keep declared intent separate from checked facts.
- An optional constrained-generation grammar with a documented dialect and
  compiler disagreements. It filters candidate syntax; it is not the parser
  specification or an acceptance oracle for NauqType programs.
- A bounded comparison of unaided generation, guide-assisted generation, and
  guide-plus-grammar generation, using the same model and tasks.

The kit is separate from [Jev's advisory review-context work](TYPESAFE_JEV.md).
Authoring assistance proposes source; reviewer-context assistance prioritizes
supplemental background. Neither becomes compiler evidence or approval.

## Corrections Required Before A Pilot

The archive review identified these concrete acceptance blockers:

1. Replace the known-wrong integer-rendering teaching example. It returns only
   `-` for the minimum `i32` value. Use correct existing semantics and test the
   full boundary case, not just whether the example parses.
2. Make validation portable and fail closed. The prototype's hard-coded
   forward-slash disagreement paths miscount on Windows. Required manifests,
   prompt examples, probes, and grammar-port checks must not silently vanish
   when files are absent; missing or unreadable inputs and empty test
   inventories must fail.
3. Record grammar limitations honestly. The reference grammar rejects an
   unparenthesized `if flag {}` form because its expression alternative
   consumes the braces. A finite corpus pass cannot establish equivalence to
   the compiler. Do not narrow valid NauqType source to suit a decoder.
4. Lock the actual decoder. A dated `master` checkout is not an immutable
   llama.cpp revision; record the exact source commit, build configuration,
   binary digest, and ported-grammar digest. Test the decoder as well as the
   reference grammar. Its matcher must reject absent or unreadable files.
5. Publish one authoritative reference/ported grammar pair. The archive also
   contains the obsolete root draft; do not distribute conflicting grammars
   as equivalent current artifacts.
6. Isolate every generated executable, regardless of its declared effects.
   An audit clause is not a security boundary. A temporary directory alone is
   not an execution sandbox.

These are review findings, not fixes already made to the external kit. Local
reference-grammar probes were inspected; no end-to-end model benchmark or
fresh Linux compiler/release gate was completed for this review.

## Reproducible Evaluation Contract

Before a pilot, freeze a manifest identifying the compiler source and seed,
compiler executable, runtime, guide, grammar, decoder build, and task/input
corpus by revision and content digest. Record model/tokenizer identity and
sampling configuration; record seeds where supported without promising
deterministic hosted-model output. A repository HEAD alone is insufficient
when sources or binaries may differ.

Use equal task sets, output budgets, tool access, and repair limits across the
three arms. Lock the test oracle before generation. Include held-out tasks
and multiple inputs per task: success, negative diagnostics, failure paths,
and boundary values. Keep task-solving inputs distinct from held-out tests.
Retain every raw attempt, follow-up diagnostic, timeout, and failed run rather
than reporting only repaired successes.

Report separately:

- syntax acceptance and compiler acceptance;
- warnings and machine-checkable contract consistency;
- behavior against the locked input/output and failure expectations;
- first-attempt success and success after each allowed repair;
- input/output tokens, monetary cost, repair rounds, and end-to-end time per
  behavior-correct solution, including failed attempts in the totals;
- grammar false rejections, compiler rejections of grammar-accepted output,
  and decoder failures or added latency.

Empty diagnostics do not prove intent, purity, safety, or functional
correctness. A passing task matrix proves only the tested behavior. Do not
label model-written claims as `checked` evidence or modify existing evidence
schemas to accommodate them.

Run compilation and generated programs in an independently enforced isolated
environment without credentials, private workspace mounts, or network access
by default. Bound CPU, memory, wall time, process count, and output; verify
process-tree cleanup on cancellation. Explicitly authorize any task needing
additional access. Do not derive execution permissions from `effects()`.

Agree the data boundary, spending cap, and stop conditions before any paid
pilot. This design is not authorization to upload a repository or start model
calls. Predeclare promotion criteria and repeat runs sufficiently to expose
variance. Promote a component only if held-out evidence shows a practical
accuracy/cost improvement without weakening supervision. Keep guide-only use
available if grammar constraints hurt. No savings target is claimed yet.

## Roadmap Placement And Ownership

M56-M61 retain their existing order in [ROADMAP.md](ROADMAP.md). This work is
an optional authoring/tooling lane, not a new prerequisite for M56 generics.

1. Before implementation, assign the kit owner through
   [NAUQTYPE_COORDINATION.md](NAUQTYPE_COORDINATION.md) and lock a small
   compiler-versioned subset. Correct the guide and examples first.
2. Repair and validate the grammar/decoder inputs, including all blockers
   above. Clearly distinguish parse-only checks from compile/run evidence.
3. Run one separately authorized bounded pilot; publish positive and negative
   results and retain the baseline. No mandatory live-model call enters
   `prove`, CI, bootstrap, or every milestone review.
4. M59 is the integration home for a maintained authoring kit if that evidence
   supports it. A failed pilot does not block M59's core tooling work or M61's
   compiler release. Version the kit independently and state which compiler
   contracts it supports.

The compiler repository owns language/evidence contracts and canonical
examples. Tooling ownership must be assigned before implementation; ordinary
reusable modules remain NQType Libraries work. Active adopted orchestration
and teaching artifacts stay NauqType-owned. The supplied Python validators
remain external research tools, not additions to the active toolchain.

Compiler performance is a separate measured track, not an inferred benefit of
authoring assistance. Follow [PERFORMANCE_BUDGETS.md](PERFORMANCE_BUDGETS.md)
and [VERIFICATION.md](VERIFICATION.md): establish a fresh supported-Linux
baseline, prioritize profiled repeated lookups or redundant clone/drop work,
and preserve exact-candidate proof. Do not infer storage uniqueness from
source-level moves, promise a speedup from external profiling, or introduce
parallel scheduling, new borrow syntax, or split C translation units as part
of this authoring plan.
