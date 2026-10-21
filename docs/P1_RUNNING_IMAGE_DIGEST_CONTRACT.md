# P1 Kernel-Anchored Running-Image Digest

Status: measured experiment rejected. All ordinary interleaved cache-oracle
runs and protected readbacks pass, but before14.53/13.91s (mean14.22) versus
after12.86/12.90s (mean12.88) is9.42% lower, below the required15%. Repeat
spreads are4.46%/.31%. Experimental ELF sizes are6,230,256/6,230,264 bytes,
padded against the real6,230,184-byte producer; these are component probes,
not production compiler measurements. Only this experiment's unstaged NQ
delta was removed; the earlier staged literal-scan improvement is retained.
Captures and receipts remain in local ignored `image-digest-v1` evidence.

Proposed for independent Gate A. The complete warm tier is104.53s, still
above60s. The fixture cache repeatedly captures the running compiler's ELF
as bytes, converts it to text and sends it to a SHA child. This proposal
selects a bounded acquisition experiment, not an assumed speedup.

## Scope

Change only `selfhost/fixture_c.nq`. Replace only running-image acquisition;
ordinary C source/runtime/include/output and CC-file captures stay unchanged.
Keep the old running-image capture as a direct oracle. Do not memoize the
digest, alter the v2 frame, drop environment keys, reuse test results, add
a runtime primitive, or change process authority, deadlines or capture caps.

Read `/proc/self/stat` in the Nauqtype parent, not through a child. Accept
only a bounded canonical positive decimal PID prefix followed by ` (`.
Do not parse or trust its command-name suffix. Build exactly
`/proc/<that-PID>/exe`; never hash a child `/proc/self/exe`, argv0, guessed
PID or resolved launch-path image. The parent remains alive and blocked in
the existing bounded process wait until the child completes; a terminated
parent cannot publish a cache hit.

Keep fresh `/proc/self/exe` metadata before/after, requiring regular-image
shape and unchanged size/mode/mtime. Hash the computed kernel-image path
with the existing pipe-only `/usr/bin/sha256sum` helper, fixed argv and cap.
Require zero exit, empty stderr, no timeout/cancellation, and the exact
lowercase64-hex plus two spaces plus computed path plus LF output. A failed
PID read, permission check, provider, decode or metadata confirmation
declines reuse; never fall back to a launch-path hash or change permissions.

Linux access to another process's `/proc/PID/exe` can be stricter than its
own self link (ptrace credential/dumpability/LSM checks). That is a disclosed
reuse limitation, not permission to weaken policy. Keep the existing fresh
compile fallback and receipt cleanup behavior.

Return a digest-only `fixture_c_identity`, not a successful file capture
with invented empty text. The existing replacement probe must obtain its
needed image size from actual metadata. Keep original producer path checks,
frame fields, all confirmations, locks and publication/readbacks unchanged.

## Evidence

Add bounded PID/output-decoder negative cases and direct same-running-image
old/new digest agreement to the existing cache oracle. Keep the actual
owned atomic A-to-B launch-path replacement check: old running A continues
to hash A; newly executed B has B identity. Preserve existing failure,
malformed output, cancellation and file/drift checks. Distinguish synthetic
decoder fault cases from real filesystem/process evidence.

The lead reviews and measures a component before accepting complexity:
ordinary interleaved old/new/new/old cache-oracle comparisons with exact
behavior/readbacks, fixed runtime/CC/flags, and producer-size disclosure.
An explicitly padded experimental ELF may assess representative byte volume;
do not call it the production compiler. Require >=15% lower mean component
wall with <=10% repeat spread, otherwise drop only this experiment.

Both independent Gate A reviews are required before edits. Trailing mixed
reviews, a legitimate current compiler, full warm measurement, exact seed
propagation and one final frozen gate remain separate requirements. No
component observation closes the strict60s goal or unblocks M56.
