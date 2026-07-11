# Nauqtype Workspace Contract v1

Status: M42/M44 implementation contract. Manifest-derived nested module loading and locked local dependency routing are active; alias syntax and cross-package governance evidence remain staged work.

## Goal

A Nauqtype workspace must make dependency authority visible and reproducible. A module path resolves from one checked manifest, never from the caller's directory, an environment variable, a registry, or an unrecorded cache.

The canonical root manifest is `nauqtype.workspace.json`.

```json
{
  "version": "workspace/v1",
  "workspace": {
    "name": "acme.tools",
    "source_roots": ["src"],
    "entrypoints": { "tool": "app::main" }
  }
}
```

## Identity And Layout

- `workspace.name` is a dotted, lowercase identity used in evidence, locks, and policy. It is not source syntax.
- A module identity is `workspace:<name>::module:<segment>::...`.
- Module segments are ordinary Nauqtype identifiers. The module `app::main` maps deterministically to `src/app/main.nq`.
- Workspace v1 accepts exactly one `source_roots` entry. Multiple roots fail closed until their ordering and duplicate-module diagnostics have a dedicated design.
- An entrypoint is always named by a manifest key and a fully qualified local module path. There is no implicit `main.nq` selection in manifest mode.

## Source Form

```nauq
use app::render;

fn main() -> i32 {
    return app::render::status();
}
```

- M42 implements manifest-derived nested entry modules and source-root loading while retaining the existing bare `use helper;` spelling for imported names. M43 adds absolute multi-segment `use` paths; direct qualified function calls are active.
- `as` import aliases remain deferred. A M44 dependency's manifest alias is the only currently active alias form, for example `use reporting::render;`.
- `::` denotes module provenance only. `.` remains field access; it never triggers method lookup or module traversal.
- Qualified values, types, enums, variants, and calls resolve through the same canonical module identity.
- No wildcard imports, relative imports, implicit re-exports, chained package discovery, or hidden prelude are allowed.

## Flat-Root Compatibility

Projects without `nauqtype.workspace.json` remain in legacy flat-root mode:

- `use helper;` resolves to `helper.nq` beside the workspace root as it does today.
- Multi-segment paths are rejected in flat-root mode rather than guessed.
- Manifest mode does not reinterpret bare `use helper;`; migration requires an explicit workspace manifest and path spelling update.

This makes migration visible in facts and diffs instead of silently changing an existing project’s dependency graph.

## Evidence And Governance Contract

- Facts currently retain checked module identities, including the explicit dependency alias root, while M45 upgrades these to canonical workspace/package/module IDs.
- Review, review-diff, change-report, policy-check, and refactor plans gain cross-package canonical-ID behavior only with M45; no filesystem-text fallback is permitted.
- M43 move/rename work remains dependent on complete cross-module references.
- [WORKSPACE_LOCK.md](WORKSPACE_LOCK.md) locks the M44 local dependency and deterministic lock-file contract. The manifest itself never fetches code.
- M45 extends ownership and policy checks across package boundaries; policy remains sidecar data, never hidden compiler authority.

## Representative Tool Checks

The contract was tested against the organizational shapes Nauqtype must support next:

| Tool shape | Required property | Contract result |
| --- | --- | --- |
| CLI with shared formatting library | one explicit entrypoint and a checked library path | `entrypoints.tool` and `use app::render` |
| Shared domain model used by two tools | type provenance remains visible at each use | `use app::model::Summary` |
| Supervised automation workspace | owner/reviewer policy can target stable code without cwd ambiguity | workspace-qualified semantic IDs |
| Local internal dependency | source origin is explicit and lockable without a registry | M44 `path` dependency plus source hash |

## Explicit Deferrals

- Remote registries, network fetching, package scripts, version solvers, and implicit caches.
- Relative imports, wildcard imports, automatic re-exports, and prelude modules.
- Methods, member calls, package-qualified field syntax, or receiver rewriting.
- General nested package managers beyond the declared local-workspace graph.

## M42/M44 Acceptance

M42/M44 require manifest parsing, module mapping, flat-root rejection/migration diagnostics, nested facts, locked dependency routing, reproducible manifest/source hashes, and runnable nested/local-dependency fixtures to agree.
