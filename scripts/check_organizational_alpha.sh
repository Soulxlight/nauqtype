#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

usage() {
    cat <<'EOF'
Usage: scripts/check_organizational_alpha.sh [--reuse-stage1] [--skip-prove]

Run the v0.3 organizational-alpha gate. It validates a locked two-workspace
tool with the active driver, records its checked snapshot and impact evidence,
then repeats check/facts/policy/run from a copied Linux release outside the
source checkout.

  --reuse-stage1  Reuse hash-verified stage1 artifacts from this run.
  --skip-prove    Skip repo-local `nauqc prove` after it was already run.
EOF
}

reuse_stage1=false
skip_prove=false
while (( $# > 0 )); do
    case "$1" in
        --reuse-stage1) reuse_stage1=true ;;
        --skip-prove) skip_prove=true ;;
        --help|-h) usage; exit 0 ;;
        *)
            printf 'check_organizational_alpha: unknown option %s\n' "$1" >&2
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

driver="$repo_root/bin/nauqc"
fixture="tests/fixtures/organizational_tool"
source_path="$fixture/src/app/main.nq"
policy_path="$fixture/nauqtype.policy.json"
before_path="tests/fixtures/organizational_tool_before/src/app/main.nq"
artifact_root="build/organizational-alpha"

if ! "$skip_prove"; then
    "$driver" prove >/dev/null
fi

rm -rf "$artifact_root"
mkdir -p "$artifact_root"

"$driver" check "$source_path"
"$driver" facts "$source_path" --format v3 > "$artifact_root/nauqtype.workspace.snapshot.json"
cmp -s "$artifact_root/nauqtype.workspace.snapshot.json" tests/golden/organizational_tool/facts_v3.json
"$driver" policy-check "$source_path" "$policy_path" > "$artifact_root/policy-check-v1.json"
cmp -s "$artifact_root/policy-check-v1.json" tests/golden/organizational_tool/policy_check_v1.json
"$driver" change-report "$before_path" "$source_path" --format v2 > "$artifact_root/change-report-v2.json"
cmp -s "$artifact_root/change-report-v2.json" tests/golden/organizational_tool/change_report_v2.json

tool_output="$("$driver" run "$source_path")"
if [[ "$tool_output" != "operations: ready" ]]; then
    printf 'organizational alpha: active tool output changed: %s\n' "$tool_output" >&2
    exit 1
fi

scripts/make_linux_release.sh >/dev/null
scripts/verify_linux_release.sh build/linux-release/nauqtype >/dev/null

release_root="$repo_root/build/linux-release/nauqtype"
release_driver="$release_root/bin/nauqc"
smoke_root="$(mktemp -d -t nauqtype-organizational-alpha-XXXXXX)"
trap 'rm -rf "$smoke_root"' EXIT
copied_tool="$smoke_root/operations-tool"
cp -R "$fixture" "$copied_tool"
copied_source="$copied_tool/src/app/main.nq"
copied_policy="$copied_tool/nauqtype.policy.json"

(
    cd "$smoke_root"
    "$release_driver" check "$copied_source"
    "$release_driver" facts "$copied_source" --format v3 > "$smoke_root/nauqtype.workspace.snapshot.json"
    cmp -s "$smoke_root/nauqtype.workspace.snapshot.json" "$repo_root/tests/golden/organizational_tool/facts_v3.json"
    "$release_driver" policy-check "$copied_source" "$copied_policy" > "$smoke_root/policy-check-v1.json"
    grep -F '"ok": true' "$smoke_root/policy-check-v1.json" >/dev/null
    grep -F 'workspace:org.reporting::module:render::fn:status_line' "$smoke_root/policy-check-v1.json" >/dev/null
    copied_output="$("$release_driver" run "$copied_source")"
    if [[ "$copied_output" != "operations: ready" ]]; then
        printf 'organizational alpha: copied-release tool output changed: %s\n' "$copied_output" >&2
        exit 1
    fi
)

printf 'organizational alpha proof ok\n'
