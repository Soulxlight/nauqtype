#!/usr/bin/env bash
# Focused attestation UNIT/STUB layer. No compiler or expensive gate is run.
# Only seed/cache derivation checks and CC metadata executables are fixtures;
# production attestation, provenance hashing, and JSON code remain unchanged.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
fixtures="$repo_root/tests/fixtures/m54_10_attestation"
mkdir -p "$fixtures/build"
scratch=$(mktemp -d "$fixtures/build/run-XXXXXX")
mkdir -p "$scratch/tmp" "$scratch/tools" "$scratch/logs"
export TMPDIR="$scratch/tmp" LC_ALL=C
export NQ_ATTEST_IMPLEMENTATION="$repo_root/scripts/milestone_attestation.sh"
export NQ_ATTEST_STUB_LOG="$scratch/stubs.log"
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
export GIT_AUTHOR_NAME='Attestation Fixture' GIT_AUTHOR_EMAIL='fixture@example.invalid'
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
export GIT_AUTHOR_DATE='2000-01-01T00:00:00Z'
export GIT_COMMITTER_DATE="$GIT_AUTHOR_DATE"
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES
unset NQ_ATTEST_STUB_SEED_FAIL NQ_ATTEST_STUB_CACHE_FAIL NQ_ATTEST_CC_FAIL
unset NQ_ATTEST_BOOTSTRAP_VERSION NQ_ATTEST_PROOF_VERSION NQ_ATTEST_BOOTSTRAP_TARGET NQ_ATTEST_PROOF_TARGET
cp "$fixtures/cc_stub.sh" "$scratch/tools/cc"
cp "$fixtures/cc_stub.sh" "$scratch/tools/bootstrap-cc"
chmod 755 "$scratch/tools/cc" "$scratch/tools/bootstrap-cc"
export CC="$scratch/tools/bootstrap-cc" PATH="$scratch/tools:$PATH"
passed=0 failed=0 sequence=0
: > "$scratch/results.tsv"

cleanup() {
    local code=$?
    cp "$scratch/results.tsv" "$fixtures/build/latest-results.tsv"
    cp "$scratch/implementation.sha256" "$fixtures/build/latest-implementation.sha256"
    if (( code == 0 )) && [[ "${NQ_KEEP_ATTESTATION_FIXTURES:-0}" != 1 ]]; then
        rm -rf -- "$scratch"
    else
        printf 'attestation fixture evidence: %s\n' "$scratch" >&2
    fi
}
sha256sum "$NQ_ATTEST_IMPLEMENTATION" "$repo_root/scripts/provenance.sh" "$repo_root/scripts/seed_manifest.sh" > "$scratch/implementation.sha256"
trap cleanup EXIT

at() { bash "$fixtures/invoke.sh" "$@"; }
sha() { sha256sum < "$1" | cut -d ' ' -f 1; }

check() {
    local expectation=$1 label=$2 code log
    shift 2
    sequence=$((sequence + 1))
    log="$scratch/logs/$sequence.log"
    if "$@" > "$log" 2>&1; then code=0; else code=$?; fi
    if [[ "$expectation" == accept && "$code" == 0 ]] || [[ "$expectation" == reject && "$code" != 0 ]]; then
        passed=$((passed + 1))
        printf 'PASS\t%s\texit=%s\n' "$label" "$code" >> "$scratch/results.tsv"
    else
        failed=$((failed + 1))
        printf 'FAIL\t%s\texit=%s\n' "$label" "$code" >> "$scratch/results.tsv"
        printf 'FAIL expected %s: %s (exit %s)\n' "$expectation" "$label" "$code" >&2
        tail -n 5 "$log" >&2
    fi
}

equal() { [[ "$1" == "$2" ]]; }
absent() { [[ ! -e "$1" ]]; }
record_value() {
    local line value
    line=$(sed -n "/^  \"$2\": /p" "$1")
    value=${line#*: }; value=${value%,}
    if [[ "$value" == \"*\" ]]; then value=${value:1:${#value}-2}; fi
    printf '%s' "$value"
}
replace_scalar() {
    awk -v key="$3" -v scalar="$4" '
        $0 ~ "^  \"" key "\": " {
            comma = ($0 ~ /,$/) ? "," : ""
            $0 = "  \"" key "\": " scalar comma
        }
        { print }
    ' "$1" > "$2"
}

# Independent contract oracle: no production framing/flags helper is called.
oracle_digest() {
    local root=$1 domain=$2 paths=$3 path mode
    {
        printf '%s\nfiles:%s\n' "$domain" "$(wc -l < "$paths")"
        while IFS= read -r path; do
            mode=100644
            [[ ! -x "$root/$path" ]] || mode=100755
            printf 'path-bytes:%s\n%s\nmode:%s\ncontent-bytes:%s\n' "${#path}" "$path" "$mode" "$(wc -c < "$root/$path")"
            cat "$root/$path"
            printf '\n'
        done < "$paths"
    } | sha256sum | cut -d ' ' -f 1
}

artifact_keys=(seed_manifest seed_c seed_runtime_c seed_runtime_h driver stage1_c cache_receipt wrapper proof_summary release_manifest)
artifact_paths=(bootstrap/seed/manifest.json bootstrap/seed/nauqc-seed.c bootstrap/seed/runtime.c bootstrap/seed/runtime.h selfhost/build/nauqc build/seed/stage1.c build/seed/stage1-derivation-v1.txt bin/nauqc build/proof/summary.json build/linux-release/nauqtype/share/nauqtype/release.json)
completion_docs=(AUDIT_REMEDIATION.md M54_10_CONTRACTS.md NAUQTYPE_COORDINATION.md ROADMAP.md TODO.md)

# Synthetic Git commit objects exist ONLY in disposable fixture repositories.
# No project commit, checkout, reset, hook, or push is performed.
fixture_commit() {
    local root=$1 tree parent=''
    tree=$(git -C "$root" write-tree)
    parent=$(git -C "$root" rev-parse --verify HEAD 2>/dev/null) || parent=''
    if [[ -n "$parent" ]]; then
        printf 'synthetic attestation fixture\n' | git -C "$root" commit-tree "$tree" -p "$parent"
    else
        printf 'synthetic attestation fixture\n' | git -C "$root" commit-tree "$tree"
    fi
}

make_fixture() {
    local root=$1 state=$2 path
    mkdir -p "$root/selfhost" "$root/schemas" "$root/scripts" "$root/stdlib"
    # Ignored artifacts isolate their own attestation checks from candidate checks.
    printf '/build/\n/selfhost/build/\n/bootstrap/seed/\n/bin/\n' > "$root/.gitignore"
    printf 'fn main() -> i32 { return 0; }\n' > "$root/selfhost/main.nq"
    printf '{"fixture":true}\n' > "$root/schemas/example.schema.json"
    printf 'fixture README, not a completion-only document\n' > "$root/README.md"
    printf 'fixture current runtime\n' > "$root/stdlib/runtime.c"
    printf 'fixture-version\n' > "$root/VERSION"
    for path in "${completion_docs[@]}"; do printf 'candidate %s\n' "$path" > "$root/$path"; done
    cp "$fixtures/cache_stub.sh" "$root/scripts/stage1_cache.sh"
    chmod 755 "$root/scripts/stage1_cache.sh"
    for path in "${artifact_paths[@]}"; do
        mkdir -p "$root/$(dirname "$path")"
        printf 'UNIT artifact bytes: %s\n' "$path" > "$root/$path"
    done
    printf '{"version":3,"ok":true,"fixture":"UNIT ONLY, not a real proof"}\n' > "$root/build/proof/summary.json"
    mkdir -p "$root/build/linux-release/nauqtype/bin"
    printf 'fixture release payload\n' > "$root/build/linux-release/nauqtype/bin/nauqc"
    chmod 755 "$root/build/linux-release/nauqtype/bin/nauqc"
    git -C "$root" init -q --object-format=sha1 --initial-branch=fixture
    git -C "$root" config core.filemode true
    git -C "$root" add -- .
    if [[ "$state" == commit ]]; then git -C "$root" update-ref refs/heads/fixture "$(fixture_commit "$root")"; fi
}

printf 'M54.10 attestation UNIT/STUB gate: no compiler, seed, cache derivation, or release proof is run\n'
base="$scratch/committed"
make_fixture "$base" commit
at exercise "$base" > "$scratch/setup.log" 2>&1
attestation="$base/build/verification/milestone-attestation-v1.json"
cp "$attestation" "$scratch/good-attestation.json"
check accept 'clean committed candidate verifies' at verify "$base"
check accept 'clean fixture Git status' equal "$(git -C "$base" status --porcelain)" ''
at fields > "$scratch/fields"
check accept 'exact fixed attestation field registry' cmp -s "$fixtures/attestation-fields.txt" "$scratch/fields"
check accept 'canonical JSON parses' at parse attestation "$attestation" "$scratch/parsed"
check accept 'committed head state' equal "$(record_value "$attestation" head_state)" commit
check accept 'actual base revision' equal "$(record_value "$attestation" base_revision)" "$(git -C "$base" rev-parse HEAD)"
check accept 'actual index tree before' equal "$(record_value "$attestation" index_tree_before)" "$(git -C "$base" write-tree)"
check accept 'actual index tree after' equal "$(record_value "$attestation" index_tree_after)" "$(git -C "$base" write-tree)"
check accept 'worktree/index equality is explicit true' equal "$(record_value "$attestation" worktree_matches_index)" true
git -C "$base" ls-files | sort > "$scratch/tracked.paths"
: > "$scratch/empty.paths"
expected_candidate=$(oracle_digest "$base" nauqtype-candidate/v1 "$scratch/tracked.paths")
check accept 'candidate before uses exact framed bytes/modes' equal "$(record_value "$attestation" candidate_sha256_before)" "$expected_candidate"
check accept 'candidate after uses exact framed bytes/modes' equal "$(record_value "$attestation" candidate_sha256_after)" "$expected_candidate"
check accept 'empty untracked domain is framed' equal "$(record_value "$attestation" untracked_sha256)" "$(oracle_digest "$base" nauqtype-untracked/v1 "$scratch/empty.paths")"

expected_bootstrap_flags=$(
    printf '%s\0' nauqtype-bootstrap-flags/v1 seed -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Ibootstrap/seed bootstrap/seed/nauqc-seed.c bootstrap/seed/runtime.c -o build/seed/nauqc-seed stage1 -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib build/seed/stage1.c stdlib/runtime.c -o selfhost/build/nauqc | sha256sum | cut -d ' ' -f 1
)
expected_proof_flags=$(
    printf '%s\0' nauqtype-proof-options/v1 -std=c11 -O2 -D_POSIX_C_SOURCE=200809L -Istdlib | sha256sum | cut -d ' ' -f 1
)
check accept 'bootstrap flags exact NUL-framed contract' equal "$(record_value "$attestation" bootstrap_flags_sha256)" "$expected_bootstrap_flags"
check accept 'proof options exact NUL-framed contract' equal "$(record_value "$attestation" proof_flags_sha256)" "$expected_proof_flags"
for role in bootstrap proof; do
    tool="$scratch/tools/cc"
    [[ "$role" != bootstrap ]] || tool="$CC"
    "$tool" --version > "$scratch/cc-version"
    check accept "$role CC exact physical path" equal "$(record_value "$attestation" "${role}_cc_path")" "$(realpath -e "$tool")"
    check accept "$role CC exact executable bytes" equal "$(record_value "$attestation" "${role}_cc_sha256")" "$(sha "$tool")"
    check accept "$role CC exact version stdout bytes" equal "$(record_value "$attestation" "${role}_cc_version_sha256")" "$(sha "$scratch/cc-version")"
    check accept "$role CC exact target" equal "$(record_value "$attestation" "${role}_cc_target")" "$("$tool" -dumpmachine)"
done
for index in "${!artifact_keys[@]}"; do
    check accept "real artifact hash ${artifact_keys[index]}" equal "$(record_value "$attestation" "${artifact_keys[index]}_sha256")" "$(sha "$base/${artifact_paths[index]}")"
done
printf 'bin/nauqc\nshare/nauqtype/release.json\n' > "$scratch/release.paths"
check accept 'release tree exact relative-path framing' equal "$(record_value "$attestation" release_tree_sha256)" "$(oracle_digest "$base/build/linux-release/nauqtype" nauqtype-release-tree/v1 "$scratch/release.paths")"

unborn="$scratch/unborn"
make_fixture "$unborn" unborn
check accept 'unborn indexed fixture begins/finishes/verifies' at exercise "$unborn"
unborn_record="$unborn/build/verification/milestone-attestation-v1.json"
check accept 'unborn has explicit head state' equal "$(record_value "$unborn_record" head_state)" unborn
check accept 'unborn has real index tree' equal "$(record_value "$unborn_record" index_tree_after)" "$(git -C "$unborn" write-tree)"
check accept 'unborn base is unquoted JSON null' grep -Fx '  "base_revision": null,' "$unborn_record"

for kind in duplicate unknown missing reordered whitespace cr nul trailing missing-lf extra-comma missing-comma quoted-bool short-hash uppercase-hash; do
    bad="$scratch/bad-$kind.json"
    cp "$scratch/good-attestation.json" "$bad"
    case "$kind" in
        duplicate) sed -i '2p' "$bad";;
        unknown) sed -i '2s/version/unknown/' "$bad";;
        missing) sed -i '2d' "$bad";;
        reordered) sed -i '2{h;d;};3{p;g;}' "$bad";;
        whitespace) sed -i '2s/^  / /' "$bad";;
        cr) sed -i 's/$/\r/' "$bad";;
        nul) printf '\0' >> "$bad";;
        trailing) printf '{}\n' >> "$bad";;
        missing-lf) truncate -s -1 "$bad";;
        extra-comma) sed -i '$i\  , ' "$bad";;
        missing-comma) sed -i '2s/,$//' "$bad";;
        quoted-bool) sed -i 's/: true,/: "true",/' "$bad";;
        short-hash) sed -i 's/"driver_sha256": "./"driver_sha256": "/' "$bad";;
        uppercase-hash) sed -i 's/"driver_sha256": "./"driver_sha256": "A/' "$bad";;
    esac
    check reject "strict JSON $kind" at parse attestation "$bad" "$scratch/parsed-bad"
done
for item in 'version:"milestone-close/v1"' 'head_state:"unborn"' 'base_revision:null' 'worktree_matches_index:false'; do
    key=${item%%:*}; scalar=${item#*:}
    replace_scalar "$scratch/good-attestation.json" "$scratch/incoherent.json" "$key" "$scalar"
    check reject "record coherence $key" at verify "$base" "$scratch/incoherent.json"
done

cp "$base/selfhost/main.nq" "$scratch/source-good"
printf 'unstaged source drift\n' >> "$base/selfhost/main.nq"
check reject 'worktree content differs from index' at verify "$base"
check reject 'begin rejects dirty worktree' at begin "$base"
cp "$scratch/source-good" "$base/selfhost/main.nq"
cp "$scratch/good-attestation.json" "$attestation"
other_blob=$(printf 'different indexed bytes\n' | git -C "$base" hash-object -w --stdin)
git -C "$base" update-index --cacheinfo "100644,$other_blob,selfhost/main.nq"
check reject 'index-only mismatch' at verify "$base"
git -C "$base" add selfhost/main.nq
chmod 755 "$base/selfhost/main.nq"
git -C "$base" config core.filemode false
check reject 'mode mismatch rejects even with core.filemode=false' at verify "$base"
chmod 644 "$base/selfhost/main.nq"
git -C "$base" config core.filemode true
printf 'untracked identity\n' > "$base/untracked.nq"
check reject 'untracked file invalidates old evidence' at verify "$base"
at exercise "$base" > "$scratch/untracked-setup.log" 2>&1
printf 'untracked.nq\n' > "$scratch/untracked.paths"
check accept 'untracked subset exact digest' equal "$(record_value "$attestation" untracked_sha256)" "$(oracle_digest "$base" nauqtype-untracked/v1 "$scratch/untracked.paths")"
sort "$scratch/tracked.paths" "$scratch/untracked.paths" > "$scratch/candidate.paths"
check accept 'candidate includes untracked bytes' equal "$(record_value "$attestation" candidate_sha256_after)" "$(oracle_digest "$base" nauqtype-candidate/v1 "$scratch/candidate.paths")"
printf 'changed untracked identity\n' >> "$base/untracked.nq"
check reject 'changed untracked bytes reject' at verify "$base"
rm "$base/untracked.nq"
check reject 'removed untracked bytes reject' at verify "$base"
cp "$scratch/good-attestation.json" "$attestation"

check accept 'state mutations restored canonical evidence' at verify "$base"

# Every artifact is deliberately ignored in this fixture so these rejections
# cannot accidentally be satisfied by the separate worktree/index checks.
for index in "${!artifact_keys[@]}"; do
    path="$base/${artifact_paths[index]}"
    cp -p "$path" "$scratch/artifact-good"
    printf 'transplanted artifact payload\n' >> "$path"
    check reject "artifact transplant ${artifact_keys[index]}" at verify "$base"
    cp -p "$scratch/artifact-good" "$path"
done
mv "$base/build/proof/summary.json" "$scratch/proof-good"
check reject 'missing required proof summary' at verify "$base"
mv "$scratch/proof-good" "$base/build/proof/summary.json"
printf 'extra release file\n' > "$base/build/linux-release/nauqtype/extra"
check reject 'release extra-file transplant' at verify "$base"
rm "$base/build/linux-release/nauqtype/extra"
chmod 644 "$base/build/linux-release/nauqtype/bin/nauqc"
check reject 'release mode tamper' at verify "$base"
chmod 755 "$base/build/linux-release/nauqtype/bin/nauqc"
check reject 'seed stub failure propagates' env NQ_ATTEST_STUB_SEED_FAIL=1 bash "$fixtures/invoke.sh" verify "$base"
check reject 'cache stub failure propagates' env NQ_ATTEST_STUB_CACHE_FAIL=1 bash "$fixtures/invoke.sh" verify "$base"
check accept 'artifact mutations restored canonical evidence' at verify "$base"

for key in bootstrap_flags_sha256 proof_flags_sha256 candidate_sha256_before candidate_sha256_after untracked_sha256 index_tree_before index_tree_after; do
    value=0000000000000000000000000000000000000000000000000000000000000000
    [[ "$key" != index_tree* ]] || value=${value:0:40}
    replace_scalar "$scratch/good-attestation.json" "$scratch/transplant.json" "$key" "\"$value\""
    check reject "record transplant $key" at verify "$base" "$scratch/transplant.json"
done
for role in bootstrap proof; do
    tool="$scratch/tools/cc"
    [[ "$role" != bootstrap ]] || tool="$CC"
    cp -p "$tool" "$scratch/cc-good"
    printf '# altered executable identity\n' >> "$tool"
    check reject "$role CC executable tamper" at verify "$base"
    cp -p "$scratch/cc-good" "$tool"
    var=NQ_ATTEST_PROOF_VERSION
    [[ "$role" != bootstrap ]] || var=NQ_ATTEST_BOOTSTRAP_VERSION
    check reject "$role CC version drift" env "$var=transplanted version" bash "$fixtures/invoke.sh" verify "$base"
    var=NQ_ATTEST_PROOF_TARGET
    [[ "$role" != bootstrap ]] || var=NQ_ATTEST_BOOTSTRAP_TARGET
    check reject "$role CC target drift" env "$var=other-linux" bash "$fixtures/invoke.sh" verify "$base"
done
cp -p "$CC" "$scratch/tools/bootstrap-other"
check reject 'bootstrap CC path transplant with same bytes' env CC="$scratch/tools/bootstrap-other" bash "$fixtures/invoke.sh" verify "$base"
mkdir "$scratch/alternate-tools"
cp -p "$scratch/tools/cc" "$scratch/alternate-tools/cc"
check reject 'proof CC path transplant with same bytes' env PATH="$scratch/alternate-tools:$PATH" bash "$fixtures/invoke.sh" verify "$base"
check reject 'unsuccessful CC version query' env NQ_ATTEST_CC_FAIL=version bash "$fixtures/invoke.sh" verify "$base"
check reject 'unsuccessful CC target query' env NQ_ATTEST_CC_FAIL=target bash "$fixtures/invoke.sh" verify "$base"
check reject 'malformed CC target atom' env NQ_ATTEST_PROOF_TARGET='invalid target' bash "$fixtures/invoke.sh" verify "$base"
check accept 'CC and record mutations restored canonical evidence' at verify "$base"

for spelling in 'bootstrap"quoted' 'bootstrap\backslash'; do
    cp -p "$CC" "$scratch/tools/$spelling"
    quoted="$scratch/quoted-${sequence}"
    cp -a "$base" "$quoted"
    check accept "canonical escaped CC path $spelling" env CC="$scratch/tools/$spelling" bash "$fixtures/invoke.sh" exercise "$quoted"
done

for kind in unstaged staged untracked cc before-flags; do
    drift="$scratch/drift-$kind"
    cp -a "$base" "$drift"
    at begin "$drift"
    case "$kind" in
        unstaged) printf 'during gate\n' >> "$drift/selfhost/main.nq";;
        staged) printf 'during gate\n' >> "$drift/selfhost/main.nq"; git -C "$drift" add selfhost/main.nq;;
        untracked) printf 'during gate\n' > "$drift/new.nq";;
        cc) cp -p "$CC" "$scratch/cc-good"; printf '# during gate\n' >> "$CC";;
        before-flags)
            replace_scalar "$drift/build/verification/milestone-start-v1.json" "$scratch/start-other" proof_flags_sha256 '"0000000000000000000000000000000000000000000000000000000000000000"'
            cp "$scratch/start-other" "$drift/build/verification/milestone-start-v1.json"
            ;;
    esac
    check reject "begin-to-finish $kind drift" at finish "$drift"
    check accept "failed $kind finish publishes no attestation" absent "$drift/build/verification/milestone-attestation-v1.json"
    [[ "$kind" != cc ]] || cp -p "$scratch/cc-good" "$CC"
done
restored="$scratch/restored"
cp -a "$base" "$restored"
at begin "$restored"
printf 'transient source mutation\n' >> "$restored/selfhost/main.nq"
cp "$scratch/source-good" "$restored/selfhost/main.nq"
check accept 'restored source mutation permits finish (no capture claim)' at finish "$restored"
check accept 'restored source evidence verifies' at verify "$restored"

wrong_tree="$scratch/wrong-tree"
cp -a "$base" "$wrong_tree"
printf 'different candidate\n' >> "$wrong_tree/selfhost/main.nq"
git -C "$wrong_tree" add selfhost/main.nq
check reject 'clean indexed wrong-tree attestation transplant' at verify "$wrong_tree"

closing="$scratch/closing"
cp -a "$base" "$closing"
candidate_tree=$(record_value "$attestation" index_tree_after)
for path in "${completion_docs[@]}"; do printf 'disclosed completion\n' >> "$closing/$path"; done
git -C "$closing" add -- "${completion_docs[@]}"
final_commit=$(fixture_commit "$closing")
git -C "$closing" update-ref refs/heads/fixture "$final_commit"
check accept 'all five allowed completion-only document deltas' at close "$closing" "$final_commit"
check accept 'completion delta verifies' at verify-close "$closing"
close_file="$closing/build/verification/milestone-close-v1.json"
delta_file="$closing/build/verification/milestone-close-delta-v1.txt"
at close-fields > "$scratch/close-fields"
check accept 'exact close field registry' cmp -s "$fixtures/close-fields.txt" "$scratch/close-fields"
check accept 'close candidate tree is original attested index' equal "$(record_value "$close_file" candidate_tree)" "$candidate_tree"
check accept 'close final commit is exact fixture commit' equal "$(record_value "$close_file" final_commit)" "$final_commit"
check accept 'close final tree is actual commit tree' equal "$(record_value "$close_file" final_tree)" "$(git -C "$closing" rev-parse "$final_commit^{tree}")"
printf 'milestone-close-delta/v1\n' > "$scratch/expected-delta"
for path in "${completion_docs[@]}"; do
    git -C "$closing" show "$candidate_tree:$path" > "$scratch/doc-before"
    git -C "$closing" show "$final_commit:$path" > "$scratch/doc-after"
    printf 'path-bytes:%s\n%s\nbefore:%s\nafter:%s\n' "${#path}" "$path" "$(sha "$scratch/doc-before")" "$(sha "$scratch/doc-after")" >> "$scratch/expected-delta"
done
check accept 'closing delta exact sorted LF bytes' cmp -s "$scratch/expected-delta" "$delta_file"
check accept 'closing delta hash binds exact bytes' equal "$(record_value "$close_file" documentation_delta_sha256)" "$(sha "$delta_file")"
check accept 'close binds original attestation bytes' equal "$(record_value "$close_file" attestation_sha256)" "$(sha "$closing/build/verification/milestone-attestation-v1.json")"
cp "$close_file" "$scratch/good-close.json"
cp "$delta_file" "$scratch/good-delta.txt"
printf '\n' >> "$delta_file"
check reject 'closing delta byte tamper' at verify-close "$closing"
cp "$scratch/good-delta.txt" "$delta_file"
sed -i '2p' "$close_file"
check reject 'closing JSON duplicate field' at verify-close "$closing"
cp "$scratch/good-close.json" "$close_file"
replace_scalar "$close_file" "$scratch/other-close" candidate_tree '"0000000000000000000000000000000000000000"'
cp "$scratch/other-close" "$close_file"
check reject 'closing candidate tree transplant' at verify-close "$closing"
cp "$scratch/good-close.json" "$close_file"
sed -i 's/"proof_flags_sha256": "./"proof_flags_sha256": "0/' "$closing/build/verification/milestone-attestation-v1.json"
check reject 'closing original attestation tamper' at verify-close "$closing"
cp "$scratch/good-attestation.json" "$closing/build/verification/milestone-attestation-v1.json"

for kind in source schema readme runtime script mode add delete rename; do
    forbidden="$scratch/forbidden-$kind"
    cp -a "$base" "$forbidden"
    if [[ "$kind" == add ]]; then
        rm "$forbidden/TODO.md"
        git -C "$forbidden" add -A
        at exercise "$forbidden" > "$scratch/add-setup.log" 2>&1
    fi
    case "$kind" in
        source) printf 'post-gate source\n' >> "$forbidden/selfhost/main.nq";;
        schema) printf 'post-gate schema\n' >> "$forbidden/schemas/example.schema.json";;
        readme) printf 'post-gate README\n' >> "$forbidden/README.md";;
        runtime) printf 'post-gate runtime\n' >> "$forbidden/stdlib/runtime.c";;
        script) printf '# post-gate script\n' >> "$forbidden/scripts/stage1_cache.sh";;
        mode) chmod 755 "$forbidden/TODO.md";;
        add) printf 'new allowlisted document\n' > "$forbidden/TODO.md";;
        delete) rm "$forbidden/TODO.md";;
        rename) mv "$forbidden/TODO.md" "$forbidden/TODO-renamed.md";;
    esac
    git -C "$forbidden" add -A
    forbidden_commit=$(fixture_commit "$forbidden")
    check reject "disallowed post-gate delta $kind" at close "$forbidden" "$forbidden_commit"
    check accept "rejected $kind delta publishes no close record" absent "$forbidden/build/verification/milestone-close-v1.json"
    if [[ "$kind" == source ]]; then
        cp "$scratch/good-close.json" "$forbidden/build/verification/milestone-close-v1.json"
        replace_scalar "$forbidden/build/verification/milestone-close-v1.json" "$scratch/forged-close" final_commit "\"$forbidden_commit\""
        cp "$scratch/forged-close" "$forbidden/build/verification/milestone-close-v1.json"
        cp "$scratch/good-delta.txt" "$forbidden/build/verification/milestone-close-delta-v1.txt"
        check reject 'verify-close refuses forged source delta' at verify-close "$forbidden"
    fi
done
untracked_close="$scratch/untracked-close"
cp -a "$base" "$untracked_close"
printf 'not indexed\n' > "$untracked_close/untracked.nq"
at exercise "$untracked_close" > "$scratch/untracked-close-setup.log" 2>&1
check reject 'closing rejects untracked candidate content' at close "$untracked_close" "$(fixture_commit "$untracked_close")"
check accept 'seed stub actually exercised' grep -q '^STUB seed_verify ' "$NQ_ATTEST_STUB_LOG"
check accept 'cache stub actually exercised' grep -q '^STUB stage1_cache require$' "$NQ_ATTEST_STUB_LOG"
check accept 'tested production implementation unchanged during run' sha256sum --check --status "$scratch/implementation.sha256"
printf 'M54.10 attestation UNIT/STUB gate: %s passed, %s failed\n' "$passed" "$failed"
(( failed == 0 ))
