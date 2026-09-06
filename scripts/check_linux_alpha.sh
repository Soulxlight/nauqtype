#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

usage() {
    cat <<'EOF'
Usage: scripts/check_linux_alpha.sh [--reuse-stage1] [--skip-prove]

Run the Linux Alpha RC1 release-layout gate.

  --reuse-stage1  Reuse a hash-verified selfhost/build/nauqc from this
                  verification run instead of rebuilding it with the seed.
  --skip-prove    Skip the repo-local `nauqc prove` run when the caller has
                  already run it in this verification run.

Without flags this remains the standalone, release-grade Alpha gate.
EOF
}

reuse_stage1=false
skip_prove=false
while (( $# > 0 )); do
    case "$1" in
        --reuse-stage1)
            reuse_stage1=true
            ;;
        --skip-prove)
            skip_prove=true
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            printf 'check_linux_alpha: unknown option %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if "$reuse_stage1"; then
    scripts/stage1_cache.sh require
else
    scripts/build_stage1_from_seed.sh >/dev/null
fi

test -x scripts/make_linux_release.sh
bin/nauqc check examples/hello.nq
bin/nauqc run examples/hello.nq
if ! "$skip_prove"; then
    bin/nauqc prove
fi
scripts/make_linux_release.sh
scripts/verify_linux_release.sh build/linux-release/nauqtype

smoke_root="$(mktemp -d -t nauqtype-linux-alpha-rc1-XXXXXX)"
trap 'rm -rf "$smoke_root"' EXIT
cp -R build/linux-release/nauqtype "$smoke_root/nauqtype"
mkdir -p "$smoke_root/project"
cp examples/hello.nq "$smoke_root/project/hello.nq"
cp tests/fixtures/m54_runtime.nq "$smoke_root/project/m54_runtime.nq"
cp tests/fixtures/m55_process/runtime.nq "$smoke_root/project/m55_process.nq"
cp -R tests/fixtures/m54_library_dependency "$smoke_root/library-project"
rm -rf "$smoke_root/library-project/src/app/build"
(
    cd "$smoke_root/project"
    "$smoke_root/nauqtype/bin/nauqc" check hello.nq
    "$smoke_root/nauqtype/bin/nauqc" run hello.nq
    "$smoke_root/nauqtype/bin/nauqc" check m54_runtime.nq
    "$smoke_root/nauqtype/bin/nauqc" run m54_runtime.nq
    "$smoke_root/nauqtype/bin/nauqc" check m55_process.nq
    "$smoke_root/nauqtype/bin/nauqc" run m55_process.nq
)
(
    cd "$smoke_root/library-project"
    "$smoke_root/nauqtype/bin/nauqc" check vendor/std/src/status.nq
    "$smoke_root/nauqtype/bin/nauqc" check src/app/main.nq
    "$smoke_root/nauqtype/bin/nauqc" facts src/app/main.nq --format v3 >/dev/null
    "$smoke_root/nauqtype/bin/nauqc" review src/app/main.nq --format v2 >/dev/null
    "$smoke_root/nauqtype/bin/nauqc" build src/app/main.nq -o build/m54-library
    test "$("$smoke_root/nauqtype/bin/nauqc" run src/app/main.nq)" = "m54 library ready"
)
