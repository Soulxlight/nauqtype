# Nauqtype Formatter-Lite Contract

Formatter-lite exists to make canonical Nauqtype teaching material stable for humans, agents, and future model training. It is intentionally small: it normalizes trusted-subset source layout without becoming a full AST-preserving formatter.

## Public Surface

- `fmt <source>` writes formatted text to stdout only.
- `fmt --check <source>` exits successfully only when the source is already canonical.
- Formatter-lite never mutates files.
- Formatter write mode stays deferred until comment preservation is safe.

## Canonical Layout

- Use LF newlines and end formatted output with a newline.
- Use four spaces per brace depth.
- Do not use tabs.
- Trim leading and trailing spaces on non-empty lines.
- Preserve blank lines as blank lines.
- Dedent lines that begin with `}` before printing them.
- Ignore braces inside string literals and line comments when computing indentation.

Formatter-lite does not reorder imports, reflow expressions, align columns, move comments, normalize names, or change source semantics. It is a line-and-brace formatter for the current teaching subset.

## Fail-Closed Cases

Formatter-lite rejects source instead of guessing when it sees:

- tabs
- unbalanced closing braces
- unbalanced opening braces

Unsupported formatter cases should stay explicit. Silent cleanup is not allowed when it could hide meaning from a human supervisor or an agent pair.

## Teaching Corpus Rule

Every canonical example under `examples/` must pass `fmt --check`. Runnable examples must also be part of `prove-corpus`; helper-only modules must still be part of the `prove` formatter sweep.

A new example is not canonical until:

- it is committed in formatter-lite output form
- `fmt --check` accepts it
- the locked formatter example list in `selfhost/proof.nq` includes it
- the stage1 driver guard confirms the list still covers every `examples/*.nq` file

This keeps examples useful as live documentation and as future LLM teaching material.
