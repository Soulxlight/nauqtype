# Nauqtype v0.1 Grammar

## Notes

- The grammar is intentionally small and suitable for a hand-written lexer plus recursive-descent / Pratt parser.
- Whitespace is insignificant except as a token separator.
- Newlines are not syntactic separators.
- The current stage0 compiler includes one controlled bootstrap-track extension to the original v0.1 freeze: statement-form `while` loops only.

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

`and`, `audit`, `break`, `const`, `continue`, `else`, `enum`, `false`, `fn`, `if`, `let`, `match`, `mut`, `mutref`, `not`, `or`, `pub`, `ref`, `return`, `true`, `type`, `use`, `while`

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

use_decl      = "use" IDENT ";" ;
```

`use` is active in stage1 and resolves against a single flat workspace root.

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
audit_block   = "audit" "{" intent_clause mutates_clause effects_clause "}" ;
intent_clause = "intent" "(" STRING_LIT ")" ";" ;
mutates_clause = "mutates" "(" ident_list? ")" ";" ;
effects_clause = "effects" "(" effect_list? ")" ";" ;

ident_list    = IDENT { "," IDENT } [ "," ] ;
effect_list   = effect_name { "," effect_name } [ "," ] ;
effect_name   = "print" ;
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
              | let_else_stmt
              | assign_stmt
              | if_stmt
              | while_stmt
              | match_stmt
              | break_stmt
              | continue_stmt
              | return_stmt
              | expr_stmt ;

let_stmt      = "let" [ "mut" ] IDENT [ ":" type_expr ] "=" expr ";" ;
let_else_stmt = "let" let_else_pattern "=" expr "else" block ";" ;
let_else_pattern = ( "Some" | "Ok" ) "(" IDENT ")" ;
assign_stmt   = IDENT "=" expr ";" ;
return_stmt   = "return" [ expr ] ";" ;
expr_stmt     = expr ";" ;

if_stmt       = "if" expr block [ "else" block ] ;
while_stmt    = "while" expr block ;
break_stmt    = "break" ";" ;
continue_stmt = "continue" ";" ;

match_stmt    = "match" expr "{" match_arm { "," match_arm } [ "," ] "}" ;
match_arm     = pattern "=>" block ;
```

## Expression Grammar

Expressions are parsed with Pratt precedence or equivalent recursive-descent layering.

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

postfix       = primary { call_suffix | field_suffix } ;
call_suffix   = "(" argument_list? ")" ;
field_suffix  = "." IDENT ;

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
              | "(" expr ")" ;

qualified_name = IDENT "::" IDENT ;

struct_literal = IDENT "{" field_init_list? "}" ;
field_init_list = field_init { "," field_init } [ "," ] ;
field_init    = IDENT ":" expr ;

list_literal  = "[" [ expr { "," expr } [ "," ] ] "]" ;

match_expr    = "match" expr "{" match_expr_arm { "," match_expr_arm } [ "," ] "}" ;
match_expr_arm = pattern "=>" expr ;
```

Parser note:

- `IDENT "(" ... ")"` may resolve later as either a function call or an enum constructor call.
- `IDENT "::" IDENT "(" ... ")"` is a Batch B direct module-qualified function call only.
- Named arguments are Batch B function-call labels only; constructor payloads stay positional.
- `IDENT "{" ... "}"` is a struct literal when the identifier resolves to a `type`.
- `[]` requires an expected `list<T>` context. Non-empty list literals infer from the first element unless an expected `list<T>` is available, and all elements must have one homogeneous type. Spreads, comprehensions, ranges, and const list initializers are not part of V1.
- Statement `match` arms remain block-bodied; only `match_expr` arms are expression-bodied.
- `let_else_stmt` is narrow in V1: only `Some(name)` and `Ok(name)` guard bindings are accepted, and the `else` block must exit explicitly.

## Pattern Grammar

```ebnf
pattern       = "_"
              | IDENT [ "(" pattern_list? ")" ] ;

pattern_list  = pattern { "," pattern } [ "," ] ;
```

Pattern meaning is resolved semantically:

- bare `IDENT` may be a binding or a unit-like constructor
- `IDENT(...)` is a tuple-like constructor pattern

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
- No loop grammar beyond bootstrap `while` and Batch B `break;` / `continue;`
- AI Contracts use a fixed clause order instead of free-form annotations
- No literal patterns in v0.1
- No generic parameter declarations in v0.1
