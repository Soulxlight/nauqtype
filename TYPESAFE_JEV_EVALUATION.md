# Jev: Harder Audit-Context Evaluation

## Scope And Cost Boundary

This is a local, exploratory workflow evaluation, not a compiler audit or a
replacement for independent reviewers. The user authorized real source uploads.
The scarce resource is Codex review effort, not Jev API spend.

One independent Sol xhigh agent authored the benchmark before receiving any
Jev output. It used bounded searches, not a whole-repository audit. The lead
ran the experiment using one-off operator tooling outside the active compiler.
No source semantics, runtime, schemas, audit requirements, or tests changed.
No compiler gates ran. No additional research/audit agents were spawned.

## Frozen Method

- Revision: `40cf99ba29c43bf497f4fd0bda9aaad519046baa`.
- Benchmark SHA-256:
  `22345fe8e4242435e800c1e8276333cfdeb0ac9d5246da403a4bc5a9af39d2ac`.
- 24 source excerpts across eight compiler/runtime/verification files;
  32,506 characters excluding each excerpt's terminal newline.
- Ten questions: eight answerable multi-file cases, two lacking the requested
  final audit/timing records. Twenty-three required excerpt labels in total.
- Expected sources and rationales were frozen before inference and withheld
  from Jev. They are independent model-authored labels, not human gold truth.
- Two ranking runs per question with shuffled order and reassigned opaque IDs.
  Filenames and line numbers were not sent as metadata; identifiers naturally
  present in source text were preserved.
- Baseline: BM25, k1=1.2, b=0.75, lowercase alphanumeric tokenization. Both
  methods see the same candidate texts. No prompt tuning after results.
- Each first-run top-two packet received a separate sufficiency question.
  Required-label coverage determines the preset expected sufficiency answer.
- Model pinned to `jev-1.13.0`; 30 requests, 30-second request timeout, no retries.

## Results

| Method | All required evidence at top 2 | All required evidence at top 4 | Required excerpts recovered at top 4 |
| --- | --- | --- | --- |
| BM25 | 2/8 | 3/8 | 14/23 |
| Jev, order A | 3/8 | 5/8 | 20/23 |
| Jev, order B | 3/8 | 6/8 | 21/23 |

First-run top-four omissions concern the distinction between legacy and new
process launch, borrow-checker encoding of consuming versus borrowed operations,
and seeding process cleanup authority into effect inference. These are exactly
the kinds of cross-layer details an audit must not silently discard.

Top-two membership changed on 3/10 questions between runs. Jev's separate
packet-sufficiency judgment matched the preset coverage labels in 7/10 cases:
one packet marked sufficient omitted a required excerpt (q05); two packets
marked insufficient contained the preset required excerpts (q06/q07). Both
questions lacking actual final-run records were marked insufficient.

These sufficiency counts use frozen labels and are not automatically model
correctness verdicts: a reviewer must assess whether required excerpts are
redundant or whether the question demands more than the label set establishes.

The independent benchmark author subsequently inspected the three disagreements.
For q05, the omitted excerpt was corroborating rather than essential: the two
selected excerpts already answer the question. This is an overstrict-label
disagreement, not a demonstrated unsafe completeness decision. For q06 and q07,
the packets do contain sufficient evidence; Jev's requests for more evidence
were substantive false escalations that could increase agent reading costs.
Frozen labels and headline counts remain unchanged to preserve the experiment.
This adjudication also limits the use of preset coverage as a completeness proxy.

## What The Cost Numbers Mean

Across ten separate review questions, all background totals 325,060 characters.
First-run top-four packets total 59,760: 81.6% less supplemental text. However,
those packets are incomplete in 3/8 answerable cases. This is not a safe 81.6%
reduction in audits, tokens billed, or Codex Pro usage. Mandatory diff, contracts,
tests, follow-up reads, and the reviewer's reasoning are outside that count.

An exploratory union of BM25 top four and Jev top four cost 84,468 characters
and still covered all required sources in only 5/8 cases. Simply combining
rankers did not repair missing context. This comparison was added after the
prespecified runs and must not be presented as a held-out optimization.

Jev reported 262,309 input tokens and 7,530 output tokens. At the user's stated
$0.04 per million input tokens, estimated spend is $0.01049, not a billing
receipt. Request times were 151-727 ms in this small serial run. These are
observations, not sustained latency or billing guarantees.

Actual Codex usage savings were not measured. Setup and the one label-authoring
agent consume Codex usage now; repeating this benchmark every milestone would
undermine the purpose. Reuse the frozen cases rather than repeatedly inventing
evaluation infrastructure.

## Workflow Verdict

**Promising for prioritizing optional reading; insufficient for deciding that
an audit packet is complete.**

The useful operating shape is:

1. Lead identifies the change's authority boundaries and provides mandatory
   diff, contracts, exact test results, known findings, and required cross-layer
   context. Deterministic freshness checks run locally, not through Jev.
2. Jev ranks supplemental excerpts for concrete questions. The auditor gets
   the short list and source index, with full material available on demand.
3. The independent auditor checks implementation and follows cross-layer
   dependencies. Neither a low rank nor a high confidence can suppress a
   required read, dismiss a finding, or waive a gate.
4. Repair reviews use the changed slice and affected evidence. Full-body
   orientation is not repeated by default; required broader release/authority
   reviews retain their existing scope.

Measure the next already-required audit's packet size and follow-up reads.
Do not commission a duplicate full-body audit merely to measure savings. If
preparation plus follow-up costs erase the benefit, keep ordinary local search.

Raw benchmark, source hashes/excerpts, requests, responses, protocol, rows,
summary, and exploratory calculation are in `build/typesafe-rigorous/`.
That directory is ignored, local experimental evidence, not a release artifact.
Credentials were kept outside the repository and request bodies.

The same independent agent reviewed the saved experiment and this report. It
verified the hash, counts, context arithmetic, and stated limitations; no second
full audit was commissioned. Local artifact JSON, credential non-persistence,
and `git diff --check` validation passed. Changes remain uncommitted.
