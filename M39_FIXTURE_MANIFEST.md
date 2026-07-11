# M39 Fixture Manifest

`tests/fixtures/m39_fixture_manifest.txt` is the checked migration ledger for the frozen Python suite inventory. It uses one of four coverage classes:

- `active-fixture`: deterministic `nauqc test` check, JSON, or supervision fixture.
- `active-corpus`: a formatter-gated emitted-C build/run corpus program.
- `active-proof`: the copied-selfhost structural proof that necessarily traverses the listed compiler boundary.
- `historical-reference`: retained Python implementation evidence that does not define an active compiler or release gate.

`future-seed` is reserved for the one bootstrap prerequisite that M40 must replace with the host-C seed proof. The Nauqtype runner checks the manifest header and every mapped suite name so neither a frozen suite nor its migration rationale can disappear silently.

This ledger is intentionally an observable-claim map, not a mechanical port of Python unit-test internals. The active gates are `nauqc test`, `nauqc prove`, the M40 seed proof, and the Linux release verification path.
