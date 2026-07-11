# Nauqtype Syntax Identity And Evolution SOP

Status: policy baseline for all future language changes. M41 validates this policy against workspace syntax before nested modules are implemented.

## Identity

> Nauqtype keeps local value flow concise, but makes every authority boundary explicit and compiler-evidenced.

Authority boundaries include mutation, borrowing, fallibility, effects, provenance, ownership, dependencies, and policy. A shorter spelling is valuable only when it preserves or improves those checked facts.

Nauqtype does not grow by reproducing another language's feature ladder. A feature earns admission when it removes demonstrated authoring or supervision friction while strengthening the compiler facts available to an agent pair and a human reviewer.

## Non-Negotiable Rules

- Keep ordinary local value flow compact: direct calls, literals, fields, `match`, and explicit local bindings should remain readable without ceremonial syntax.
- Mark authority transitions at their boundary: `let mut`, `ref`, `mutref`, `audit`, `effects`, `propagates`, and future dependency declarations must stay visible in source.
- Give every feature one canonical spelling and a deliberately narrow first semantic contract.
- Do not hide control flow, mutation authority, effects, error conversion, module provenance, dependency resolution, or policy consequences.
- Complete compiler evidence before calling syntax shipped: facts, review, change reporting, policy impact, and refactor impact must either support the feature or reject it explicitly.
- Treat compatibility and migration as semantic work. A new form must not silently reinterpret old source.

## Syntax Decision SOP

### 1. Establish Real Pressure

Record a concrete program, internal-tool task, corpus gap, or review failure that the feature solves. "Other languages have it" is not sufficient pressure.

### 2. Select One Canonical Form

Specify one spelling, its legal positions, and its first-version limits. Prefer a small explicit form over several equivalent forms or overloaded punctuation.

### 3. Define Semantics And Authority

State parsing, resolution, type rules, lowering, runtime behavior, failure behavior, and any desugaring. Explicitly state what authority crosses the form and where that authority becomes visible.

### 4. Define Evidence Before Implementation

State the stable IDs, facts, review output, diffs, policy checks, refactor plans, diagnostics, and formatter behavior. If a surface cannot represent the change truthfully, the feature is incomplete.

### 5. Teach The Boundary

Ship one canonical positive example and one negative teaching case. The negative case must explain the conservative alternative, not merely report rejection.

### 6. Prove Composition

Add parser through C-emission coverage, a runtime or proof-corpus case where appropriate, and one stress-leg composition case when the feature changes control flow, modules, ownership, or supervision evidence.

## Required Decision Record

Every source-language proposal must answer:

```text
Problem and real usage pressure:
Canonical syntax:
Rejected alternatives:
Exact semantics and desugaring:
Authority and evidence impact:
Diagnostics and formatter rule:
Teaching positive and negative cases:
Compiler phases and schema effects:
Migration and deferred extensions:
Acceptance gate:
```

## Workspace Syntax Direction

M41 locks [WORKSPACE_CONTRACT.md](WORKSPACE_CONTRACT.md) as the implementation-facing contract for M42 and M43. The following is planned syntax, not current Nauqtype syntax:

```nauq
use org::reporting::render as report;
use org::reporting::model::Summary;

fn main() -> i32 {
    let summary: Summary = report::build(...);
    return 0;
}
```

The design intent is deliberate:

- `::` scales explicit module provenance; `.` remains field access only.
- A manifest resolves every package and module path to one canonical identity and source file; M44 adds checked local-dependency content hashes.
- Facts retain both the source spelling and resolved target identity.
- Aliases are explicit and formatter-normalized.
- No wildcard imports, implicit re-exports, hidden search paths, or automatic dependency fetching are permitted in the first workspace model.

## Rejected Growth Patterns

- Multiple interchangeable spellings for the same authority boundary.
- Implicit error conversion, panic-style unwrap, or exception-like flow.
- Method lookup or receiver rewriting hidden behind field syntax.
- Broad lvalue, reference, or lifetime expansion inferred from a narrow mutation convenience.
- User-defined effect atom sprawl before fixed evidence surfaces prove insufficient.
- Dependency resolution that depends on the current directory, environment, network state, or unrecorded cache.
- Syntax admitted before its diagnostic, formatter, evidence, teaching, and proof contract exists.

## Completion Rule

A feature is complete only when its source form, checked evidence, teaching example, conservative rejection, and proof behavior all agree. If any layer must guess, the feature remains planned rather than shipped.
