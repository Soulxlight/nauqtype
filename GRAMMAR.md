# Nauqtype v0.1 Grammar

## Notes

- The grammar is intentionally small and suitable for a hand-written lexer plus recursive-descent / Pratt parser.
- Whitespace is insignificant except as a token separator.
- Newlines are not syntactic separators.
- The frozen stage0 reference includes statement-form `while`; the active stage1 surface also includes list-only `for` iteration and nearest-loop control.

## Lexical Grammar

### Identifiers

```ebnf
IDENT = ( "_" | ASCII_LETTER ) { "_" | ASCII_LETTER | ASCII_DIGIT } ;
```

### Integer Literals

```ebnf
INT_LIT = ASCII_DIGIT { ASCII_DIGIT } ;
```

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
- `,` `;` `:` `.`
- `::`
- `->` `=>`
- `=` `==` `!=`
- `<` `<=` `>` `>=`
- `+` `-` `*` `/`

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
function_decl = "fn" IDENT "(" param_list? ")" "->" type_expr [ audit_block ] block ;

const_decl    = "const" IDENT ":" type_expr "=" const_expr ";" ;

param_list    = param { "," param } [ "," ] ;
param         = IDENT ":" type_expr ;

type_decl     = "type" IDENT "{" field_decl_list? "}" ;
field_decl_list = field_decl { "," field_decl } [ "," ] ;
field_decl    = IDENT ":" type_expr ;

enum_decl     = "enum" IDENT "{" variant_decl_list? "}" ;
variant_decl_list = variant_decl { "," variant_decl } [ "," ] ;
variant_decl  = IDENT [ "(" type_list? ")" ] ;

type_list     = type_expr { "," type_expr } [ "," ] ;
```

`const_expr` is deliberately narrower than general `expr` in the first stage1 implementation: literals, parentheses, unary `-` / `not`, arithmetic and integer comparison operators, and boolean `and` / `or` over non-borrow `i32` / `bool` / `str` constants only. String and boolean equality are intentionally rejected in const initializers until there is an explicit compile-time evaluator.

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
              | "i32"
              | "str"
              | "unit" ;

generic_args  = "<" type_expr { "," type_expr } [ "," ] ">" ;
```

In the current bootstrap compiler, generic arguments are semantically valid only for built-in `option<T>`, `result<T, E>`, and `list<T>`.

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
for_stmt      = "for" IDENT "in" expr block ;
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
multiplicative = unary { ( "*" | "/" ) unary } ;

unary         = ( "-" | "not" ) unary
              | borrow_expr
              | postfix ;

borrow_expr   = "ref" IDENT
              | "mutref" IDENT ;

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
              | struct_literal
              | list_literal
              | match_expr
              | try_expr
              | "(" expr ")" ;

try_expr      = "try" "{" expr "}" ;

qualified_name = IDENT "::" IDENT ;

struct_literal = IDENT "{" [ field_init_list | record_update_init ] "}" ;
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
- `let_else_stmt` is narrow in V1: only `Some(name)` and `Ok(name)` guard bindings are accepted, and the `else` block must exit explicitly.
- `field_assign_stmt` is narrow in V1: its base is a direct owned `let mut` product binding, never a nested field, `mutref` parameter, enum, list element, or arbitrary expression.

## Pattern Grammar

```ebnf
pattern       = "_"
              | INT
              | "-" INT
              | IDENT [ "(" pattern_list? ")" ] ;

pattern_list  = pattern { "," pattern } [ "," ] ;
```

Pattern meaning is resolved semantically:

- bare `IDENT` may be a binding or a unit-like constructor
- `IDENT(...)` is a tuple-like constructor pattern
- integer literals, including `-INT`, match only `i32` scrutinees
- constructor patterns may nest recursively; a match containing a literal or nested constructor pattern requires a wildcard or binding fallback arm

## Precedence And Associativity

| Level | Operators | Associativity |
| --- | --- | --- |
| 1 | `or` | left |
| 2 | `and` | left |
| 3 | `==`, `!=` | left |
| 4 | `<`, `<=`, `>`, `>=` | left |
| 5 | `+`, `-` | left |
| 6 | `*`, `/` | left |
| 7 | unary `-`, `not`, `ref`, `mutref` | right |
| 8 | qualified name, call, field access | left |

## Grammar Simplifications Chosen Intentionally

- No newline significance
- No implicit last-expression returns
- No general block expressions
- No loop grammar beyond `while`, list-only `for`, and nearest-loop `break;` / `continue;`
- AI Contracts use a fixed clause order instead of free-form annotations
- No generic parameter declarations in v0.1
