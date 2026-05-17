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
if [[ -d build/linux-release/nauqtype/share/nauqtype/examples/build ]]; then
    printf 'linux alpha: copied release contains generated examples/build artifacts\n' >&2
    exit 1
fi
if find build/linux-release/nauqtype/share/nauqtype/examples -name '*.exe' -print -quit | grep -q .; then
    printf 'linux alpha: copied release contains .exe artifacts\n' >&2
    exit 1
fi
build/linux-release/nauqtype/bin/nauqc check examples/hello.nq
build/linux-release/nauqtype/bin/nauqc run examples/hello.nq
