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
- `path` uses canonical forward-slash spelling: no absolute paths, backslashes, duplicate separators, `.` segments, or interior `..` segments. Leading `../` segments remain explicit and allowed.
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

The lock is deterministic: entries are ordered by alias, paths retain their manifest spelling, and source hashes cover the dependency's single declared source root in canonical module-path order. On the Linux host contract, the compiler recomputes the source hash with:

```sh
find "$source_root" -type f -name '*.nq' -print0 | sort -z | xargs -0 cat | sha256sum
```

It recomputes `manifest_sha256` with `sha256sum <dependency>/nauqtype.workspace.json`. This requires the standard Linux `sh`, `find`, `sort`, `xargs`, `cat`, and `sha256sum` tools already used by the bootstrap/release environment. A stale or missing lock is a diagnostic, never a reason to fetch or silently refresh code.

The stage1 loader validates, before loading a dependency:

- root workspace identity and `workspace-lock/v1` version
- unique declared aliases and paths
- matching alias, path, and workspace identity in the lock
- valid lowercase SHA-256 fields
- dependency manifest identity and source root
- recomputed manifest and source-root hashes

The source-visible alias is the dependency's import root. For example, `use reporting::render;` loads `vendor/reporting/src/render.nq`; an internal dependency import uses the same explicit root, such as `use reporting::model;`.

## Evidence

- M44 facts retain the checked alias-rooted module graph, so imported dependency modules and call edges are visible without filesystem search.
- M45 adds workspace-qualified facts, review/change-report impact, and policy targets. Canonical `workspace:<name>::module:<path>` IDs are not claimed as implemented before that milestone.
- Refactor plans may rename symbols across locked local dependencies but do not rewrite manifests or locks in v1.

## Explicit Deferrals

- Registries, URL dependencies, transitive solver behavior, version ranges, package scripts, and automatic lock updates.
- Network access and hidden package caches.
- Cross-workspace visibility inference or implicit re-export.
