# Nauqtype Local Workspace Lock v1

M44 adds local dependencies without adding registry resolution, network fetching, package scripts, or an environment-dependent search path.

## Manifest Form

```json
{
  "version": "workspace/v1",
  "workspace": { "name": "acme.tools", "source_roots": ["src"] },
  "dependencies": [
    { "alias": "reporting", "path": "../reporting", "workspace": "acme.reporting" }
  ]
}
```

- `alias` is the only source-visible dependency root: `use reporting::render;`.
- `path` is local, relative to the declaring manifest, and must name a directory containing `nauqtype.workspace.json`.
- `workspace` must equal the dependency manifest's declared workspace identity.
- Duplicate aliases, duplicate canonical paths, parent escapes outside an explicit local path, missing manifests, and identity mismatches fail closed.

## Lock Form

The checked lock file is `nauqtype.workspace.lock.json`:

```json
{
  "version": "workspace-lock/v1",
  "workspace": "acme.tools",
  "dependencies": [
    {
      "alias": "reporting",
      "workspace": "acme.reporting",
      "path": "../reporting",
      "manifest_sha256": "<sha256>",
      "source_sha256": "<sha256>"
    }
  ]
}
```

The lock is deterministic: entries are ordered by alias, paths retain their manifest spelling, and source hashes cover the dependency's declared source roots in canonical module-path order. A stale or missing lock is a diagnostic, never a reason to fetch or silently refresh code.

## Evidence

- Facts records dependency aliases as declared references and resolved dependency modules as checked references.
- Review/change-report surface affected dependency identities and lock changes.
- Policy targets use canonical `workspace:<name>::module:<path>` identities; an alias is source spelling only.
- Refactor plans may rename symbols across locked local dependencies but do not rewrite manifests or locks in v1.

## Explicit Deferrals

- Registries, URL dependencies, transitive solver behavior, version ranges, package scripts, and automatic lock updates.
- Network access and hidden package caches.
- Cross-workspace visibility inference or implicit re-export.
