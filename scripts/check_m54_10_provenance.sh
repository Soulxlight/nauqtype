#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
phase_only=false
publication_only=false
case "${1:-}" in
    '') (( $# == 0 )) || exit 2;;
    --seed-phases-only) (( $# == 1 )) || exit 2; phase_only=true;;
    --seed-publication-only) (( $# == 1 )) || exit 2; publication_only=true;;
    *) printf 'Usage: scripts/check_m54_10_provenance.sh [--seed-phases-only|--seed-publication-only]\n' >&2; exit 2;;
esac
source "$script_dir/provenance.sh"
source "$script_dir/seed_manifest.sh"
scratch=$(mktemp -d -t nauqtype-provenance-tests-XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
export NQ_TEST_STATE="$scratch/state" NQ_TEST_LOG="$scratch/log"
export NQ_TEST_DRIVER="$repo_root/tests/fixtures/m54_10_provenance/driver.sh"
mkdir -p "$NQ_TEST_STATE"
cp "$repo_root/tests/fixtures/m54_10_provenance/cc.sh" "$scratch/cc"
chmod +x "$scratch/cc"
export CC="$scratch/cc"
passed=0

reject() {
    local name=$1
    shift
    if "$@" > "$scratch/reject-log" 2>&1; then printf 'FAIL accepted: %s\n' "$name" >&2; exit 1; fi
    passed=$((passed + 1))
}

assert_equal() {
    [[ "$1" == "$2" ]] || { printf 'FAIL %s: %s != %s\n' "$3" "$1" "$2" >&2; exit 1; }
    passed=$((passed + 1))
}

seal_checksums() {
    local root=$1 path
    seed_checksum_paths "$root" > "$scratch/checksum-paths"
    : > "$root/bootstrap/seed/SHA256SUMS"
    while IFS= read -r path; do
        printf '%s  %s\n' "$(prov_sha256 "$root/$path")" "$path" >> "$root/bootstrap/seed/SHA256SUMS"
    done < "$scratch/checksum-paths"
}

make_fixture() {
    local root=$1 path key value scalar comma hash inventory_hash tree_hash flags_hash
    mkdir -p "$root/scripts" "$root/selfhost" "$root/stdlib" "$root/bootstrap/seed/source-snapshot/selfhost"
    prov_producer_scripts > "$scratch/scripts"
    printf 'scripts/check_seed_bootstrap.sh\n' >> "$scratch/scripts"
    while IFS= read -r path; do cp --preserve=mode "$repo_root/$path" "$root/$path"; done < "$scratch/scripts"
    printf 'fixture-version\n' > "$root/VERSION"
    printf 'synthetic source C bytes\n' > "$root/selfhost/main.nq"
    : > "$root/selfhost/empty.nq"
    cp "$root/selfhost/"*.nq "$root/bootstrap/seed/source-snapshot/selfhost/"
    cp "$root/selfhost/main.nq" "$root/bootstrap/seed/nauqc-seed.c"
    printf 'pinned-runtime-c\n' > "$root/bootstrap/seed/runtime.c"
    printf 'pinned-runtime-h\n' > "$root/bootstrap/seed/runtime.h"
    printf 'current-runtime-c\n' > "$root/stdlib/runtime.c"
    printf 'current-runtime-h\n' > "$root/stdlib/runtime.h"
    printf '%s\0' -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib build/generator.c stdlib/runtime.c -o build/generator > "$root/bootstrap/seed/generator-flags.txt"
    seed_source_inventory "$root/bootstrap/seed/source-snapshot" > "$root/bootstrap/seed/source-inventory-v1.txt"
    inventory_hash=$(prov_sha256 "$root/bootstrap/seed/source-inventory-v1.txt")
    tree_hash=$(seed_source_tree_sha256 "$root/bootstrap/seed/source-snapshot")
    flags_hash=$(prov_sha256 "$root/bootstrap/seed/generator-flags.txt")
    hash=$(prov_sha256 "$root/bootstrap/seed/nauqc-seed.c")
    seed_manifest_fields > "$scratch/fields"
    printf '{\n' > "$root/bootstrap/seed/manifest.json"
    while IFS= read -r key; do
        scalar=''
        case "$key" in
            version) value=nauqtype-c-seed/v2;;
            source_entry) value=selfhost/main.nq;;
            source_tree_format) value=nauqtype-selfhost-source/v1;;
            source_tree_sha256) value=$tree_hash;;
            source_inventory_sha256) value=$inventory_hash;;
            source_base_revision) scalar=null;;
            source_index_tree) value=1111111111111111111111111111111111111111;;
            source_dirty) scalar=true;;
            runtime_c_sha256) value=$(prov_sha256 "$root/bootstrap/seed/runtime.c");;
            runtime_h_sha256) value=$(prov_sha256 "$root/bootstrap/seed/runtime.h");;
            generator_flags_sha256) value=$flags_hash;;
            generator_cc_target) value=fixture-linux;;
            *) value=$hash;;
        esac
        [[ -n "$scalar" ]] || scalar="\"$value\""
        comma=,
        [[ "$key" != generator_flags_sha256 ]] || comma=''
        printf '  "%s": %s%s\n' "$key" "$scalar" "$comma" >> "$root/bootstrap/seed/manifest.json"
    done < "$scratch/fields"
    printf '}\n' >> "$root/bootstrap/seed/manifest.json"
    seal_checksums "$root"
}

check_seed_publication() {
    local mode root code expected command_code fail_at
    root="$scratch/publication-setup-failure"
    mkdir -p "$root/build/seed" "$root/build/verification"
    printf 'stale receipt\n' > "$root/build/seed/seed-bootstrap-proof-v1.txt"
    printf 'stale success\n' > "$root/build/verification/seed-bootstrap-phases-v1.json"
    (
        repo_root="$root"
        mkdir() { return 1; }
        eval "$(sed -n '/^report=/,/^phase_tmp=/p' "$script_dir/check_seed_bootstrap.sh")"
    ) > "$root/output" 2>&1 &
    if wait "$!"; then code=0; else code=$?; fi
    assert_equal "$code" 1 'setup mkdir failure'
    [[ ! -e "$root/build/seed/seed-bootstrap-proof-v1.txt" ]]
    [[ ! -e "$root/build/verification/seed-bootstrap-phases-v1.json" ]]
    passed=$((passed + 1))
    printf 'PASS setup failure invalidates stale publication\n'

    for mode in command7 command124 command0 final-failure final-success final-term final-term-late write-{1..8}; do
        root="$scratch/publication-$mode"
        mkdir -p "$root"
        (
            # Exercise production functions, faulting only shell commands at
            # the publication boundary rather than copying their logic.
            eval "$(sed -n '/^write_phase_report() {$/,/^}$/p' "$repo_root/scripts/check_seed_bootstrap.sh")"
            eval "$(sed -n '/^on_seed_exit() {$/,/^}$/p' "$repo_root/scripts/check_seed_bootstrap.sh")"
            eval "$(sed -n '/^run_seed_phase() {$/,/^}$/p' "$repo_root/scripts/check_seed_bootstrap.sh")"
            phase_ids=(historical_compare stage2_emit current_compare)
            phase_status=(not_run not_run not_run)
            phase_wall=(null null null); phase_code=(null null null)
            phase_active=-1; phase_started=0; phase_boundary=setup
            phase_overall=running; phase_signal=""; inputs_hash=""; work_dir=""
            snapshot="$root"; report="$root/receipt"; phase_report="$root/phases.json"
            phase_tmp="$root/temporary"; writes=0; printf_calls=0; fail_at=${mode#write-}
            trap on_seed_exit EXIT
            printf() {
                if [[ "$mode" == write-* && "$phase_overall" == ok ]]; then
                    printf_calls=$((printf_calls + 1))
                    if (( printf_calls == fail_at )); then
                        builtin printf "$@"
                        return 1
                    fi
                fi
                builtin printf "$@"
            }
            mv() {
                writes=$((writes + 1))
                if [[ "$mode" == command* && "$writes" -ge 2 ]] || [[ "$mode" == final-failure && "$phase_overall" == ok ]]; then
                    command printf 'observed_command_exit=%s\n' "${phase_code[1]}" >> "$root/witness"
                    if [[ -f "$report" ]]; then command printf 'receipt_present_at_failure\n' >> "$root/witness"; fi
                    return 1
                fi
                if [[ "$mode" == final-term && "$phase_overall" == ok ]]; then
                    [[ -f "$report" ]] && command printf 'receipt_present_at_signal\n' > "$root/witness"
                    kill -TERM "$BASHPID"
                fi
                command mv "$@"
            }
            rm() {
                if [[ "$mode" == final-term-late && "${*: -1}" == "$phase_tmp" ]]; then
                    [[ -f "$report" && -f "$phase_report" ]] && command printf 'receipt_and_sidecar_present_at_signal\n' > "$root/witness"
                    kill -TERM "$BASHPID"
                fi
                command rm "$@"
            }
            case "$mode" in
                command*)
                    command_code=${mode#command}
                    run_seed_phase 1 bash -c 'exit "$1"' _ "$command_code"
                    printf 'unexpected later phase\n' > "$root/later";;
                final-*)
                    phase_status=(ok ok ok); phase_wall=(1 1 1); phase_code=(0 0 0)
                    phase_boundary=provenance
                    write_phase_report
                    # Match production ordering: receipt first, final sidecar
                    # in EXIT. The fault witness proves receipt publication.
                    printf 'successful receipt\n' > "$report"
                    phase_boundary=complete; phase_overall=ok;;
                write-*)
                    phase_status=(ok ok ok); phase_wall=(1 1 1); phase_code=(0 0 0)
                    phase_boundary=provenance
                    write_phase_report
                    printf 'successful receipt\n' > "$report"
                    phase_boundary=complete; phase_overall=ok;;
            esac
        ) > "$root/output" 2>&1 &
        # Keep errexit active inside the child; a conditional subshell would
        # otherwise suppress the production function's failure behavior.
        if wait "$!"; then code=0; else code=$?; fi
        case "$mode" in
            command7) expected=7;; command124) expected=124;;
            command0|final-failure) expected=1;; final-success) expected=0;;
            final-term|final-term-late) expected=143;; write-*) expected=1;;
        esac
        assert_equal "$code" "$expected" "$mode publication status"
        [[ ! -e "$root/later" ]]
        if [[ "$mode" == final-success ]]; then
            [[ -f "$root/receipt" ]]
            grep -Fqx '  "status": "ok",' "$root/phases.json"
        elif [[ "$mode" == final-term ]]; then
            [[ ! -e "$root/receipt" ]]
            grep -Fqx '  "status": "interrupted",' "$root/phases.json"
            grep -Fqx '  "termination_signal": "TERM",' "$root/phases.json"
        elif [[ "$mode" == final-term-late ]]; then
            [[ ! -e "$root/receipt" && ! -e "$root/phases.json" ]]
        else
            [[ ! -e "$root/receipt" ]]
            grep -Fqx '  "status": "running",' "$root/phases.json"
        fi
        case "$mode" in
            command*) grep -qx "observed_command_exit=${mode#command}" "$root/witness";;
            final-failure) grep -qx 'receipt_present_at_failure' "$root/witness";;
            final-term) grep -qx 'receipt_present_at_signal' "$root/witness";;
            final-term-late) grep -qx 'receipt_and_sidecar_present_at_signal' "$root/witness";;
        esac
        passed=$((passed + 1))
        printf 'PASS %s preserves results and receipt truth\n' "$mode"
    done
}

if [[ "$publication_only" == true ]]; then
    check_seed_publication
    printf 'seed publication fixtures passed (%s assertions; extracted production code, fault-injected shell commands)\n' "$passed"
    exit 0
fi

check_seed_phases() {
    local root="$scratch/phase-fixture" evidence log phase index code pattern label
    make_fixture "$root"
    export NQ_TEST_ROOT="$root"
    : > "$NQ_TEST_LOG"
    bash "$root/scripts/build_stage1_from_seed.sh" >/dev/null
    evidence="$root/build/verification/seed-bootstrap-phases-v1.json"
    log="$scratch/phase-output"

    assert_phase() {
        local id=$1 status=$2 result=$3 wall='[0-9]+'
        [[ "$status" != not_run ]] || wall=null
        grep -Eq "^    \{\"id\": \"$id\", \"status\": \"$status\", \"wall_seconds\": $wall, \"command_exit_code\": $result\},?$" "$evidence" || {
            printf 'FAIL phase %s expected %s/%s\n' "$id" "$status" "$result" >&2; cat "$evidence" >&2; exit 1;
        }
        passed=$((passed + 1))
    }
    assert_overall() {
        grep -Fqx "  \"status\": \"$1\"," "$evidence"
        grep -Fqx "  \"active_phase\": \"$2\"," "$evidence"
        grep -Fqx "  \"exit_code\": $3," "$evidence"
        passed=$((passed + 1))
    }

    # No real compiler: the fixture CC copies the synthetic driver.
    : > "$NQ_TEST_LOG"
    bash "$root/scripts/check_seed_bootstrap.sh" --reuse-stage1 > "$log"
    assert_overall ok complete 0
    for phase in historical_compare stage2_emit current_compare; do assert_phase "$phase" ok 0; done
    assert_equal "$(grep -c '^compare$' "$NQ_TEST_LOG")" 2 'timed direct comparison edges'
    grep -qx 'historical_c_equal=true' "$root/build/seed/seed-bootstrap-proof-v1.txt"
    grep -qx 'current_c_equal=true' "$root/build/seed/seed-bootstrap-proof-v1.txt"
    grep -Fqx '  "wall_seconds_resolution": 1,' "$evidence"
    grep -Eq '^  "inputs_sha256": "[0-9a-f]{64}",$' "$evidence"
    printf 'PASS seed phase success and original proof receipt\n'

    for index in 0 1 2; do
        phase=(historical_compare stage2_emit current_compare)
        : > "$NQ_TEST_LOG"
        if NQ_TEST_PHASE="${phase[$index]}" NQ_TEST_PHASE_ACTION=fail bash "$root/scripts/check_seed_bootstrap.sh" --reuse-stage1 > "$log" 2>&1; then code=0; else code=$?; fi
        assert_equal "$code" 7 "${phase[$index]} preserves command failure"
        assert_overall failed "${phase[$index]}" 7
        for label in 0 1 2; do
            if (( label < index )); then assert_phase "${phase[$label]}" ok 0
            elif (( label == index )); then assert_phase "${phase[$label]}" failed 7
            else assert_phase "${phase[$label]}" not_run null; fi
        done
        [[ ! -e "$root/build/seed/seed-bootstrap-proof-v1.txt" ]]
        # Exactly the reached commands ran, including the failing command.
        assert_equal "$(grep -Ec '^compare$|^emit:build/seed/stage2.c$' "$NQ_TEST_LOG")" "$((index + 1))" 'no later phase executed'
        printf 'PASS failure in %s and unreached phases\n' "${phase[$index]}"
    done

    if NQ_TEST_PHASE=stage2_emit NQ_TEST_PHASE_ACTION=exit124 bash "$root/scripts/check_seed_bootstrap.sh" --reuse-stage1 > "$log" 2>&1; then code=0; else code=$?; fi
    assert_equal "$code" 124 'command exit 124 preserved'
    assert_overall failed stage2_emit 124
    assert_phase stage2_emit failed 124
    grep -Fqx '  "termination_signal": null,' "$evidence"
    printf 'PASS command exit 124 is not asserted to be a timeout\n'

    # All phase commands succeed, but captured-source tampering still fails the
    # original final provenance check and never publishes a successful receipt.
    if NQ_TEST_PHASE=current_compare NQ_TEST_PHASE_ACTION=mutate bash "$root/scripts/check_seed_bootstrap.sh" --reuse-stage1 > "$log" 2>&1; then code=0; else code=$?; fi
    assert_equal "$code" 1 'post-phase provenance failure preserved'
    assert_overall failed provenance 1
    for phase in historical_compare stage2_emit current_compare; do assert_phase "$phase" ok 0; done
    [[ ! -e "$root/build/seed/seed-bootstrap-proof-v1.txt" ]]
    printf 'PASS completed phases do not imply bootstrap provenance success\n'

    # Exercise the same process-group TERM behavior as run_budgeted.sh. The
    # aggregate timeout owns exit 124; the sidecar reports observed interruption.
    : > "$NQ_TEST_LOG"
    if NQ_TEST_PHASE=stage2_emit NQ_TEST_PHASE_ACTION=block timeout --signal=TERM --kill-after=3s 30s bash "$root/scripts/check_seed_bootstrap.sh" --reuse-stage1 > "$log" 2>&1; then code=0; else code=$?; fi
    assert_equal "$code" 124 'external GNU timeout exit'
    grep -qx 'phase-blocked:stage2_emit' "$NQ_TEST_LOG"
    assert_overall interrupted stage2_emit 143
    assert_phase historical_compare ok 0
    assert_phase stage2_emit interrupted null
    assert_phase current_compare not_run null
    grep -Fqx '  "termination_signal": "TERM",' "$evidence"
    [[ ! -e "$root/build/seed/seed-bootstrap-proof-v1.txt" ]]
    printf 'PASS external timeout retains completed and interrupted phase evidence\n'

    # Fresh success replaces interruption; an early failure then replaces that
    # success with all phases unreached, even though the previous file existed.
    bash "$root/scripts/check_seed_bootstrap.sh" --reuse-stage1 > "$log"
    assert_overall ok complete 0
    cp "$root/bootstrap/seed/SHA256SUMS" "$scratch/phase-checksums"
    printf 'tampered\n' >> "$root/bootstrap/seed/nauqc-seed.c"
    if bash "$root/scripts/check_seed_bootstrap.sh" --reuse-stage1 > "$log" 2>&1; then code=0; else code=$?; fi
    assert_equal "$code" 1 'early seed verification failure'
    assert_overall failed setup 1
    for phase in historical_compare stage2_emit current_compare; do assert_phase "$phase" not_run null; done
    [[ ! -e "$root/build/seed/seed-bootstrap-proof-v1.txt" ]]
    printf 'PASS stale success/interruption replaced and early failure stays unreached\n'

    cp "$root/bootstrap/seed/source-snapshot/selfhost/main.nq" "$root/bootstrap/seed/nauqc-seed.c"
    if NQ_TEST_PHASE=current_compare NQ_TEST_PHASE_ACTION=evidence-dir bash "$root/scripts/check_seed_bootstrap.sh" --reuse-stage1 > "$log" 2>&1; then code=0; else code=$?; fi
    assert_equal "$code" 1 'evidence publication failure cannot pass'
    [[ ! -e "$root/build/seed/seed-bootstrap-proof-v1.txt" ]]
    printf 'PASS atomic evidence publication rejects a directory target\n'
    check_seed_publication
}

if [[ "$phase_only" == true ]]; then
    check_seed_phases
    printf 'seed bootstrap phase fixtures passed (%s assertions; synthetic CC/driver only)\n' "$passed"
    exit 0
fi

fixture="$scratch/fixture"
make_fixture "$fixture"
export NQ_TEST_ROOT="$fixture"
seed_verify "$fixture"
printf 'PASS canonical synthetic seed v2\n'

# Canonical bytes, not a permissive JSON extractor or checksum-line consumer.
cp "$fixture/bootstrap/seed/manifest.json" "$scratch/manifest-good"
for kind in duplicate unknown reordered missing whitespace cr nul version incoherent; do
    cp "$scratch/manifest-good" "$fixture/bootstrap/seed/manifest.json"
    case "$kind" in
        duplicate) sed -i '2p' "$fixture/bootstrap/seed/manifest.json";;
        unknown) sed -i '2s/version/unknown/' "$fixture/bootstrap/seed/manifest.json";;
        reordered) sed -i '2{h;d;};3{p;g;}' "$fixture/bootstrap/seed/manifest.json";;
        missing) sed -i '2d' "$fixture/bootstrap/seed/manifest.json";;
        whitespace) sed -i '2s/  / /' "$fixture/bootstrap/seed/manifest.json";;
        cr) sed -i 's/$/\r/' "$fixture/bootstrap/seed/manifest.json";;
        nul) printf '\0' >> "$fixture/bootstrap/seed/manifest.json";;
        version) sed -i 's@nauqtype-c-seed/v2@nauqtype-c-seed/v1@' "$fixture/bootstrap/seed/manifest.json";;
        incoherent) sed -i 's/"generator_input_c_sha256": "./"generator_input_c_sha256": "0/' "$fixture/bootstrap/seed/manifest.json";;
    esac
    seal_checksums "$fixture"
    reject "manifest $kind" seed_verify "$fixture"
done
cp "$scratch/manifest-good" "$fixture/bootstrap/seed/manifest.json"
seal_checksums "$fixture"
for path in nauqc-seed.c runtime.c runtime.h source-inventory-v1.txt generator-flags.txt source-snapshot/selfhost/main.nq; do
    cp "$fixture/bootstrap/seed/$path" "$scratch/material-good"
    printf 'tamper\n' >> "$fixture/bootstrap/seed/$path"
    reject "material $path" seed_verify "$fixture"
    cp "$scratch/material-good" "$fixture/bootstrap/seed/$path"
done
cp "$fixture/bootstrap/seed/SHA256SUMS" "$scratch/sums-good"
for kind in missing duplicate traversal order; do
    cp "$scratch/sums-good" "$fixture/bootstrap/seed/SHA256SUMS"
    case "$kind" in
        missing) sed -i '1d' "$fixture/bootstrap/seed/SHA256SUMS";;
        duplicate) sed -i '1p' "$fixture/bootstrap/seed/SHA256SUMS";;
        traversal) sed -i '1s@bootstrap/@../bootstrap/@' "$fixture/bootstrap/seed/SHA256SUMS";;
        order) LC_ALL=C sort -r "$scratch/sums-good" > "$fixture/bootstrap/seed/SHA256SUMS";;
    esac
    reject "checksum set $kind" seed_verify "$fixture"
done
cp "$scratch/sums-good" "$fixture/bootstrap/seed/SHA256SUMS"
source_dir="$fixture/bootstrap/seed/source-snapshot/selfhost"
for kind in extra symlink directory-symlink fifo missing mode unreadable unsafe; do
    case "$kind" in
        extra) printf 'x' > "$source_dir/extra.txt";;
        symlink) ln -s main.nq "$source_dir/link.nq";;
        directory-symlink) ln -s selfhost "$fixture/bootstrap/seed/source-snapshot/link";;
        fifo) mkfifo "$source_dir/special.nq";;
        missing) mv "$source_dir/empty.nq" "$scratch/empty";;
        mode) chmod +x "$source_dir/main.nq";;
        unreadable) chmod 000 "$source_dir/main.nq";;
        unsafe) touch "$source_dir/"$'bad\nname.nq';;
    esac
    reject "snapshot $kind" seed_verify "$fixture"
    rm -f "$source_dir/extra.txt" "$source_dir/link.nq" "$source_dir/special.nq" "$fixture/bootstrap/seed/source-snapshot/link" "$source_dir/"$'bad\nname.nq'
    if [[ -e "$scratch/empty" ]]; then mv "$scratch/empty" "$source_dir/empty.nq"; fi
    chmod 644 "$source_dir/main.nq"
done
seed_verify "$fixture"
printf 'PASS seed parser, inventory, allowlist, and tamper rejection\n'

for metadata in nauqtype.workspace.json nauqtype.workspace.lock.json selfhost/nauqtype.workspace.json selfhost/nauqtype.workspace.lock.json; do
    printf '{}\n' > "$fixture/$metadata"
    reject "flat loading $metadata" prov_input_paths "$fixture"
    rm "$fixture/$metadata"
done
for metadata in nauqtype.workspace.json nauqtype.workspace.lock.json; do
    printf '{}\n' > "$scratch/$metadata"
    : > "$NQ_TEST_LOG"
    reject "ambient parent $metadata" bash "$fixture/scripts/build_stage1_from_seed.sh"
    [[ ! -s "$NQ_TEST_LOG" ]]
    rm "$scratch/$metadata"
done
printf 'PASS root/selfhost lock names and physical ancestor metadata rejection\n'

# Independently assemble a binary/empty-file frame, including lengths and mode.
mkdir "$scratch/framing"
printf 'x\0y\n' > "$scratch/framing/a"
: > "$scratch/framing/empty"
chmod 644 "$scratch/framing/a" "$scratch/framing/empty"
printf 'a\nempty\n' > "$scratch/frame-paths"
printf 'nauqtype-candidate/v1\nfiles:2\npath-bytes:1\na\nmode:100644\ncontent-bytes:4\nx\0y\n\npath-bytes:5\nempty\nmode:100644\ncontent-bytes:0\n\n' > "$scratch/frame-expected"
assert_equal "$(prov_files_digest "$scratch/framing" nauqtype-candidate/v1 "$scratch/frame-paths")" "$(prov_sha256 "$scratch/frame-expected")" 'exact raw byte frame'
printf 'a\na\n' > "$scratch/frame-bad-paths"
reject 'duplicate frame paths' prov_files_digest "$scratch/framing" nauqtype-candidate/v1 "$scratch/frame-bad-paths"
printf 'a' > "$scratch/frame-bad-paths"
reject 'unterminated frame path' prov_files_digest "$scratch/framing" nauqtype-candidate/v1 "$scratch/frame-bad-paths"
ln -s "$scratch/framing" "$scratch/frame-link"
reject 'frame symlink root' prov_files_digest "$scratch/frame-link" nauqtype-candidate/v1 "$scratch/frame-paths"
proof_expected=$(printf '%s\0' nauqtype-proof-options/v1 -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib | prov_hash_stream)
assert_equal "$(prov_proof_flags_sha256)" "$proof_expected" 'proof options exact NUL frame'
sed -n 's/^[[:space:]]*list_push(mutref cc_args, "\([^"]*\)");$/\1/p' "$repo_root/selfhost/host_c.nq" | head -n 4 > "$scratch/host-options"
printf '%s\n' -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib > "$scratch/expected-options"
cmp -s "$scratch/host-options" "$scratch/expected-options"
printf 'PASS exact binary file framing and host_c proof option policy\n'

: > "$NQ_TEST_LOG"
bash "$fixture/scripts/build_stage1_from_seed.sh" >/dev/null
bash "$fixture/scripts/stage1_cache.sh" require
cmp -s "$fixture/selfhost/main.nq" "$fixture/build/seed/stage1.c"
assert_equal "$(grep -c '^compile:' "$NQ_TEST_LOG")" 2 'pinned/current compilation route count'
reject 'record removed' bash "$fixture/scripts/stage1_cache.sh" record
for path in build/seed/stage1.c selfhost/build/nauqc build/seed/nauqc-seed build/seed/stage1-derivation-v1.txt build/seed/stage1-cache-v2.txt selfhost/main.nq VERSION stdlib/runtime.c stdlib/runtime.h scripts/provenance.sh; do
    cp --preserve=mode "$fixture/$path" "$scratch/cache-good"
    printf 'tamper\n' >> "$fixture/$path"
    reject "cache $path" bash "$fixture/scripts/stage1_cache.sh" check
    cp --preserve=mode "$scratch/cache-good" "$fixture/$path"
done
reject 'CC target changed' env NQ_TEST_TARGET=other-linux bash "$fixture/scripts/stage1_cache.sh" check
reject 'invalid CC target' env NQ_TEST_TARGET=$'bad\ntarget' bash "$fixture/scripts/stage1_cache.sh" check
cp "$CC" "$scratch/cc-other"
chmod +x "$scratch/cc-other"
reject 'CC path changed' env CC="$scratch/cc-other" bash "$fixture/scripts/stage1_cache.sh" check
printf '\n# changed CC bytes\n' >> "$CC"
reject 'CC bytes changed' bash "$fixture/scripts/stage1_cache.sh" check
cp "$repo_root/tests/fixtures/m54_10_provenance/cc.sh" "$CC"
chmod +x "$CC"
bash "$fixture/scripts/stage1_cache.sh" require

# Rebind the outer receipt hash: strict shape and recomputation must still win.
receipt="$fixture/build/seed/stage1-derivation-v1.txt"
cache_manifest="$fixture/build/seed/stage1-cache-v2.txt"
cp "$receipt" "$scratch/receipt-good"
cp "$cache_manifest" "$scratch/cache-manifest-good"
zero=0000000000000000000000000000000000000000000000000000000000000000
for kind in duplicate unknown missing reorder nul cc_path cc_sha256 cc_version_sha256 cc_target flags_sha256 inputs_sha256 seed_manifest_sha256 seed_exe_sha256; do
    cp "$scratch/receipt-good" "$receipt"
    case "$kind" in
        duplicate) sed -i '2p' "$receipt";;
        unknown) printf 'unknown=%s\n' "$zero" >> "$receipt";;
        missing) sed -i '2d' "$receipt";;
        reorder) sed -i '2{h;d;};3{p;g;}' "$receipt";;
        nul) printf '\0' >> "$receipt";;
        cc_path) sed -i 's@^cc_path=.*@cc_path=/not/the/compiler@' "$receipt";;
        cc_target) sed -i 's/^cc_target=.*/cc_target=other-linux/' "$receipt";;
        *) sed -i "s/^$kind=.*/$kind=$zero/" "$receipt";;
    esac
    sed "s/^derivation_sha256=.*/derivation_sha256=$(prov_sha256 "$receipt")/" "$scratch/cache-manifest-good" > "$cache_manifest"
    reject "rebound receipt $kind" bash "$fixture/scripts/stage1_cache.sh" check
done
cp "$scratch/receipt-good" "$receipt"
cp "$scratch/cache-manifest-good" "$cache_manifest"
bash "$fixture/scripts/stage1_cache.sh" require
printf 'PASS builder-only cache and recomputed input/toolchain/artifact identity\n'

cp "$fixture/selfhost/main.nq" "$scratch/cache-source-good"
reject 'source mutation during cache CC probe' env NQ_TEST_MUTATION=cache-source bash "$fixture/scripts/stage1_cache.sh" check
cp "$scratch/cache-source-good" "$fixture/selfhost/main.nq"
bash "$fixture/scripts/stage1_cache.sh" require
reject 'source mutation during initial builder CC probe' env NQ_TEST_MUTATION=cache-source bash "$fixture/scripts/build_stage1_from_seed.sh"
[[ ! -e "$fixture/build/seed/stage1-cache-v2.txt" ]]
cp "$scratch/cache-source-good" "$fixture/selfhost/main.nq"

# Mutations use the existing CC boundary; production has no test hook authority.
for mode in persistent restored toolchain fail; do
    cp "$fixture/selfhost/main.nq" "$scratch/current-source"
    if [[ "$mode" == restored ]]; then
        NQ_TEST_MUTATION=$mode bash "$fixture/scripts/build_stage1_from_seed.sh" >/dev/null
        bash "$fixture/scripts/stage1_cache.sh" require
        cmp -s "$scratch/current-source" "$fixture/build/seed/stage1.c"
        passed=$((passed + 1))
    else
        reject "build $mode" env NQ_TEST_MUTATION="$mode" bash "$fixture/scripts/build_stage1_from_seed.sh"
        [[ ! -e "$fixture/build/seed/stage1-cache-v2.txt" ]]
    fi
    cp "$scratch/current-source" "$fixture/selfhost/main.nq"
    cp "$repo_root/tests/fixtures/m54_10_provenance/cc.sh" "$CC"
    chmod +x "$CC"
done
reject 'identity smoke mismatch' env NQ_TEST_VERSION=wrong bash "$fixture/scripts/build_stage1_from_seed.sh"
[[ ! -e "$fixture/build/seed/stage1-cache-v2.txt" ]]
printf 'PASS persistent/restored source, toolchain drift, failure, and identity smoke\n'

for branch in equal unequal; do
    if [[ "$branch" == unequal ]]; then printf 'different current C bytes\n' > "$fixture/selfhost/main.nq"; fi
    : > "$NQ_TEST_LOG"
    bash "$fixture/scripts/build_stage1_from_seed.sh" >/dev/null
    bash "$fixture/scripts/check_seed_bootstrap.sh" --reuse-stage1 > "$scratch/proof-stdout"
    expected=2
    reused=true
    if [[ "$branch" == unequal ]]; then expected=3; reused=false; fi
    assert_equal "$(grep -c '^emit:' "$NQ_TEST_LOG")" "$expected" "$branch emission count including builder"
    assert_equal "$(grep -c '^compare$' "$NQ_TEST_LOG")" 2 "$branch direct comparison edges"
    grep -qx "historical_reused=$reused" "$fixture/build/seed/seed-bootstrap-proof-v1.txt"
done
: > "$NQ_TEST_LOG"
bash "$fixture/scripts/check_seed_bootstrap.sh" >/dev/null
assert_equal "$(grep -c '^emit:' "$NQ_TEST_LOG")" 3 'cold unequal proof emissions'
assert_equal "$(grep -c '^compare$' "$NQ_TEST_LOG")" 2 'cold unequal proof comparison edges'
custom="$scratch/custom-driver"
bash "$fixture/scripts/build_stage1_from_seed.sh" "$custom" >/dev/null
[[ -x "$custom" && ! -e "$fixture/build/seed/stage1-cache-v2.txt" ]]
reject 'custom publication cannot bless default cache' bash "$fixture/scripts/stage1_cache.sh" check
printf 'PASS equal/unequal historical proof reuse and both comparison edges\n'
check_seed_phases
printf 'M54.10 shell provenance fixtures passed (%s assertions; synthetic CC/driver only)\n' "$passed"
