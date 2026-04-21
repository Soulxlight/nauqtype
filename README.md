# Nauqtype

Nauqtype is a small compiled language designed for AI-authored software under human supervision.

Current bootstrap status:

- `stage0`: Python bootstrap compiler in the current workspace
- flat-root multi-file imports with one workspace root
- explicit types at function boundaries
- nominal `type` and `enum`
- `option<T>` and `result<T, E>`
- builtin `io_err` and `list<T>`
- explicit `match`
- bootstrap file input and string helpers
- minimal move / borrow checking
- structural copy for all-copy user `type` / `enum`
- compile-to-C backend with a tiny runtime
- `selfhost/`: first Nauqtype-written front-end skeleton that can load, lex, parse, and diagnose its own module tree

## Quick Start

Install local bootstrap dependencies:

```powershell
python scripts/setup_deps.py
```

Run the full test suite:

```powershell
python -m unittest discover -s tests -v
```

Compile and run an example:

```powershell
python -m compiler.main run examples\hello.nq
```

Run the AI-friendliness audit:

```powershell
python scripts/run_ai_audit.py
```

Emit a machine-readable review summary:

```powershell
python -m compiler.main review examples\review_contracts.nq
```

Run the current stage1 selfhost front end:

```powershell
python -m compiler.main run selfhost\main.nq
```

## Key Docs

- [RESEARCH_MEMO.md](RESEARCH_MEMO.md)
- [SPEC.md](SPEC.md)
- [GRAMMAR.md](GRAMMAR.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [ROADMAP.md](ROADMAP.md)
- [DECISIONS.md](DECISIONS.md)
- [RISKS.md](RISKS.md)
- [DEFERRED.md](DEFERRED.md)
- [AI_AUDIT.md](AI_AUDIT.md)
- [AI_CONTRACTS.md](AI_CONTRACTS.md)
- [BOOTSTRAP_STAGE1.md](BOOTSTRAP_STAGE1.md)

## Repository Notes

- The current compiler is a Python bootstrap because this workspace did not provide a Rust toolchain.
- The long-term implementation preference remains Rust.
- The language surface is still intentionally small, but bootstrap-critical stage1 features are now active: imports, file input, and builtin `list<T>`.
