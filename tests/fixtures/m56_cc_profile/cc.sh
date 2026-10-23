#!/usr/bin/env bash
set -euo pipefail

case "${1:-}" in
    --version) printf 'm56 synthetic cc v1\n'; exit 0;;
    -dumpmachine) printf 'm56-fixture-linux\n'; exit 0;;
    -Q)
        [[ $# == 2 && "$2" == --help=params ]]
        case "${NQ_TEST_CC_MODE:-gcc}" in
            gcc)
                printf '  --param=ggc-min-expand=      100\n'
                printf '  --param=ggc-min-heapsize=   131072\n';;
            portable) printf 'no supported parameter rows\n';;
            exit1) exit 1;;
            exit2) exit 2;;
            duplicate)
                printf '  --param=ggc-min-expand=      100\n'
                printf '  --param=ggc-min-expand=      100\n'
                printf '  --param=ggc-min-heapsize=   131072\n';;
            malformed)
                printf '  --param=ggc-min-expand=      enabled\n'
                printf '  --param=ggc-min-heapsize=   131072\n';;
            stderr)
                printf '  --param=ggc-min-expand=      100\n'
                printf '  --param=ggc-min-heapsize=   131072\n'
                printf 'synthetic warning\n' >&2;;
            timeout) sleep 5;;
            signal) kill -TERM "$$";;
            oversize) awk 'BEGIN { for (i=0; i<70000; i++) printf "x"; printf "\n" }';;
            exact64k-exit1)
                awk 'BEGIN { for (i=0; i<65536; i++) printf "x" }'
                exit 1;;
            overflow-stdout-exit1)
                set +e
                awk 'BEGIN { for (i=0; i<80000; i++) printf "x" }'
                exit 1;;
            overflow-stderr-exit2)
                set +e
                awk 'BEGIN { for (i=0; i<80000; i++) printf "x" }' >&2
                exit 2;;
            identity-change)
                printf '  --param=ggc-min-expand=      100\n'
                printf '  --param=ggc-min-heapsize=   131072\n'
                printf '\n# changed during probe\n' >> "$0";;
            *) exit 70;;
        esac
        exit 0;;
esac

[[ $# == 8 || $# == 10 ]]
[[ "$1" == -std=c11 && "$2" == -O2 && "$3" == -D_POSIX_C_SOURCE=200809L && "$7" == -o ]]
if (( $# == 10 )); then
    [[ "$9" == --param=ggc-min-expand=20 && "${10}" == --param=ggc-min-heapsize=32768 ]]
fi
if [[ -n "${NQ_TEST_ARGV_LOG:-}" ]]; then printf '%s\0' "$@" > "$NQ_TEST_ARGV_LOG"; fi
printf '#!/usr/bin/env bash\nexit 0\n' > "$8"
chmod +x "$8"
