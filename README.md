# Nauqtype

Nauqtype is a small compiled language designed for AI-authored software under human supervision.

Current bootstrap status:

- single-file compile units
- explicit types at function boundaries
- nominal `type` and `enum`
- `option<T>` and `result<T, E>`
- explicit `match`
- minimal move / borrow checking
- compile-to-C backend with a tiny runtime
- Python bootstrap compiler in the current workspace

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

## Repository Notes

- The current compiler is a Python bootstrap because this workspace did not provide a Rust toolchain.
- The long-term implementation preference remains Rust.
- The v0.1 language surface is intentionally small and frozen during the current hardening phase.

