#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

python3 -m compiler.main run selfhost/main.nq
python3 -m compiler.main build selfhost/main.nq -o selfhost/build/nauqc
bin/nauqc check examples/hello.nq
bin/nauqc run examples/hello.nq
bin/nauqc prove
scripts/make_linux_release.sh
build/linux-release/nauqtype/bin/nauqc check examples/hello.nq
build/linux-release/nauqtype/bin/nauqc run examples/hello.nq
