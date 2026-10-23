#!/usr/bin/env bash
# Sourced proof-input helpers; no compiler or public command lives here.

release_generic_smoke_roots() {
    local root=$1 project=$2 root_real project_real
    prov_directory "$root" && prov_directory "$project" || return 1
    root_real=$(realpath -e -- "$root") || return 1
    project_real=$(realpath -e -- "$project") || return 1
    case "$project_real/" in "$root_real/"*) return 1;; esac
}

release_generic_smoke_pin() {
    local root=$1 paths=$2 digest=$3
    prov_flat_loading "$root/examples" || return 1
    printf '%s\n' examples/generic_reuse.nq examples/generic_values.nq > "$paths" || return 1
    prov_files_digest "$root" nauqtype-generic-smoke/v1 "$paths" > "$digest" || return 1
    prov_hex "$(< "$digest")"
}

release_generic_smoke_check() {
    local root=$1 project=$2 paths=$3 expected=$4 current
    release_generic_smoke_roots "$root" "$project" || return 1
    prov_hex "$expected" || return 1
    prov_flat_loading "$root/examples" || return 1
    prov_flat_loading "$project/examples" || return 1
    current=$(prov_files_digest "$root" nauqtype-generic-smoke/v1 "$paths") || return 1
    [[ "$current" == "$expected" ]] || return 1
    current=$(prov_files_digest "$project" nauqtype-generic-smoke/v1 "$paths") || return 1
    [[ "$current" == "$expected" ]]
}

release_generic_smoke_copy() {
    local root=$1 project=$2 paths=$3 expected=$4 current
    release_generic_smoke_roots "$root" "$project" || return 1
    prov_flat_loading "$root/examples" || return 1
    current=$(prov_files_digest "$root" nauqtype-generic-smoke/v1 "$paths") || return 1
    [[ "$current" == "$expected" ]] || return 1
    mkdir -p -- "$project/examples" || return 1
    cp --preserve=mode -- "$root/examples/generic_reuse.nq" "$root/examples/generic_values.nq" "$project/examples/" || return 1
    release_generic_smoke_check "$root" "$project" "$paths" "$expected"
}
