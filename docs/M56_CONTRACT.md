# M56: Explicit Generic Reuse Foundation

Status: both independent Gate A reviews passed, 2026-10-23. This is the
implementation/acceptance contract; closing evidence is recorded separately
in ROADMAP, TODO and AUDIT_REMEDIATION. Base: `2ddd097`.
M56 is not a stable release, M57 collections, or a new ownership model.

## Problem And Usage Pressure

Compiler and library authors duplicate list/value helpers and product wrappers
because only builtin containers accept type arguments. Admit explicit reuse
without method lookup, traits, hidden conversions, or inferred requirements.
The already-closed P1-P4 performance checkpoint remains separate evidence.

## Canonical Syntax

```nq
fn identity<T>(value: T) -> T {
    return value;
}

type Parcel<T> {
    value: T,
}

enum Choice<T, E> {
    Value(T),
    Failure(E),
}

fn main() -> i32 {
    let item: Parcel<i32> = Parcel::<i32> { value: identity::<i32>(7) };
    let selected: Choice<i32, str> = Value::<i32, str>(item.value);
    match selected {
        Value::<i32, str>(number) => { return number; },
        Failure::<i32, str>(_) => { return 1; },
    }
}
```

Function, product, and enum declarations have an ordered nonempty list of
distinct type-parameter identifiers. Every application supplies every argument
explicitly. `name::<Types>` is value/pattern application; `Name<Types>` is
type application. Imported applications retain the existing explicit module
qualifier/alias (`module::function::<i32>(...)`). An enum variant takes its
enclosing enum's complete argument list, including zero-payload variants and
pattern occurrences. A zero-payload expression/pattern is `Empty::<i32>`
without `()`. Within explicit generic arguments only, `alias::Tag` may name a
nominal type from a directly imported module; aliases are not type identities.
Ordinary top-level type annotation heads remain unqualified. Generic functions
named `main` are rejected: the driver supplies no type arguments to entrypoints.
`propagates(E)` may name a template parameter; concrete substitution and existing
contract validation check the exact resulting error type. Its argument must
still fit the existing single concrete builtin/nominal error-name atom; a
utility-container error argument is rejected rather than widening audit syntax
or silently discarding type arguments.

There are no defaults, inference, overloads, generic constants, higher-kinded
parameters, type-level values, constraints, traits, methods, or implicit
conversions. A type parameter is not a value or constructor. It cannot shadow
another parameter, a builtin type, an import alias, or a value binding in its
template. Field and argument labels remain labels, not type substitutions.

## Exact Semantics And Construction Boundary

1. Capture the existing workspace/dependency graph without widening authority.
2. Inventory structured template declarations and explicit type applications.
   Parse type arguments recursively; resolve each nominal argument to its
   declaration module before substitution. Reject unknown, ambiguous, private,
   wrong-kind, wrong-arity, borrowed/stored-reference, or forged internal names.
3. Check syntax, definition-scope name/type resolution, declaration uniqueness,
   parameter binding, target kinds/arities, audit structure, and forbidden
   reference storage of every template, including unused templates. In
   particular, `type Bad<T> { value: ref T }` is rejected without instantiation.
   Concrete operation/type compatibility and ownership are checked for each
   demanded instance, not universally proved for all types. No instance means
   no claim that the body is checked for a particular type.
4. Intern concrete instances by template module, declaration identity, and
   the ordered recursively canonical type arguments. Keep ordinary recursion
   on an identical instance. A definition-expansion dependency path which
   revisits a template with different arguments is polymorphic recursion and
   is rejected, including mutual cycles; worklist order must not affect this.
   Explicit finite nesting of the same template in a type argument is not a
   definition-expansion cycle. Maximum type-application depth is32 (a scalar
   is0, `list<i32>` is1); maximum distinct function/product/enum instances is256
   across the whole graph. Repeated applications and enum variants do not use
   extra slots. Boundaries32/33 and256/257 are tested. Reject instantiated data
   layout cycles, including through containers, rather than guessing drop/layout.
   Depth/count limits do not bound serialized width: before allocation or
   concatenation, also bound one canonical type at4096 bytes, an instance key
   at16384 bytes, generated template tokens at131072 per project, elaborated
   text at8388608 bytes per project, and maps/registries at16777216 bytes per
   project. Count UTF-8 bytes, including delimiters; reject overflow before
   multiplication/addition. Ordinary source tokens are not charged against the
   generated-token limit. Acyclic repeated `result<T,T>` expansion must fail
   normally at a bound, not allocate exponential text. Test exact size edges
   and an explosive-width chain in addition to recursion/depth/count cases.
5. Materialize concrete declarations in their definition module and lexical
   environment. Preserve actual nominal type origins across modules; never
   introduce imports that change unrelated lookup/ambiguity or expose a private
   template to source code. Reserve collision-free internal specialization
   names and reject their spelling in user source.
6. Existing resolution, typechecking, contract validation, checked handoff,
   ownership/value planning, borrow checking, IR, and C emission validate the
   concrete program. Backends do not read templates, raw tokens, or flat facts.
   A checked-type layout graph, before value planning, rejects concrete data
   cycles, including cycles that bridge a nongeneric declaration. It uses
   checked type/field/variant IDs, not template-name heuristics or raw facts.

This is a dedicated structured frontend elaborator, not unrestricted textual
replacement, a C macro facility, a parser/typechecker rewrite, or backend
reconstruction from source. Specialization happens before checked handoff;
the checked handoff and IR remain concrete and self-sufficient. Repeated
applications reuse one instance. Initial traversal is captured module/source
order followed by a deterministic instance worklist; key/name assignment is
content-derived, not a discovery counter or a host path.

Every explicit application in an ordinary declaration or body is a root,
including code unreachable from `main`. Applications inside a template are
validated structurally now but demanded only with that template's instance.
Compiler-internal audit/effect/propagation validation remains mandatory even
when external evidence export rejects generic input.

The nominal registry binds a concrete generated atom to its declaration-owned
identity, module, ordered argument vector and original span. Parameter IDs are
owned by their declaration and ordered index, never a globally substituted
name. Every generated parser item is authenticated against the exact registry;
a prefix or globally unique spelling is not authorization. Only authenticated
nominal references bypass ordinary import lookup after the source reference
has passed visibility checking. All consumers resolve the same canonical atom:
no handoff recovery from an accidentally matching short name. A caller's `Tag`
must remain that caller's type when passed into a template whose module owns a
different private `Tag`. Instance vectors are n-ary; three-argument coverage is
required despite the legacy two-argument convenience fields.

## Source Identity And Evidence

Keep immutable original bytes/path and a compiler-owned token-origin map for
elaborated sources. Tokens/facts/handoff/IR use unique elaborated coordinates;
each repeated lexer consumer reads the identical elaborated text. Do not put
multiple instances at the same internal coordinate or mix token indexes and
byte offsets. Reporting maps ranges back to original bytes; substitute type
tokens are anchored to the template type occurrence. The map covers every
token including EOF, validates monotone elaborated ranges and original bounds,
and binds an instance context. Missing/inconsistent mappings fail closed.
Diagnostic JSON spans and rendered lines/columns use mapped original bytes;
instance diagnostics also identify the concrete application. Constant paths,
handoff/typecheck re-readers and internal review use the same source view.
Mapping preserves existing stage1 diagnostic point conventions, including
statement-point borrow errors; it does not claim to refine all operand spans.

Keep an internal relation from each concrete identity to its source template,
ordered canonical argument identities, declaration span, and application sites.
The immutable source-template identity is not the C symbol or an instance ID.

The proof exposed an existing call-only propagation-evidence gap. Ordinary
`let value = operand?` evidence is enriched from the unique checked statement,
binding and root result/error type IDs, including names and fields. Missing or
inconsistent joins, duplicate identities and unrepresentable error atoms fail
with NQ-INTERNAL-012; nested calls or declared return types are not substitutes
for operand truth. Local `try` evidence keeps its separate existing boundary.

Existing machine-readable formats and all nongeneric goldens stay unchanged.
They describe source declarations, not monomorphized instances: do not silently
redefine them or export generated declarations as fabricated source facts.
For this foundation, `facts`, `review`, `review-diff`, `change-report`,
`policy-check`, and `refactor-rename` explicitly reject a captured graph that
contains generics, including unused templates. Preserve each command's existing
failure envelope and do not emit a partial successful report. Generic-aware
source/instance export requires a separately versioned format contract before
these commands accept generic graphs. This restriction is an explicit M56
limitation, not completed evidence parity or a stable generic library promise.

In particular, rename must not emit generated names as source replacements,
incomplete edits, or mutate files. Formatter-lite preserves explicit generic
punctuation and remains output-only; formatting is not semantic validation.

## Diagnostics And Teaching

Reserve `NQ-GENERIC-001` through `NQ-GENERIC-009` for invalid declarations,
missing/extra arguments, invalid/unresolved type arguments or targets, invalid
parameter use/capture, recursion/instance bounds, internal-name forgery,
unsupported template refactoring, and invalid elaboration metadata. Exact
assignment/messages are locked with focused positive/negative cases before
close. Existing type/borrow/contract diagnostics remain the authority for
concrete-body errors; include specialization context rather than relabel them.

Canonical teaching covers identity/list reuse, generic products/enums, nested
utility/user shapes, imported/aliased calls, named arguments, and explicit
borrow parameters. Pair them with wrong arity/type, missing explicit arguments,
private/ambiguous imports, duplicate/captured parameters, ownership failures,
unused-template name failures, recursion limits, and rejected rename cases.
The conservative alternative remains an explicitly typed nongeneric helper.

## Bootstrap, Performance, And Acceptance

Active implementation and fixtures are Nauqtype. Python stays frozen; no new
runtime primitive or public command is needed. Initially keep compiler source
in the previous supported dialect while building the new phase. Promote only
exact compiler-generated C with source inventory, lineage, runtime, and the
standing self-build comparison; never hand-edit generated C.

Develop on one assigned native-ext4 WSL Ubuntu24.04 candidate, syncing changed
files only. Preserve existing wall/RSS ceilings and serial default/full/proof
contracts. The prior driver peak520116KiB leaves only4172KiB below its ceiling:
measure compiler construction early and optimize a demonstrated blocker rather
than quietly raising a budget. No generic speedup is claimed without a pair.

Required acceptance:

- direct owned Nauqtype generic probes, positive runtime corpus, focused
  diagnostics, ownership checks, tooling/refactor behavior, and formatter
  idempotence pass;
- unchanged nongeneric evidence goldens pass; generic graphs are rejected
  deterministically by legacy evidence/edit commands, and internal instance
  origins/diagnostics preserve actual original locations;
- copied-selfhost/seed fixed point and the complete existing corpus stay green;
- new generic modules are explicitly registered in copied-selfhost and included
  in the exact seed source inventory; a genuine imported function/product/enum
  composition runs through both the seed-rebuilt compiler and the relocated
  copied-release compiler outside the checkout (a nongeneric fixed point alone
  does not establish generic bootstrap/relocation behavior);
- seed and relocated generic smoke inputs bind the same two original/copied
  source files, modes and flat-loading boundary before and after execution;
  persistent copied-source mutation fails the proof rather than changing its target;
- independent Sol xhigh and adversarial Astra xhigh audits pass (GPT-5.5 is
  unavailable on this host; retain the explicitly recorded mixed fallback);
- after repairs and focused checks, freeze once and run
  `scripts/check_milestone.sh` on the exact reviewed Linux candidate;
- update README/spec/grammar/decisions/deferred/teaching and coordination to the
  implemented boundary without claiming M57 or stable release completion.

No commit/push before the audits and exact-candidate close. Do not overwrite
the sealed P1-P4 evidence or change downstream consumer pins.
