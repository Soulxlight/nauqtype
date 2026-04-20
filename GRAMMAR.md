# Nauqtype v0.1 Grammar

## Notes

- The grammar is intentionally small and suitable for a hand-written lexer plus recursive-descent / Pratt parser.
- Whitespace is insignificant except as a token separator.
- Newlines are not syntactic separators.

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

`and`, `else`, `enum`, `false`, `fn`, `if`, `let`, `match`, `mut`, `mutref`, `not`, `or`, `pub`, `ref`, `return`, `true`, `type`, `use`

## Tokens

Punctuation and operators:

- `(` `)` `{` `}`
- `,` `;` `:` `.`
- `->` `=>`
- `=` `==` `!=`
- `<` `<=` `>` `>=`
- `+` `-` `*` `/`

## High-Level Grammar

```ebnf
source_file   = { item } EOF ;

item          = visibility? function_decl
              | visibility? type_decl
              | visibility? enum_decl
              | use_decl ;

visibility    = "pub" ;

use_decl      = "use" IDENT ";" ;
```

`use` is reserved in v0.1 but semantic import resolution is deferred.

## Declarations

```ebnf
function_decl = "fn" IDENT "(" param_list? ")" "->" type_expr block ;

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

In v0.1, generic arguments are semantically valid only for built-in `option<T>` and `result<T, E>`.

## Block And Statement Grammar

```ebnf
block         = "{" { stmt } "}" ;

stmt          = let_stmt
              | assign_stmt
              | if_stmt
              | match_stmt
              | return_stmt
              | expr_stmt ;

let_stmt      = "let" [ "mut" ] IDENT [ ":" type_expr ] "=" expr ";" ;
assign_stmt   = IDENT "=" expr ";" ;
return_stmt   = "return" [ expr ] ";" ;
expr_stmt     = expr ";" ;

if_stmt       = "if" expr block [ "else" block ] ;

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

argument_list = expr { "," expr } [ "," ] ;

primary       = literal
              | IDENT
              | struct_literal
              | "(" expr ")" ;

struct_literal = IDENT "{" field_init_list? "}" ;
field_init_list = field_init { "," field_init } [ "," ] ;
field_init    = IDENT ":" expr ;
```

Parser note:

- `IDENT "(" ... ")"` may resolve later as either a function call or an enum constructor call.
- `IDENT "{" ... "}"` is a struct literal when the identifier resolves to a `type`.

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
| 8 | call, field access | left |

## Grammar Simplifications Chosen Intentionally

- No newline significance
- No implicit last-expression returns
- No expression-bodied match arms
- No loop grammar in v0.1
- No literal patterns in v0.1
- No generic parameter declarations in v0.1
