# Nauqtype Risk Register

## R001: Parser risk

- Description: expression parsing, constructor syntax, and match arm handling could become inconsistent if the grammar grows mid-stream.
- Impact: high
- Likelihood: medium
- Mitigation: freeze the grammar early, require semicolons/commas, and keep arm bodies as blocks.
- v0.1 stance: avoid

## R002: Ownership-checking risk

- Description: adding stored references or field borrows would explode complexity.
- Impact: high
- Likelihood: high if scope is not protected
- Mitigation: keep references temporary and call-scoped only.
- v0.1 stance: avoid

## R003: Type-system risk

- Description: user-defined generics, inference, and ad hoc conversions would complicate checking and diagnostics.
- Impact: high
- Likelihood: medium
- Mitigation: monomorphic user types only, no implicit conversions, built-in generic utility types only.
- v0.1 stance: avoid

## R004: Diagnostics risk

- Description: a technically correct compiler can still be poor at supervision if errors are vague or unstable.
- Impact: high
- Likelihood: medium
- Mitigation: structured diagnostics, golden tests, and span tracking from the lexer onward.
- v0.1 stance: accept and mitigate

## R005: Codegen risk

- Description: tagged union layout and match lowering can become brittle, especially for nested patterns.
- Impact: high
- Likelihood: medium
- Mitigation: lower through a small typed IR and keep emitted C readable and deterministic.
- v0.1 stance: accept and mitigate

## R006: Standard-library scope risk

- Description: pressure to add collections, formatting, and I/O could consume time better spent on the compiler core.
- Impact: medium-high
- Likelihood: high
- Mitigation: tiny runtime boundary and explicit deferred list.
- v0.1 stance: avoid

## R007: Scope-creep risk

- Description: language projects attract speculative features before the vertical slice works.
- Impact: very high
- Likelihood: high
- Mitigation: decision log, deferred-features document, and scope freeze after research.
- v0.1 stance: avoid

## R008: AI-friendliness risk

- Description: if syntax grows irregular or overloaded, AI-written code quality will drop sharply.
- Impact: high
- Likelihood: medium
- Mitigation: keep a small set of syntax templates, avoid hidden inference, and preserve explicit ownership markers.
- v0.1 stance: accept and mitigate

## R009: Future-backend migration risk

- Description: compile-to-C shortcuts might leak into the language model and make future direct native backends harder.
- Impact: medium
- Likelihood: medium
- Mitigation: separate typed IR from backend details and avoid exposing C-specific semantics in the source language.
- v0.1 stance: accept and mitigate

## R010: Runtime model risk

- Description: string and enum runtime representations may drift from language semantics if not documented clearly.
- Impact: medium
- Likelihood: medium
- Mitigation: define `str`, `option`, and `result` lowering explicitly in the architecture and backend docs.
- v0.1 stance: accept and mitigate

## R011: Test coverage illusion risk

- Description: compiler projects can appear healthy with parser tests only while semantic passes remain fragile.
- Impact: high
- Likelihood: medium
- Mitigation: require tests for lexing, parsing, resolution, type checking, ownership, C emission, and integration.
- v0.1 stance: avoid

## R012: Bootstrap implementation-language divergence risk

- Description: using Python for the current bootstrap compiler could drift away from the intended long-term Rust implementation if the architecture is not kept disciplined.
- Impact: medium
- Likelihood: medium
- Mitigation: keep phases cleanly separated, keep generated artifacts deterministic, and avoid Python-specific shortcuts that would not survive a Rust port.
- v0.1 stance: accept and mitigate
