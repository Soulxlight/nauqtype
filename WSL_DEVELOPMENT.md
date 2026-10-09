# WSL Development Contract

Status: base WSL environment and the specific compiler P0 baseline verified
2026-09-30; optimization acceptance and library integration remain pending.
This document authorizes bounded local Kimi Code
access for library integration, not changes to project ownership or checkouts.

## Local Access Boundary

Windows-hosted Codex and Kimi processes owned by the same user may invoke the
same Ubuntu distro through `wsl.exe`. This is local process access, not a new
network boundary. It does not provide an SSH server, credentials, relay-to-PC
access, privileged shares, or remote grants.

Local WSL work and the Rachul relay are separate environments. Relay access
does not grant access to this PC or to another owner's checkout. The existing
[AGENT_ROUTING.md](AGENT_ROUTING.md) remains authoritative for task fit and
ownership.

## Current State

Windows has been rebooted. Ubuntu 24.04 runs under WSL2 with a non-root default
user (UID 1000), its native home on the Linux filesystem, `/usr/bin/cc` as GCC
13.3.0, Git 2.43.0, GNU `time`, and GNU `timeout` 9.4 available. The compiler
owner also verified one frozen native-ext4 candidate and its checked stage1
cache, seven-phase cold gate, and repeatable full-tree check baseline on
2026-09-30; see `PERFORMANCE_BASELINE.md`. This is baseline evidence, not
speedup acceptance or a library gate. Kimi previously
verified Windows-side `wsl.exe` version access only; her own Ubuntu smoke check
is still pending. Kimi's access/version checks alone are not compiler or
library integration evidence; they are separate from the compiler P0 result.

Kimi's earlier Windows-side check ran only `wsl.exe --version` in its normal
shell and reported WSL2.7.14.0 with kernel 6.18.33.2-2. This confirms
Windows-side `wsl.exe` access/version only, not Ubuntu, compiler, or integration
access. No permissions, global config, credentials, SSH server, or
adjacent-repository changes occurred.

## Verification Boundary

Existing user authorization for local compiler setup and Kimi WSL access
remains in force. Before project verification, each participant confirms
access from its existing app and uses an owner-controlled native-Linux-filesystem
snapshot or worktree: the compiler owner controls NauqType and its cache; the
library owner controls NQType Libraries. Preserve pinned `workspace-lock` and
source provenance in every capture. The compiler owner's verification does
not grant access to or authority over the library checkout, and vice versa.

Do not make uncontrolled edits to golden Windows checkouts. Do not treat the
missing NQType AI/ML workspace as recovered; it remains unavailable until its
owner recreates and evidences it under the coordination rules.

## Kimi Library Integration

Kimi uses the compiler build, cache, and provenance contracts plus a read-only
compiler dependency pin. Library changes require explicit authorization from
the NQType Libraries owner; this document does not transfer compiler or
library ownership.

Confirm Linux access separately from compiler compatibility: each participant
first checks the selected distro and Linux user, then the same compiler
version and identity. Library integration is evidenced only after its checks
pass against the source checkout and copied release. The exact commands and
identities belong in the owner handoff; no result is implied here.

This is a bounded access and verification contract. Only the specific compiler
baseline linked above has passed its gate; library integration is not implied.
Do not add shell aliases or other integration
implementation under this document. Follow [LINUX.md](LINUX.md) and
[NAUQTYPE_COORDINATION.md](NAUQTYPE_COORDINATION.md).
