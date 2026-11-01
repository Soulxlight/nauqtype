# Nauqtype v0.1 Grammar

## Notes

- The grammar is intentionally small and suitable for a hand-written lexer plus recursive-descent / Pratt parser.
- Whitespace is insignificant except as a token separator.
- Newlines are not syntactic separators.
- The frozen stage0 reference includes statement-form `while`; the active stage1 surface also includes list, indexed and range `for` iteration and nearest-loop control.

## Lexical Grammar

### Identifiers

```ebnf
IDENT = ( "_" | ASCII_LETTER ) { "_" | ASCII_LETTER | ASCII_DIGIT } ;
```

### Integer Literals

```ebnf
INT_LIT = ASCII_DIGIT { ASCII_DIGIT } ;
```

### Float Literals

```ebnf
FLOAT_LIT = ASCII_DIGIT { ASCII_DIGIT } "." ASCII_DIGIT { ASCII_DIGIT }
            [ "e" [ "-" ] ASCII_DIGIT { ASCII_DIGIT } ] ;
```

`INT_LIT` immediately followed by `.` and an ASCII digit starts a `FLOAT_LIT`
(M56.2). A float literal has type `f64`. The exponent marker is lowercase `e`
with an optional `-` only. After `DIGITS "." DIGITS`, the lexer consumes an
`e` or `E`, at most one `+` or `-`, and the following digits; unless that is
`e`, an optional `-`, and at least one digit, the consumed span is one
malformed token reported as `NQ-PARSE-004` (`1.0E5`, `1.0e+5`, `1.0e`,
`1.0e-`). `.5`, `1.`, `1e5`, `1E5`, and `1e-5` are not float literals: since
M58.1 the lexer reads each as one malformed token reported as `NQ-PARSE-004`
with a help line showing the canonical form. `1.e5` and `1.foo` remain an
integer followed by field access.

### String Literals

```ebnf
STRING_LIT = '"' { STRING_CHAR } '"' ;
STRING_CHAR = any character except '"' and '\' and newline
            | '\' ( '"' | '\' | 'n' | 't' ) ;
```

### Comments

```ebnf
LINE_COMMENT = "//" { any character except newline } ;
```

### Keywords

`and`, `audit`, `break`, `const`, `continue`, `else`, `enum`, `false`, `fn`, `for`, `if`, `in`, `let`, `match`, `mut`, `mutref`, `not`, `or`, `pub`, `ref`, `return`, `true`, `try`, `type`, `use`, `while`

## Tokens

Punctuation and operators:

- `(` `)` `{` `}` `[` `]`
- `,` `;` `:` `.` `..`
- `::`
- `->` `=>`
- `=` `==` `!=`
- `<` `<=` `>` `>=`
- `+` `-` `*` `/` `%`

`..` is one token (maximal munch, left to right): `0..10` is `0`, `..`, `10`,
and a single `.` directly after `..` is a plain `.`, never the start of a
leading-dot float. `..` is legal only between the two bounds of a `for`
iterable; the range splits at the depth-zero `..` and binds more loosely than
every operator (`0..n + 1` is `0..(n + 1)`). Malformed ranges and `..`
elsewhere are `NQ-PARSE-006` (M58.2).

## High-Level Grammar

```ebnf
source_file   = { use_decl } { item_without_use } EOF ;

item_without_use = visibility? function_decl
                 | visibility? type_decl
                 | visibility? enum_decl
                 | visibility? const_decl ;

visibility    = "pub" ;

use_decl      = "use" module_path [ "as" IDENT ] ";" ;
module_path   = IDENT { "::" IDENT } ;
```

`use` is active in stage1. In a manifest workspace, `module_path` resolves from the declared source root; legacy flat-root projects retain their existing one-segment form. `as` creates one explicit module alias local to the importing file, for example `use app::render as report;` followed by `report::status()`. It does not rename exported definitions or create an implicit re-export.

## Declarations

```ebnf
function_decl = "fn" IDENT [ type_parameters ] "(" param_list? ")" "->" type_expr [ audit_block ] block ;
type_parameters = "<" IDENT { "," IDENT } ">" ;

const_decl    = "const" IDENT ":" type_expr "=" const_expr ";" ;

param_list    = param { "," param } [ "," ] ;
param         = IDENT ":" type_expr ;

type_decl     = "type" IDENT [ type_parameters ] "{" field_decl_list? "}" ;
field_decl_list = field_decl { "," field_decl } [ "," ] ;
field_decl    = IDENT ":" type_expr ;

enum_decl     = "enum" IDENT [ type_parameters ] "{" variant_decl_list? "}" ;
variant_decl_list = variant_decl { "," variant_decl } [ "," ] ;
variant_decl  = IDENT [ "(" type_list? ")" ] ;

type_list     = type_expr { "," type_expr } [ "," ] ;
```

`const_expr` is deliberately narrower than general `expr` in the first stage1 implementation: literals, parentheses, unary `-` / `not`, arithmetic and integer comparison operators, and boolean `and` / `or` over non-borrow `i32` / `i64` / `bool` / `str` constants only. String and boolean equality are intentionally rejected in const initializers until there is an explicit compile-time evaluator.

An `f64` constant initializer is narrower still (M56.2):

```ebnf
f64_const_expr = FLOAT_LIT | "-" FLOAT_LIT ;
```

Parentheses, repeated minus, arithmetic, constant references, and any `f64`
operand inside a `bool`/`i32`/`i64` initializer are rejected with
`NQ-TYPE-048`. There is no compile-time float folding.

## Audit Grammar

The keyword `audit` is reserved. Clause names inside the block are contextual and only meaningful there.

```ebnf
audit_block   = "audit" "{" intent_clause mutates_clause effects_clause [ propagates_clause ] "}" ;
intent_clause = "intent" "(" STRING_LIT ")" ";" ;
mutates_clause = "mutates" "(" ident_list? ")" ";" ;
effects_clause = "effects" "(" effect_list? ")" ";" ;
propagates_clause = "propagates" "(" ident_list? ")" ";" ;

ident_list    = IDENT { "," IDENT } [ "," ] ;
effect_list   = effect_name { "," effect_name } [ "," ] ;
effect_name   = "print" | "io" ;
```

## Type Grammar

```ebnf
type_expr     = borrow_type
              | named_type ;

borrow_type   = "ref" named_type
              | "mutref" named_type ;

named_type    = IDENT [ generic_args ]
              | "bool"
              | "f64"
              | "i32"
              | "i64"
              | "str"
              | "unit" ;

generic_args  = "<" generic_type_arg { "," generic_type_arg } ">" ;
generic_type_arg = type_expr | qualified_name [ generic_args ] ;
```

The archived bootstrap supports generic arguments only for builtin utility
types. The M56 active-stage1 extension admits explicit user function/product/
enum parameters and n-ary arguments under `docs/M56_CONTRACT.md`. Canonical
generic declaration/application vectors are nonempty and have no trailing
comma. All arguments are explicit; no inference or defaults.

```ebnf
explicit_type_arg = qualified_name_or_ident [ "<" explicit_type_arg { "," explicit_type_arg } ">" ] ;
value_application = qualified_name_or_ident "::" "<" explicit_type_arg { "," explicit_type_arg } ">" ;
qualified_name_or_ident = IDENT { "::" IDENT } ;
```

`value_application` can be a direct function/variant call target, a product
literal head, or an enum pattern head. An enum variant uses the full enclosing
enum vector, even a zero-payload variant (without `()`). Qualified nominal
type arguments require a directly imported module/alias. General qualified
annotation heads remain excluded. References remain parameter syntax, never
stored generic arguments; `propagates(E)` remains a single error-name atom.

## Block And Statement Grammar

```ebnf
block         = "{" { stmt } "}" ;

stmt          = let_stmt
              | let_try_stmt
              | let_propagate_stmt
              | let_else_stmt
              | assign_stmt
              | field_assign_stmt
              | if_stmt
              | while_stmt
              | for_stmt
              | match_stmt
              | break_stmt
              | continue_stmt
              | return_stmt
              | expr_stmt ;

let_stmt      = "let" [ "mut" ] IDENT [ ":" type_expr ] "=" expr ";" ;
let_try_stmt  = "let" [ "mut" ] IDENT ":" result_type "=" try_expr ";" ;
let_propagate_stmt = "let" [ "mut" ] IDENT [ ":" type_expr ] "=" expr "?" [ "[" IDENT "]" ] ";" ;
let_else_stmt = "let" let_else_pattern "=" expr "else" block ";" ;
let_else_pattern = ( "Some" | "Ok" ) "(" IDENT ")" ;
assign_stmt   = IDENT "=" expr ";" ;
field_assign_stmt = IDENT "." IDENT "=" expr ";" ;
return_stmt   = "return" [ expr ] ";" ;
expr_stmt     = expr ";" ;

if_stmt       = "if" expr block [ "else" block ] ;
while_stmt    = "while" expr block ;
for_stmt      = "for" IDENT [ "," IDENT ] "in" for_iterable block ;
for_iterable  = expr ".." expr | expr ;
break_stmt    = "break" ";" ;
continue_stmt = "continue" ";" ;

match_stmt    = "match" expr "{" match_arm { "," match_arm } [ "," ] "}" ;
match_arm     = pattern "=>" block ;
```

## Expression Grammar

Expressions are parsed with Pratt precedence or equivalent recursive-descent layering.

`try` V1 is deliberately narrower than the grammar envelope: it must be the direct initializer of an explicitly annotated `result<T, E>` local. A postfix propagation suffix inside that expression must apply to a direct function call. Short-circuit logic and `match` success expressions are rejected inside V1 boundaries.

```ebnf
expr          = logical_or ;

logical_or    = logical_and { "or" logical_and } ;
logical_and   = equality { "and" equality } ;
equality      = comparison { ( "==" | "!=" ) comparison } ;
comparison    = additive { ( "<" | "<=" | ">" | ">=" ) additive } ;
additive      = multiplicative { ( "+" | "-" ) multiplicative } ;
multiplicative = unary { ( "*" | "/" | "%" ) unary } ;

unary         = ( "-" | "not" ) unary
              | borrow_expr
              | postfix ;

borrow_expr   = ( "ref" | "mutref" ) borrow_place ;
borrow_place  = IDENT { "." IDENT }
              | "(" borrow_place ")" ;

postfix       = primary { call_suffix | field_suffix | propagation_suffix } ;
call_suffix   = "(" argument_list? ")" ;
field_suffix  = "." IDENT ;
propagation_suffix = "?" [ "[" IDENT "]" ] ;

argument_list = positional_arguments | named_arguments ;
positional_arguments = expr { "," expr } [ "," ] ;
named_arguments = named_argument { "," named_argument } [ "," ] ;
named_argument = IDENT ":" expr ;

primary       = literal
              | IDENT
              | qualified_name
              | value_application
              | struct_literal
              | list_literal
              | match_expr
              | try_expr
              | "(" expr ")" ;

try_expr      = "try" "{" expr "}" ;

qualified_name = IDENT "::" IDENT ;

struct_literal = ( qualified_name_or_ident | value_application ) "{" [ field_init_list | record_update_init ] "}" ;
field_init_list = field_init { "," field_init } [ "," ] ;
field_init    = IDENT ":" expr ;
record_update_init = "from" IDENT "," field_init_list ;

list_literal  = "[" [ expr { "," expr } [ "," ] ] "]" ;

match_expr    = "match" expr "{" match_expr_arm { "," match_expr_arm } [ "," ] "}" ;
match_expr_arm = pattern "=>" expr ;
```

Parser note:

- `IDENT "(" ... ")"` may resolve later as either a function call or an enum constructor call.
- `IDENT "::" IDENT "(" ... ")"` is a Batch B direct module-qualified function call only.
- Named arguments are Batch B function-call labels only; constructor payloads stay positional.
- `IDENT "{" ... "}"` is a struct literal when the identifier resolves to a `type`.
- `IDENT "{ from base, field: value }"` is a copy-only record update; `from` is contextual in this position and `base` must be a simple visible name that satisfies the record-update ownership and copy rules.
- `[]` requires an expected `list<T>` context. Non-empty list literals infer from the first element unless an expected `list<T>` is available, and all elements must have one homogeneous type. Spreads, comprehensions, ranges, and const list initializers are not part of V1.
- Statement `match` arms remain block-bodied; only `match_expr` arms are expression-bodied.
- `let_else_stmt` is narrow in V1: only `Some(name)` and `Ok(name)` guard bindings are accepted, and the `else` block must exit with `return`, `break;` or `continue;` (SPEC "Local Bindings").
- `field_assign_stmt` is narrow in V1: its base is a `let mut` local or a `mutref` parameter of a product type, never a nested field (`NQ-TYPE-059`), enum, list element, or arbitrary expression.
- A `let` binding is visible from the end of its statement; its initializer cannot see it (SPEC "Local Bindings").
- Every function body must end each path in `return` (SPEC "Every path returns", `NQ-TYPE-053`); `while true` with no `break` targeting it counts as terminating, where the condition is exactly the token `true`.
- `borrow_expr` is legal only as a direct call argument.
- A call's callee must be a function name (`NQ-TYPE-058`); `field_init` is the only struct-literal field form (`NQ-TYPE-055`).
- `propagation_suffix` is legal only in `let_propagate_stmt` and on direct call operands inside `try_expr` (`NQ-PROPAGATE-007`).

## Pattern Grammar

```ebnf
pattern       = "_"
              | INT
              | "-" INT
              | ( qualified_name_or_ident | value_application ) [ "(" pattern_list? ")" ] ;

pattern_list  = pattern { "," pattern } [ "," ] ;
```

Pattern meaning is resolved semantically:

- bare `IDENT` may be a binding or a unit-like constructor
- `IDENT(...)` is a tuple-like constructor pattern
- integer literals, including `-INT`, match only `i32` scrutinees
- `true`/`false`, string literals, negated non-literals and other shapes are not patterns (`NQ-TYPE-056`); an unknown constructor is `NQ-RESOLVE-010`
- float literals are never patterns, and an `f64` value is never a scrutinee (`NQ-TYPE-047`)
- constructor patterns may nest recursively; a match containing a literal or nested constructor pattern requires a wildcard or binding fallback arm

## Precedence And Associativity

| Level | Operators | Associativity |
| --- | --- | --- |
| 1 | `or` | left |
| 2 | `and` | left |
| 3 | `==`, `!=` | left |
| 4 | `<`, `<=`, `>`, `>=` | left |
| 5 | `+`, `-` | left |
| 6 | `*`, `/`, `%` | left |
| 7 | unary `-`, `not`, `ref`, `mutref` | right |
| 8 | qualified name, call, field access | left |

## Grammar Simplifications Chosen Intentionally

- No newline significance
- No implicit last-expression returns
- No general block expressions
- No loop grammar beyond `while`, list and indexed `for`, half-open range `for`, and nearest-loop `break;` / `continue;`; a range is not an expression
- AI Contracts use a fixed clause order instead of free-form annotations
- Explicit M56 generic parameters only; no inference, constraints or generic constants
