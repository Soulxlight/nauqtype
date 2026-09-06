# Nauqtype Local Workspace Lock v2

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
  "version": "workspace-lock/v2",
  "workspace": "acme.tools",
  "dependencies": [
    {
      "alias": "reporting",
      "workspace": "acme.reporting",
      "path": "../reporting",
      "manifest_sha256": "<sha256>",
      "legacy_source_sha256": "<sha256 of captured sorted contents>",
      "source_tree_format": "nauqtype-source-tree/v2",
      "source_tree_sha256": "<sha256 of framed captured tree>"
    }
  ]
}
```

Entries retain explicit manifest path spellings. The authoritative tree hash
frames the sorted relative path and exact captured content of every regular
`.nq`, including empty files. The byte encoding is fixed in
[M54_10_CONTRACTS.md](M54_10_CONTRACTS.md). Renaming an empty file changes
this identity even though the old concatenated-content checksum does not.

`manifest_sha256` hashes the captured dependency manifest bytes.
`legacy_source_sha256` hashes concatenated captured source bytes for old JSON
formats only; it is not authoritative dependency-change evidence. Hashing uses
the standard Linux `sha256sum` tool. A stale or missing lock is a diagnostic,
never a reason to fetch, silently refresh, or fall back to old hashing.

The stage1 loader validates, before loading a dependency:

- root workspace identity and `workspace-lock/v2` version
- unique declared aliases and paths
- matching alias, path, and workspace identity in the lock
- valid lowercase SHA-256 fields
- dependency manifest identity and source root
- recomputed manifest, legacy compatibility, and framed source-root hashes
- exact manifest/lock dependency membership and strict duplicate-key rejection
- regular source files only, with no symlink roots, ancestors, or descendants

The command captures dependency source text once. Module loading and evidence
use that validated capture rather than reopening original paths. Root source
loading remains unchanged. This is not a hostile concurrent-filesystem
transaction or a promise of descriptor-atomic capture. Transitive dependencies
remain rejected; direct local roots are the entire bounded contract.

Legacy `workspace-lock/v1` files are rejected with a migration diagnostic.
Consumers must explicitly produce v2 framing and pin the new lock with their
own source revision. NauqType updates only its owned fixtures; it does not
silently edit external library or AIML locks.

The source-visible alias is the dependency's import root. For example, `use reporting::render;` loads `vendor/reporting/src/render.nq`; an internal dependency import uses the same explicit root, such as `use reporting::model;`.

## Evidence

- M44 facts retain the checked alias-rooted module graph, so imported dependency modules and call edges are visible without filesystem search.
- Workspace-qualified facts, change impact, and policy targets use canonical
  `workspace:<name>::module:<path>` IDs.
- Facts v3 retains its validated legacy `source_sha256` compatibility field.
  Facts v4 exposes the explicit lock version and framed source identity.
- Change-report v1-v3 retain their prior comparison behavior. Use v4 for
  framed dependency-change evidence; it includes both captured dependency
  sets and does not base its decision on the legacy checksum.
- Refactor plans may rename symbols across locked local dependencies but do not rewrite manifests or locks in v1.

## Explicit Deferrals

- Registries, URL dependencies, transitive solver behavior, version ranges, package scripts, and automatic lock updates.
- Network access and hidden package caches.
- Cross-workspace visibility inference or implicit re-export.
