#!/usr/bin/env bash
# Synthetic capture/readback checks, not a compiler or relocated runtime proof.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
source "$script_dir/provenance.sh"
source "$script_dir/release_generic_smoke.sh"
scratch=$(mktemp -d -t nauqtype-release-generic-inputs-XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
root="$scratch/input"
project="$scratch/relocated"
mkdir -p "$root/examples" "$project"
cp --preserve=mode -- "$repo_root/examples/generic_reuse.nq" "$repo_root/examples/generic_values.nq" "$root/examples/"
release_generic_smoke_pin "$root" "$scratch/paths" "$scratch/digest"
expected=$(< "$scratch/digest")
release_generic_smoke_copy "$root" "$project" "$scratch/paths" "$expected"
release_generic_smoke_check "$root" "$project" "$scratch/paths" "$expected"
passed=1
reject() {
    if release_generic_smoke_check "$root" "$project" "$scratch/paths" "$expected" > "$scratch/rejected.stdout" 2> "$scratch/rejected.stderr"; then
        printf 'FAIL accepted generic smoke input mutation: %s\n' "$1" >&2
        exit 1
    fi
    passed=$((passed + 1))
}
printf '\n' >> "$project/examples/generic_reuse.nq"
reject 'copied source bytes'
cp --preserve=mode -- "$root/examples/generic_reuse.nq" "$project/examples/generic_reuse.nq"
cp --preserve=mode -- "$root/examples/generic_values.nq" "$scratch/original-values.nq"
printf '\n' >> "$root/examples/generic_values.nq"
reject 'original source bytes'
cp --preserve=mode -- "$scratch/original-values.nq" "$root/examples/generic_values.nq"
printf '{}\n' > "$project/examples/nauqtype.workspace.json"
reject 'copied loading boundary'
rm -- "$project/examples/nauqtype.workspace.json"
printf '{}\n' > "$root/examples/nauqtype.workspace.lock.json"
reject 'original loading boundary'
rm -- "$root/examples/nauqtype.workspace.lock.json"
if [[ -x "$project/examples/generic_values.nq" ]]; then
    chmod a-x "$project/examples/generic_values.nq"
else
    chmod a+x "$project/examples/generic_values.nq"
fi
reject 'copied source mode'
cp --preserve=mode -- "$root/examples/generic_values.nq" "$project/examples/generic_values.nq"
release_generic_smoke_check "$root" "$project" "$scratch/paths" "$expected"
mkdir -p "$root/not-relocated"
if release_generic_smoke_copy "$root" "$root/not-relocated" "$scratch/paths" "$expected"; then
    printf 'FAIL accepted generic smoke project inside source root\n' >&2
    exit 1
fi
passed=$((passed + 1))
printf 'M56 relocated generic input fixtures passed (%s assertions; synthetic capture only)\n' "$passed"
