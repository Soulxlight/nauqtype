#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "$script_dir/provenance.sh"
source "$script_dir/seed_manifest.sh"

attest_fields() {
    printf '%s\n' version command status head_state base_revision index_tree_before \
        index_tree_after candidate_sha256_before candidate_sha256_after untracked_sha256 \
        worktree_matches_index seed_manifest_sha256 seed_c_sha256 seed_runtime_c_sha256 \
        seed_runtime_h_sha256 driver_sha256 stage1_c_sha256 cache_receipt_sha256 wrapper_sha256 \
        bootstrap_cc_path bootstrap_cc_sha256 bootstrap_cc_version_sha256 bootstrap_cc_target \
        bootstrap_flags_sha256 proof_cc_path proof_cc_sha256 proof_cc_version_sha256 \
        proof_cc_target proof_flags_sha256 proof_summary_sha256 release_manifest_sha256 release_tree_sha256
}

attest_start_fields() {
    printf '%s\n' head_state base_revision index_tree candidate_sha256 untracked_sha256 \
        bootstrap_cc_path bootstrap_cc_sha256 bootstrap_cc_version_sha256 bootstrap_cc_target \
        bootstrap_flags_sha256 proof_cc_path proof_cc_sha256 proof_cc_version_sha256 \
        proof_cc_target proof_flags_sha256
}

attest_close_fields() {
    printf '%s\n' version attestation_sha256 final_commit final_tree candidate_tree documentation_delta_sha256 status
}

attest_value_valid() {
    local key=$1 value=$2
    case "$key" in
        version) [[ "$value" == milestone-attestation/v1 || "$value" == milestone-close/v1 ]];;
        command) [[ "$value" == check-milestone ]];;
        status) [[ "$value" == ok ]];;
        head_state) [[ "$value" == commit || "$value" == unborn ]];;
        base_revision) [[ "$value" == null || "$value" =~ ^[0-9a-f]{40}$ ]];;
        index_tree*|final_commit|final_tree|candidate_tree) [[ "$value" =~ ^[0-9a-f]{40}$ ]];;
        worktree_matches_index) [[ "$value" == true ]];;
        *_path) prov_absolute "$value";;
        *_target) prov_atom "$value";;
        *_sha256*) prov_hex "$value";;
        *) return 1;;
    esac
}

attest_quote() {
    local value=$1
    value=${value//\\/\\\\}
    value=${value//\"/\\\"}
    printf '"%s"' "$value"
}

# Only printable scalar records from the fixed key registry are accepted.
attest_json_write() (
    local fields=$1 values=$2 key value suffix index=0
    local -a keys=()
    local -A record=()
    mapfile -t keys < "$fields" || exit 1
    while IFS='=' read -r key value; do
        [[ ! -v record[$key] ]] && attest_value_valid "$key" "$value" || exit 1
        record[$key]=$value
    done < "$values"
    [[ ${#keys[@]} == ${#record[@]} ]] || exit 1
    printf '{\n'
    for key in "${keys[@]}"; do
        [[ -v record[$key] ]] || exit 1
        value=${record[$key]}
        index=$((index + 1)); suffix=,
        (( index != ${#keys[@]} )) || suffix=''
        printf '  "%s": ' "$key"
        if [[ "$key" == worktree_matches_index || ( "$key" == base_revision && "$value" == null ) ]]; then
            printf '%s' "$value"
        else
            attest_quote "$value"
        fi
        printf '%s\n' "$suffix"
    done
    printf '}\n'
)

attest_json_read() (
    local file=$1 fields=$2 output=$3 scratch key line scalar value ch index next
    local -a keys=()
    prov_regular "$file" || exit 1
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    mapfile -t keys < "$fields" || exit 1
    exec 3< "$file" || exit 1
    IFS= read -r line <&3 && [[ "$line" == '{' ]] || exit 1
    : > "$scratch/values"
    for key in "${keys[@]}"; do
        IFS= read -r line <&3 || exit 1
        [[ "$line" == "  \"$key\": "* ]] || exit 1
        scalar=${line#"  \"$key\": "}; scalar=${scalar%,}
        if [[ "$key" == worktree_matches_index || ( "$key" == base_revision && "$scalar" == null ) ]]; then
            value=$scalar
        else
            [[ "$scalar" == \"*\" ]] || exit 1
            scalar=${scalar:1:${#scalar}-2}; value=''; index=0
            while (( index < ${#scalar} )); do
                ch=${scalar:index:1}
                if [[ "$ch" == '\' ]]; then
                    index=$((index + 1)); next=${scalar:index:1}
                    [[ "$next" == '\' || "$next" == '"' ]] || exit 1
                    ch=$next
                elif [[ "$ch" == '"' ]]; then exit 1; fi
                value+=$ch; index=$((index + 1))
            done
        fi
        attest_value_valid "$key" "$value" || exit 1
        printf '%s=%s\n' "$key" "$value" >> "$scratch/values"
    done
    attest_json_write "$fields" "$scratch/values" > "$scratch/canonical" || exit 1
    cmp -s "$file" "$scratch/canonical" || exit 1
    cp -- "$scratch/values" "$output"
)

attest_candidate_state() (
    local root=$1 out=$2 scratch record metadata path mode blob stage actual prefix key value
    local head_state=commit revision index_tree candidate_hash untracked_hash
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    prov_directory "$root" || exit 1
    revision=$(git -C "$root" rev-parse --verify HEAD 2>/dev/null) || { head_state=unborn; revision=null; }
    [[ "$revision" == null || "$revision" =~ ^[0-9a-f]{40}$ ]] || exit 1
    git -C "$root" ls-files --stage -z > "$scratch/index" || exit 1
    : > "$scratch/tracked"
    while IFS= read -r -d '' record; do
        metadata=${record%%$'\t'*}; path=${record#*$'\t'}
        read -r mode blob stage <<< "$metadata"
        prov_safe_relative "$path" && [[ "$stage" == 0 ]] || exit 1
        actual=$(prov_mode "$root/$path") || exit 1
        [[ "$mode" == "$actual" ]] || { prov_error "worktree mode differs from index: $path"; exit 1; }
        actual=$(git -C "$root" hash-object --no-filters -- "$path") || exit 1
        [[ "$blob" == "$actual" ]] || { prov_error "worktree bytes differ from index: $path"; exit 1; }
        printf '%s\n' "$path" >> "$scratch/tracked"
    done < "$scratch/index"
    git -C "$root" ls-files --others --exclude-standard -z > "$scratch/others" || exit 1
    : > "$scratch/untracked"
    while IFS= read -r -d '' path; do
        prov_safe_relative "$path" || exit 1
        printf '%s\n' "$path" >> "$scratch/untracked"
    done < "$scratch/others"
    LC_ALL=C sort -o "$scratch/untracked" "$scratch/untracked" || exit 1
    LC_ALL=C sort "$scratch/tracked" "$scratch/untracked" > "$scratch/paths" || exit 1
    index_tree=$(git -C "$root" write-tree) || exit 1
    candidate_hash=$(prov_files_digest "$root" nauqtype-candidate/v1 "$scratch/paths") || exit 1
    untracked_hash=$(prov_files_digest "$root" nauqtype-untracked/v1 "$scratch/untracked") || exit 1
    {
        printf 'head_state=%s\nbase_revision=%s\nindex_tree=%s\n' "$head_state" "$revision" "$index_tree"
        printf 'candidate_sha256=%s\n' "$candidate_hash"
        printf 'untracked_sha256=%s\n' "$untracked_hash"
        for prefix in bootstrap proof; do
            if [[ "$prefix" == bootstrap ]]; then value=${CC:-cc}; else value=cc; fi
            prov_cc_identity "$value" "$scratch/cc" || exit 1
            while IFS='=' read -r key value; do printf '%s_%s=%s\n' "$prefix" "$key" "$value"; done < "$scratch/cc"
            if [[ "$prefix" == bootstrap ]]; then value=$(prov_bootstrap_flags_sha256) || exit 1;
            else value=$(prov_proof_flags_sha256) || exit 1; fi
            printf '%s_flags_sha256=%s\n' "$prefix" "$value"
        done
    } > "$out"
    attest_start_fields > "$scratch/fields"
    attest_json_write "$scratch/fields" "$out" > "$scratch/checked" || exit 1
)

attest_artifacts() (
    local root=$1 key path hash scratch
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    seed_verify "$root" || exit 1
    "$root/scripts/stage1_cache.sh" require > /dev/null || exit 1
    for key in seed_manifest seed_c seed_runtime_c seed_runtime_h driver stage1_c cache_receipt wrapper proof_summary release_manifest; do
        case "$key" in
            seed_manifest) path=bootstrap/seed/manifest.json;;
            seed_c) path=bootstrap/seed/nauqc-seed.c;;
            seed_runtime_c) path=bootstrap/seed/runtime.c;;
            seed_runtime_h) path=bootstrap/seed/runtime.h;;
            driver) path=selfhost/build/nauqc;;
            stage1_c) path=build/seed/stage1.c;;
            cache_receipt) path=build/seed/stage1-derivation-v1.txt;;
            wrapper) path=bin/nauqc;;
            proof_summary) path=build/proof/summary.json;;
            release_manifest) path=build/linux-release/nauqtype/share/nauqtype/release.json;;
        esac
        hash=$(prov_sha256 "$root/$path") || exit 1
        printf '%s_sha256=%s\n' "$key" "$hash"
    done
    prov_tree_paths "$root" build/linux-release/nauqtype all > "$scratch" || exit 1
    sed -i 's#^build/linux-release/nauqtype/##' "$scratch" || exit 1
    hash=$(prov_files_digest "$root/build/linux-release/nauqtype" nauqtype-release-tree/v1 "$scratch") || exit 1
    printf 'release_tree_sha256=%s\n' "$hash"
)

attest_render() (
    local root=$1 before=$2 after=$3 output=$4 scratch key value
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    cmp -s "$before" "$after" || { prov_error 'candidate or toolchain changed during gate'; exit 1; }
    {
        printf 'version=milestone-attestation/v1\ncommand=check-milestone\nstatus=ok\n'
        while IFS='=' read -r key value; do
            case "$key" in
                index_tree|candidate_sha256) printf '%s_before=%s\n%s_after=%s\n' "$key" "$value" "$key" "$value";;
                *) printf '%s=%s\n' "$key" "$value";;
            esac
        done < "$before"
        printf 'worktree_matches_index=true\n'
        attest_artifacts "$root" || exit 1
    } > "$scratch/values"
    attest_fields > "$scratch/fields"
    attest_json_write "$scratch/fields" "$scratch/values" > "$output"
)

attest_begin() (
    local root=$1 dir=$1/build/verification scratch
    mkdir -p "$dir" || exit 1
    rm -f -- "$dir/milestone-attestation-v1.json" "$dir/milestone-close-v1.json" "$dir/milestone-close-delta-v1.txt"
    scratch=$(mktemp -d "$dir/attest-begin-XXXXXX") || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    attest_candidate_state "$root" "$scratch/state" || exit 1
    attest_start_fields > "$scratch/fields"
    attest_json_write "$scratch/fields" "$scratch/state" > "$scratch/start.json" || exit 1
    mv -- "$scratch/start.json" "$dir/milestone-start-v1.json"
)

attest_finish() (
    local root=$1 dir=$1/build/verification scratch
    scratch=$(mktemp -d "$dir/attest-finish-XXXXXX") || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    attest_start_fields > "$scratch/fields"
    attest_json_read "$dir/milestone-start-v1.json" "$scratch/fields" "$scratch/before" || exit 1
    attest_candidate_state "$root" "$scratch/after" || exit 1
    attest_render "$root" "$scratch/before" "$scratch/after" "$scratch/attestation" || exit 1
    mv -- "$scratch/attestation" "$dir/milestone-attestation-v1.json"
)

attest_verify() (
    local root=$1 file=${2:-$1/build/verification/milestone-attestation-v1.json} scratch
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    attest_candidate_state "$root" "$scratch/state" || exit 1
    attest_render "$root" "$scratch/state" "$scratch/state" "$scratch/expected" || exit 1
    prov_regular "$file" && cmp -s "$file" "$scratch/expected" || { prov_error 'milestone attestation does not match current candidate/artifacts'; exit 1; }
    printf 'milestone attestation ok\n'
)

attest_tree_materialize() (
    local root=$1 tree=$2 dest=$3 list=$4 scratch record metadata path mode kind blob
    scratch=$(mktemp) || exit 1
    trap 'rm -f -- "$scratch"' EXIT
    mkdir -p "$dest" || exit 1
    git -C "$root" ls-tree -r -z "$tree" > "$scratch" || exit 1
    : > "$list"
    while IFS= read -r -d '' record; do
        metadata=${record%%$'\t'*}; path=${record#*$'\t'}
        read -r mode kind blob <<< "$metadata"
        prov_safe_relative "$path" && [[ "$kind" == blob && ( "$mode" == 100644 || "$mode" == 100755 ) ]] || exit 1
        if [[ "$path" == */* ]]; then mkdir -p "$dest/${path%/*}" || exit 1; fi
        git -C "$root" cat-file blob "$blob" > "$dest/$path" || exit 1
        if [[ "$mode" == 100755 ]]; then chmod 755 "$dest/$path"; else chmod 644 "$dest/$path"; fi
        printf '%s\n' "$path" >> "$list"
    done < "$scratch"
    LC_ALL=C sort -o "$list" "$list"
)

attest_closing_artifacts() (
    local root=$1 attestation=$2 commit=$3 output=$4 delta=$5 scratch key value final_tree candidate_tree
    local record metadata path old_mode new_mode old_blob new_blob status before_hash after_hash
    local -A fields=()
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    attest_fields > "$scratch/fields"
    attest_json_read "$attestation" "$scratch/fields" "$scratch/values" || exit 1
    while IFS='=' read -r key value; do fields[$key]=$value; done < "$scratch/values"
    [[ "${fields[version]}" == milestone-attestation/v1 ]] || exit 1
    candidate_tree=${fields[index_tree_after]}
    [[ "$candidate_tree" == "${fields[index_tree_before]}" && "${fields[candidate_sha256_before]}" == "${fields[candidate_sha256_after]}" ]] || exit 1
    : > "$scratch/empty"
    [[ "${fields[untracked_sha256]}" == "$(prov_files_digest "$root" nauqtype-untracked/v1 "$scratch/empty")" ]] || { prov_error 'closing requires a fully indexed candidate'; exit 1; }
    attest_tree_materialize "$root" "$candidate_tree" "$scratch/candidate" "$scratch/paths" || exit 1
    [[ "${fields[candidate_sha256_after]}" == "$(prov_files_digest "$scratch/candidate" nauqtype-candidate/v1 "$scratch/paths")" ]] || exit 1
    [[ "$commit" =~ ^[0-9a-f]{40}$ ]] || exit 1
    [[ "$(git -C "$root" cat-file -t "$commit")" == commit ]] || exit 1
    final_tree=$(git -C "$root" rev-parse "$commit^{tree}") || exit 1
    git -C "$root" diff-tree --no-commit-id --raw --no-renames -r -z "$candidate_tree" "$final_tree" > "$scratch/diff" || exit 1
    printf 'milestone-close-delta/v1\n' > "$delta"
    while IFS= read -r -d '' metadata; do
        IFS= read -r -d '' path || exit 1
        read -r old_mode new_mode old_blob new_blob status <<< "$metadata"
        old_mode=${old_mode#:}
        [[ "$status" == M && "$old_mode" == "$new_mode" && ( "$old_mode" == 100644 || "$old_mode" == 100755 ) ]] || exit 1
        case "$path" in
            M54_10_CONTRACTS.md|AUDIT_REMEDIATION.md|ROADMAP.md|TODO.md|NAUQTYPE_COORDINATION.md) ;;
            *) prov_error "non-completion change after gate: $path"; exit 1;;
        esac
        git -C "$root" cat-file blob "$old_blob" > "$scratch/before" || exit 1
        git -C "$root" cat-file blob "$new_blob" > "$scratch/after" || exit 1
        before_hash=$(prov_sha256 "$scratch/before") || exit 1
        after_hash=$(prov_sha256 "$scratch/after") || exit 1
        printf 'path-bytes:%d\n%s\nbefore:%s\nafter:%s\n' "${#path}" "$path" "$before_hash" "$after_hash" >> "$delta"
    done < "$scratch/diff"
    {
        printf 'version=milestone-close/v1\nattestation_sha256=%s\n' "$(prov_sha256 "$attestation")"
        printf 'final_commit=%s\nfinal_tree=%s\ncandidate_tree=%s\n' "$commit" "$final_tree" "$candidate_tree"
        printf 'documentation_delta_sha256=%s\nstatus=ok\n' "$(prov_sha256 "$delta")"
    } > "$scratch/close-values"
    attest_close_fields > "$scratch/close-fields"
    attest_json_write "$scratch/close-fields" "$scratch/close-values" > "$output"
)

attest_close() (
    local root=$1 commit=$2 dir=$1/build/verification scratch
    scratch=$(mktemp -d "$dir/attest-close-XXXXXX") || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    attest_closing_artifacts "$root" "$dir/milestone-attestation-v1.json" "$commit" "$scratch/record" "$scratch/delta" || exit 1
    mv -- "$scratch/delta" "$dir/milestone-close-delta-v1.txt" || exit 1
    mv -- "$scratch/record" "$dir/milestone-close-v1.json"
)

attest_verify_close() (
    local root=$1 dir=$1/build/verification scratch key value commit=''
    scratch=$(mktemp -d) || exit 1
    trap 'rm -rf -- "$scratch"' EXIT
    attest_close_fields > "$scratch/fields"
    attest_json_read "$dir/milestone-close-v1.json" "$scratch/fields" "$scratch/values" || exit 1
    while IFS='=' read -r key value; do if [[ "$key" == final_commit ]]; then commit=$value; fi; done < "$scratch/values"
    attest_closing_artifacts "$root" "$dir/milestone-attestation-v1.json" "$commit" "$scratch/record" "$scratch/delta" || exit 1
    cmp -s "$dir/milestone-close-v1.json" "$scratch/record" || exit 1
    cmp -s "$dir/milestone-close-delta-v1.txt" "$scratch/delta" || exit 1
    printf 'milestone closing evidence ok\n'
)

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    root="$(cd -- "$script_dir/.." && pwd -P)"
    case "${1:-}" in
        begin) attest_begin "$root";;
        finish) attest_finish "$root";;
        verify) attest_verify "$root" "${2:-$root/build/verification/milestone-attestation-v1.json}";;
        close) attest_close "$root" "${2:-$(git -C "$root" rev-parse HEAD)}";;
        verify-close) attest_verify_close "$root";;
        *) printf 'usage: scripts/milestone_attestation.sh begin|finish|verify [attestation]|close [commit]|verify-close\n' >&2; exit 2;;
    esac
fi
