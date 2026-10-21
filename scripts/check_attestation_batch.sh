#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "$script_dir/milestone_attestation.sh"

scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
export LC_ALL=C GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES
passed=0

check() {
    local label=$1
    shift
    if "$@"; then
        passed=$((passed + 1))
    else
        printf 'attestation batch check failed: %s\n' "$label" >&2
        exit 1
    fi
}

make_repo() {
    local root=$1
    mkdir -p "$root"
    git -C "$root" init -q --object-format=sha1 --initial-branch=fixture
    git -C "$root" config core.filemode true
}

capture_index() { git -C "$1" ls-files --stage -z > "$2"; }

# Frozen copy of the decoder that preceded the scalar fast path.
attest_oracle_decode_old() (
    local scalar=$1 value='' ch index=0 next
    while (( index < ${#scalar} )); do
        ch=${scalar:index:1}
        if [[ "$ch" == '\' ]]; then
            index=$((index + 1)); next=${scalar:index:1}
            [[ "$next" == '\' || "$next" == '"' ]] || exit 1
            ch=$next
        elif [[ "$ch" == '"' ]]; then exit 1; fi
        value+=$ch; index=$((index + 1))
    done
    printf '%s' "$value"
)

write_scalar_record() {
    printf '{\n  "bootstrap_cc_path": "%s"\n}\n' "$2" > "$1"
}

scalar_accept_matches_old() {
    local raw=$1 expected=$2 tag=$3 decoded
    local fields="$scratch/scalar-$tag.fields" values="$scratch/scalar-$tag.values"
    local record="$scratch/scalar-$tag.json" parsed="$scratch/scalar-$tag.parsed"
    decoded=$(attest_oracle_decode_old "$raw") || return 1
    [[ "$decoded" == "$expected" ]] || return 1
    printf 'bootstrap_cc_path\n' > "$fields"
    printf 'bootstrap_cc_path=%s\n' "$expected" > "$values"
    write_scalar_record "$record" "$raw"
    attest_json_write "$fields" "$values" > "$scratch/scalar-$tag.canonical" || return 1
    cmp -s "$record" "$scratch/scalar-$tag.canonical" || return 1
    attest_json_read "$record" "$fields" "$parsed" || return 1
    cmp -s "$values" "$parsed"
}

scalar_reject_matches_old() {
    local raw=$1 tag=$2 decoded
    local fields="$scratch/scalar-$tag.fields" record="$scratch/scalar-$tag.json"
    if decoded=$(attest_oracle_decode_old "$raw"); then return 1; fi
    printf 'bootstrap_cc_path\n' > "$fields"
    write_scalar_record "$record" "$raw"
    ! attest_json_read "$record" "$fields" "$scratch/scalar-$tag.parsed"
}

compare_accept() {
    local root=$1 index=$2 label=$3 scalar batch
    scalar="$scratch/$label.scalar"
    batch="$scratch/$label.batch"
    attest_index_matches_worktree_scalar "$root" "$index" "$scalar" || return 1
    attest_index_matches_worktree_batch "$root" "$index" "$batch" || return 1
    cmp -s "$scalar" "$batch"
}

compare_reject() {
    local root=$1 index=$2 label=$3 scalar batch scalar_error batch_error
    scalar="$scratch/$label.scalar"
    batch="$scratch/$label.batch"
    scalar_error="$scratch/$label.scalar.err"
    batch_error="$scratch/$label.batch.err"
    if attest_index_matches_worktree_scalar "$root" "$index" "$scalar" 2> "$scalar_error"; then return 1; fi
    if attest_index_matches_worktree_batch "$root" "$index" "$batch" 2> "$batch_error"; then return 1; fi
    cmp -s "$scalar_error" "$batch_error"
}

empty="$scratch/empty"
make_repo "$empty"
capture_index "$empty" "$scratch/empty.index"
check 'empty scalar/batch equivalence' compare_accept "$empty" "$scratch/empty.index" empty

multi="$scratch/multi"
make_repo "$multi"
mkdir -p "$multi/dir"
printf 'alpha\n' > "$multi/plain"
printf 'space\n' > "$multi/dir/space name"
printf 'quote\n' > "$multi/quote\"name"
git -C "$multi" add -- .
capture_index "$multi" "$scratch/multi.index"
check 'multiple, space and quote path equivalence' compare_accept "$multi" "$scratch/multi.index" multi

content="$scratch/content"
make_repo "$content"
printf 'indexed\n' > "$content/a-content"
git -C "$content" add -- .
capture_index "$content" "$scratch/content.index"
printf 'changed\n' > "$content/a-content"
check 'content defect scalar/batch equivalence' compare_reject "$content" "$scratch/content.index" content

mode="$scratch/mode"
make_repo "$mode"
printf 'mode\n' > "$mode/a-mode"
git -C "$mode" add -- .
capture_index "$mode" "$scratch/mode.index"
chmod 755 "$mode/a-mode"
check 'mode defect scalar/batch equivalence' compare_reject "$mode" "$scratch/mode.index" mode

ordered="$scratch/ordered"
make_repo "$ordered"
printf 'first\n' > "$ordered/a-content"
printf 'later\n' > "$ordered/z-mode"
git -C "$ordered" add -- .
capture_index "$ordered" "$scratch/ordered.index"
printf 'changed first\n' > "$ordered/a-content"
chmod 755 "$ordered/z-mode"
if attest_index_matches_worktree_batch "$ordered" "$scratch/ordered.index" "$scratch/ordered.paths" 2> "$scratch/ordered.err"; then exit 1; fi
check 'earlier content mismatch precedes later mode defect' grep -Fqx 'provenance: worktree bytes differ from index: a-content' "$scratch/ordered.err"

ordered_path="$scratch/ordered-path"
make_repo "$ordered_path"
printf 'first\n' > "$ordered_path/a-content"
printf 'later\n' > "$ordered_path/"$'z\npath'
git -C "$ordered_path" add -- .
capture_index "$ordered_path" "$scratch/ordered-path.index"
printf 'changed first\n' > "$ordered_path/a-content"
if attest_index_matches_worktree_batch "$ordered_path" "$scratch/ordered-path.index" "$scratch/ordered-path.paths" 2> "$scratch/ordered-path.err"; then exit 1; fi
check 'earlier content mismatch precedes later path defect' grep -Fqx 'provenance: worktree bytes differ from index: a-content' "$scratch/ordered-path.err"

git() {
    local arg batch=0 hashing=0
    for arg in "$@"; do
        [[ "$arg" != hash-object ]] || hashing=1
        [[ "$arg" != --stdin-paths ]] || batch=1
    done
    if (( hashing )) && [[ -n "${NQ_ATTEST_BATCH_STUB:-}" ]]; then
        if (( batch )); then
            printf 'batch\n' >> "$NQ_ATTEST_BATCH_LOG"
            case "$NQ_ATTEST_BATCH_STUB" in
                failed) cat > /dev/null; printf '%040d\n' 0; return 7;;
                partial) cat > /dev/null; printf '%040d\n' 0; return 0;;
                malformed)
                    while IFS= read -r _; do printf 'gggggggggggggggggggggggggggggggggggggggg\n'; done
                    return 0
                    ;;
                extra)
                    while IFS= read -r _; do printf '%040d\n' 0; done
                    printf '%040d\n' 0
                    return 0
                    ;;
                *) return 9;;
            esac
        fi
        printf 'scalar\n' >> "$NQ_ATTEST_BATCH_LOG"
    fi
    command git "$@"
}

stub_rejects() {
    local kind=$1 log out
    log="$scratch/stub-$kind.log"
    out="$scratch/stub-$kind.paths"
    : > "$log"
    export NQ_ATTEST_BATCH_STUB=$kind NQ_ATTEST_BATCH_LOG=$log
    if attest_index_matches_worktree "$multi" "$scratch/multi.index" "$out"; then return 1; fi
    [[ "$(cat "$log")" == batch ]]
}

check 'legacy scalar accepts batch fault fixture' attest_index_matches_worktree_scalar "$multi" "$scratch/multi.index" "$scratch/stub-scalar.paths"
check 'failed batch has no scalar fallback' stub_rejects failed
check 'partial batch output rejects' stub_rejects partial
check 'malformed batch output rejects' stub_rejects malformed
check 'extra batch output rejects' stub_rejects extra

unsupported="$scratch/unsupported"$'\n'root
make_repo "$unsupported"
printf 'root framing\n' > "$unsupported/file"
git -C "$unsupported" add -- .
capture_index "$unsupported" "$scratch/unsupported.index"
: > "$scratch/unsupported.log"
export NQ_ATTEST_BATCH_STUB=failed NQ_ATTEST_BATCH_LOG="$scratch/unsupported.log"
check 'unsupported root uses legacy scalar path' attest_index_matches_worktree "$unsupported" "$scratch/unsupported.index" "$scratch/unsupported.paths"
check 'unsupported root never invokes batch' test "$(cat "$scratch/unsupported.log")" = scalar

unset NQ_ATTEST_BATCH_STUB NQ_ATTEST_BATCH_LOG
batch_passed=$passed
[[ "$batch_passed" == 13 ]] || exit 1

write_root="$scratch/write-fault"
make_repo "$write_root"
printf 'one indexed row\n' > "$write_root/tracked.txt"
git -C "$write_root" add -- tracked.txt
capture_index "$write_root" "$scratch/write.index"

write_fault_rejects() (
    local behavior=$1 implementation=$2 path='' blob=''
    local log="$scratch/write-$behavior-$implementation.log" result="$scratch/write-$behavior-$implementation.paths"
    : > "$log"
    printf() {
        if [[ "${path:-}" == tracked.txt && "$#" == 2 && "$1" == '%s\n' ]] && \
            [[ "$2" == "$path" || "$2" == "$write_root/$path" || "$2" == "${blob:-}" ]]; then
            builtin printf 'discarded row field\n' >> "$log"
            [[ "$behavior" == drop ]]
            return $?
        fi
        builtin printf "$@"
    }
    if "attest_index_matches_worktree_$implementation" "$write_root" "$scratch/write.index" "$result" 2> "$scratch/write.err"; then
        return 1
    fi
    [[ -s "$log" && ! -s "$result" ]]
)
check 'batch rejects whole-row printf failure inside if context' write_fault_rejects fail batch
check 'batch independent count rejects silently discarded whole row' write_fault_rejects drop batch
check 'scalar rejects tracked-path write failure inside if context' write_fault_rejects fail scalar

initialization_fault_rejects() (
    local field=$1 log="$scratch/init-$1.log" result="$scratch/init-$1.paths"
    : > "$log"
    mktemp() {
        local directory
        [[ "$#" == 1 && "$1" == -d ]] || return 1
        directory=$(command mktemp -d "$scratch/init.XXXXXX") || return 1
        mkdir -- "$directory/$field" || return 1
        builtin printf '%s\n' "$directory"
    }
    prov_mode() { builtin printf 'unexpected validation\n' >> "$log"; return 1; }
    if attest_index_matches_worktree_batch "$write_root" "$scratch/write.index" "$result" 2> "$scratch/init.err"; then
        return 1
    fi
    [[ ! -s "$log" && ! -s "$result" ]]
)
for field in paths absolute-paths expected-oids static-error; do
    check "batch rejects $field initialization failure before validation" initialization_fault_rejects "$field"
done
write_passed=$((passed - batch_passed))
scalar_start=$passed

check 'old decoder plain scalar roundtrip' scalar_accept_matches_old '/tmp/plain value' '/tmp/plain value' plain
check 'old decoder punctuation scalar roundtrip' scalar_accept_matches_old '/tmp/a-b_c.d 42' '/tmp/a-b_c.d 42' punctuation
check 'old decoder escaped backslash roundtrip' scalar_accept_matches_old '/tmp/back\\slash' '/tmp/back\slash' backslash
check 'old decoder escaped quote roundtrip' scalar_accept_matches_old '/tmp/quote\"value' '/tmp/quote"value' quote
check 'old decoder combined escapes roundtrip' scalar_accept_matches_old '/tmp/a\\b\"c' '/tmp/a\b"c' combined
check 'old decoder rejects unknown escape' scalar_reject_matches_old '/tmp/bad\q' unknown
check 'old decoder rejects dangling escape' scalar_reject_matches_old '/tmp/dangling\' dangling
check 'old decoder rejects embedded quote' scalar_reject_matches_old '/tmp/bad"quote' embedded

printf 'attestation batch checks: %d passed\n' "$batch_passed"
printf 'attestation write-failure checks: %d passed\n' "$write_passed"
printf 'attestation scalar checks: %d passed\n' "$((passed - scalar_start))"
