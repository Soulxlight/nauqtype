#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
release_root="${1:-$repo_root/build/linux-release/nauqtype}"
if [[ ! -d "$release_root" ]]; then
    printf 'linux release verify: missing release root %s\n' "$release_root" >&2
    exit 1
fi
release_root="$(cd -- "$release_root" && pwd -P)"
version="$(tr -d '[:space:]' < "$repo_root/VERSION")"
release_id="nauqtype-$version"

require_file() {
    local path="$1"
    if [[ ! -f "$release_root/$path" ]]; then
        printf 'linux release verify: missing file %s\n' "$path" >&2
        exit 1
    fi
}

require_dir() {
    local path="$1"
    if [[ ! -d "$release_root/$path" ]]; then
        printf 'linux release verify: missing directory %s\n' "$path" >&2
        exit 1
    fi
}

require_exe() {
    local path="$1"
    require_file "$path"
    if [[ ! -x "$release_root/$path" ]]; then
        printf 'linux release verify: expected executable %s\n' "$path" >&2
        exit 1
    fi
}

require_exe "bin/nauqc"
require_exe "lib/nauqtype/nauqc-stage1"
require_file "lib/nauqtype/stdlib/runtime.h"
require_file "lib/nauqtype/stdlib/runtime.c"
require_file "share/nauqtype/VERSION"
require_file "share/nauqtype/release.json"
require_dir "share/nauqtype/schemas"
require_dir "share/nauqtype/examples"
require_file "share/doc/nauqtype/README.md"
require_file "share/doc/nauqtype/LINUX.md"
require_file "share/doc/nauqtype/LINUX_RELEASE_MANIFEST.md"

verify_cli_golden() {
    local label="$1"
    local executable="$2"
    local cwd="$3"
    local golden="$4"
    shift 4
    local actual
    local errors
    actual="$(mktemp)"
    errors="$(mktemp)"
    if ! (cd "$cwd" && "$executable" "$@") > "$actual" 2> "$errors"; then
        printf 'linux release verify: %s command failed\n' "$label" >&2
        cat "$errors" >&2
        rm -f "$actual" "$errors"
        exit 1
    fi
    if [[ -s "$errors" ]]; then
        printf 'linux release verify: %s produced unexpected stderr\n' "$label" >&2
        cat "$errors" >&2
        rm -f "$actual" "$errors"
        exit 1
    fi
    if ! cmp -s "$golden" "$actual"; then
        printf 'linux release verify: %s output does not match %s\n' "$label" "$golden" >&2
        rm -f "$actual" "$errors"
        exit 1
    fi
    rm -f "$actual" "$errors"
}

if [[ "$(tr -d '[:space:]' < "$release_root/share/nauqtype/VERSION")" != "$version" ]]; then
    printf 'linux release verify: copied VERSION does not match repo VERSION\n' >&2
    exit 1
fi

expected_version="$(mktemp)"
printf 'nauqc %s\n' "$version" > "$expected_version"
if ! cmp -s "$repo_root/tests/golden/cli/version.txt" "$expected_version"; then
    printf 'linux release verify: version golden does not match repo VERSION\n' >&2
    rm -f "$expected_version"
    exit 1
fi
rm -f "$expected_version"

public_driver="$release_root/bin/nauqc"
direct_driver="$release_root/lib/nauqtype/nauqc-stage1"
driver_cwd="$release_root/lib/nauqtype"
for alias in help --help -h; do
    verify_cli_golden "public $alias" "$public_driver" "$release_root" "$repo_root/tests/golden/cli/help.txt" "$alias"
done
for alias in version --version -V; do
    verify_cli_golden "public $alias" "$public_driver" "$release_root" "$repo_root/tests/golden/cli/version.txt" "$alias"
done
verify_cli_golden "direct help" "$direct_driver" "$driver_cwd" "$repo_root/tests/golden/cli/help.txt" help
verify_cli_golden "direct version" "$direct_driver" "$driver_cwd" "$repo_root/tests/golden/cli/version.txt" version

require_json_field() {
    local key="$1"
    local value="$2"
    if ! grep -q "\"$key\": \"$value\"" "$release_root/share/nauqtype/release.json"; then
        printf 'linux release verify: release.json missing %s=%s\n' "$key" "$value" >&2
        exit 1
    fi
}

require_json_field "version" "$version"
require_json_field "release_id" "$release_id"
require_json_field "layout" "linux-alpha-rc1"
require_json_field "public_driver" "bin/nauqc"
require_json_field "stage1_driver" "lib/nauqtype/nauqc-stage1"
require_json_field "stdlib" "lib/nauqtype/stdlib"
require_json_field "schemas" "share/nauqtype/schemas"
require_json_field "examples" "share/nauqtype/examples"

verify_tracked_tree() {
    local git_pattern="$1"
    local release_prefix="$2"
    local expected_list
    local actual_list
    expected_list="$(mktemp)"
    actual_list="$(mktemp)"
    trap 'rm -f "$expected_list" "$actual_list"' RETURN
    (cd "$repo_root" && git ls-files "$git_pattern" | sed 's#^#share/nauqtype/#' | sort) > "$expected_list"
    (cd "$release_root/$release_prefix" && find . -type f -printf '%P\n' | sed "s#^#$release_prefix/#" | sort) > "$actual_list"
    if ! cmp -s "$expected_list" "$actual_list"; then
        printf 'linux release verify: copied %s tree does not match tracked files\n' "$release_prefix" >&2
        printf 'expected:\n' >&2
        cat "$expected_list" >&2
        printf 'actual:\n' >&2
        cat "$actual_list" >&2
        exit 1
    fi
    rm -f "$expected_list" "$actual_list"
    trap - RETURN
}

verify_tracked_tree 'schemas/*' 'share/nauqtype/schemas'
verify_tracked_tree 'examples/*' 'share/nauqtype/examples'

if [[ -d "$release_root/share/nauqtype/examples/build" ]]; then
    printf 'linux release verify: copied release contains generated examples/build artifacts\n' >&2
    exit 1
fi
if find "$release_root/share/nauqtype/examples" -name '*.exe' -print -quit | grep -q .; then
    printf 'linux release verify: copied release contains .exe artifacts\n' >&2
    exit 1
fi

printf 'linux release verify ok: %s\n' "$release_id"
