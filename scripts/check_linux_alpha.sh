#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

python3 -m compiler.main run selfhost/main.nq
python3 -m compiler.main build selfhost/main.nq -o selfhost/build/nauqc
test -x scripts/make_linux_release.sh
bin/nauqc check examples/hello.nq
bin/nauqc run examples/hello.nq
bin/nauqc prove
scripts/make_linux_release.sh
scripts/verify_linux_release.sh build/linux-release/nauqtype

smoke_root="$(mktemp -d -t nauqtype-linux-alpha-rc1-XXXXXX)"
trap 'rm -rf "$smoke_root"' EXIT
cp -R build/linux-release/nauqtype "$smoke_root/nauqtype"
mkdir -p "$smoke_root/project"
cp examples/hello.nq "$smoke_root/project/hello.nq"
(
    cd "$smoke_root/project"
    "$smoke_root/nauqtype/bin/nauqc" check hello.nq
    "$smoke_root/nauqtype/bin/nauqc" run hello.nq
)
