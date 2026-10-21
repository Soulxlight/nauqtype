# P1 Private Fixture Literal Scan Amendment

Independently approved at Gate A, 2026-10-19. Implementation/final evidence
remain subject to trailing review and fresh candidate verification. This is a
bounded continuation of [P1-P4](P1_P4_CONTRACT.md), not language development.
The complete warm goal remains <=60s; no waiver or test-coverage reduction.

## Measured Reason

The corrected same-session warm allocation suite took35.06s, with unchanged
fixture receipt bytes and inode/mtime records on the immediate repeat. The
separate `warm-profile-v1` diagnostic cache-oracle component recorded91,052,509
`starts_with_at` calls,227,558,727 `char_at` calls and roughly1.124 billion
string retains/drops. Literal/source modeling dominates sampled application
CPU. Instrumented49.77s wall time and3.05 sampled CPU seconds are attribution,
not production timing or a prediction of savings. The component image is
smaller than the real compiler, and helper waits are separately significant.

## Exact Slice

Change only private `fixture_c_contains` and `fixture_c_count` plus bounded
direct oracle checks in `selfhost/fixture_c.nq`:

- cache immutable string lengths and the first pattern byte;
- reject a longer pattern before scanning;
- test the first byte before calling `starts_with_at` at a candidate offset;
- keep byte-oriented exact substring matching, overlapping count behavior,
  empty-pattern results, and checked integer behavior;
- keep eligibility/splicing/directive algorithms and their callers unchanged.

This is computation on captured strings only. It does not alter file capture,
hash frames, raw environment binding, running-image identity, CC identity,
receipt domains, locks, publication, fresh-compile fallback, process polling,
or the order of cache decisions. No new public helper, runtime primitive,
command, output format, language syntax, scheduler, or result cache.

Retain the original linear loops as private independent test oracles. Compare
both predicates on empty strings/patterns, longer patterns, overlapping and
repeated prefixes, exact/start/end/absent matches, directive markers, CR/LF,
and NUL bytes supplied by the existing probe. Exercise current runtime source
text as well as bounded adversarial strings. Keep every existing pure/cache,
completion-fault, PCH/shadow, producer-replacement and refusal assertion.

## Ownership And Evidence

The Sol High fixture worker owns only `selfhost/fixture_c.nq` after both
independent Gate A reviews clear this amendment. The lead owns integration,
registration if needed, measurements, seed promotion, docs and Git. Auditors
stay read-only. Existing probes should invoke the new oracle checks, without
adding a separate full-oracle run to the default suite.

Before/after ordinary component-oracle timing must use the same inputs,
environment, compiler flags and host, and record artifact identities. The
diagnostic profile is not that comparison. Do not run simultaneous heavy
native jobs. Report measured gains or lack of gain rather than extrapolating.
The complete warm tier must be timed again on a valid current compiler; this
slice alone is not expected or claimed to close the60s goal.

Any accepted source change requires actual compiler construction and exact
seed propagation, independent trailing reviews, and one fresh seven-phase
gate on the reviewed final candidate. The earlier attested1afe candidate
remains retained evidence for its own bytes, not approval for changed sources.
