# WSL Development Contract

Status: reviewed 2026-10-31. WSL2 is the supported native-Linux verification
host for this checkout's executable gates. Earlier text granting Kimi Code WSL
access for library integration is retired with that lane; see
[docs/history/COORDINATION_LEDGER_2026-10.md](docs/history/COORDINATION_LEDGER_2026-10.md).

## Environment

Ubuntu 24.04 under WSL2, with a non-root default user, native ext4 home
storage, `/usr/bin/cc` as GCC 13.3.0, Git, GNU `time`, and GNU `timeout`.
Windows-hosted agents owned by the same user invoke it locally through
`wsl.exe`. This is local process access only: no SSH server, credentials,
relay access, privileged shares, or remote grants are implied. The P0
performance baseline and later gates were measured on this host; see
`PERFORMANCE_BASELINE.md`.

## Verification Boundary

- Run builds and gates on the Linux filesystem, not on a mounted Windows path.
  Use an ext4 clone or worktree of the candidate, owned by the lead for the
  task's duration.
- Bring the reviewed result back to the canonical checkout and compare trees
  before committing. The ext4 copy is a disposable snapshot, not a source of
  truth.
- Preserve pinned `workspace-lock` and source provenance in every capture.
- Do not make uncontrolled edits to the canonical checkout from inside WSL.
- A Windows-side edit or static check is not Linux evidence; follow
  [LINUX.md](LINUX.md) and [VERIFICATION.md](VERIFICATION.md).

Machine-specific paths and commands belong in untracked local configuration,
not in this file.
