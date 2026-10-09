#!/usr/bin/env bash
set -euo pipefail

# Focused normalizer regressions; the frozen E1 oracle remains the baseline.
(( $# == 2 )) || { printf 'Usage: scripts/check_p2_normalizer.sh <frozen-reference-driver> <candidate-driver>\n' >&2; exit 2; }
reference=$(realpath -- "$1")
candidate=$(realpath -- "$2")
[[ -x "$reference" && -x "$candidate" ]] || exit 2

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ -x "$script_dir/check_e1_normalizer.sh" ]]; then
    "$script_dir/check_e1_normalizer.sh" "$reference" "$candidate"
else
    bash "$script_dir/check_e1_normalizer.sh" "$reference" "$candidate"
fi

scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
count=0

pair() {
    local label=$1 expected=$2 left=$3 right=$4 driver code prefix
    printf '%s' "$left" > "$scratch/left.c"
    printf '%s' "$right" > "$scratch/right.c"
    for prefix in reference candidate; do
        driver=$reference
        [[ "$prefix" != candidate ]] || driver=$candidate
        code=0
        "$driver" prove-seed "$scratch/left.c" "$scratch/right.c" > "$scratch/$prefix.out" 2> "$scratch/$prefix.err" || code=$?
        printf '%s\n' "$code" > "$scratch/$prefix.code"
        [[ "$code" == "$expected" ]] || { printf '%s: %s verdict %s, expected %s\n' "$label" "$prefix" "$code" "$expected" >&2; exit 1; }
    done
    cmp "$scratch/reference.code" "$scratch/candidate.code"
    cmp "$scratch/reference.out" "$scratch/candidate.out"
    cmp "$scratch/reference.err" "$scratch/candidate.err"
    printf 'PASS P2 normalizer oracle: %s\n' "$label"
    count=$((count + 1))
}

# Reusing a mapping thousands of tokens later must remain consistent.
late_left='int nqv_17_item;'
late_right='int nqv_804_item;'
for ((i = 0; i < 256; i++)); do
    late_left+=$' nqv_17_item;'
    late_right+=$' nqv_804_item;'
done
late_left+=$' return nqv_17_item;'
late_right+=$' return nqv_804_item;'
pair repeated-id-late-reuse 0 "$late_left" "$late_right"
pair repeated-id-late-conflict 1 "$late_left" "${late_right/nqv_804_item/nqv_805_item}"

# Exercise IDs beyond small implementation tables while preserving token order.
many_left=''
many_right=''
for ((i = 1; i <= 96; i++)); do
    many_left+="int nqv_${i}_v${i};"$'\n'
    mapped=$((1000 + (97 - i) * 13))
    many_right+="int nqv_${mapped}_v${i};"$'\n'
done
pair more-than-64-distinct-remapped 0 "$many_left" "$many_right"
reordered_right=$(printf '%s' "$many_right" | awk 'NF { lines[NR]=$0 } END { for (i=NR; i>=1; i--) print lines[i] }')
pair more-than-64-order-preserved 1 "$many_left" "$reordered_right"
reuse_left=$many_left
reuse_right=$many_right
reuse_left+=$'nqv_1_v1;\n'
reuse_right+="nqv_$((1000 + (97 - 1) * 13))_v1;"$'\n'
pair 96-unique-keys-then-earlier-key-reuse 0 "$reuse_left" "$reuse_right"

pair binding-and-temp-namespaces-independent 0 \
    $'int nqv_12_value = 1;\nint nq_tmp_12 = nqv_12_value;\nreturn nq_tmp_12;\n' \
    $'int nqv_900_value = 1;\nint nq_tmp_700 = nqv_900_value;\nreturn nq_tmp_700;\n'
pair binding-and-temp-namespace-crossed 1 \
    $'int nqv_12_value = 1;\nint nq_tmp_31 = nqv_12_value;\nreturn nq_tmp_31;\n' \
    $'int nqv_900_value = 1;\nint nq_tmp_700 = nq_tmp_700;\nreturn nqv_900_value;\n'

pair oversized-digit-identifiers 0 \
    'nqv_12345678901234567890123456789012345678901234567890_x nq_tmp_98765432109876543210987654321098765432109876543210' \
    'nqv_99999999999999999999999999999999999999999999999999_x nq_tmp_88888888888888888888888888888888888888888888888888'
pair leading-zero-singleton-remaps-by-first-appearance 0 'nqv_00000000000000000017_x' 'nqv_17_x'
pair leading-zero-keys-remain-distinct 0 \
    'nqv_01_x nqv_1_x nqv_01_x nqv_1_x' \
    'nqv_7_x nqv_8_x nqv_7_x nqv_8_x'
pair leading-zero-key-reuse-conflict 1 \
    'nqv_01_x nqv_1_x nqv_01_x nqv_1_x' \
    'nqv_7_x nqv_8_x nqv_9_x nqv_8_x'

pair identifiers-inside-strings-are-normalized 0 \
    'const char *s = "nqv_12_x nq_tmp_31"; nqv_12_x;' \
    'const char *s = "nqv_900_x nq_tmp_700"; nqv_900_x;'
pair string-identifier-sets-first-appearance-ordinal 1 \
    'const char *s = "nqv_12_x nq_tmp_31"; nqv_12_x;' \
    'const char *s = "nqv_12_x nq_tmp_31"; nqv_900_x;'
pair quoted-token-content-matters 1 \
    'const char *s = "nqv_12_x"; nqv_12_x;' \
    'const char *s = "nqv_13_x"; nqv_900_x;'

pair crlf-and-final-line 0 \
    $'int nqv_12_x = 1;\r\nreturn nqv_12_x;' \
    $'int nqv_900_x = 1;\r\nreturn nqv_900_x;\r\n'
pair internal-spacing-remains-significant 1 'return nqv_12_x + 2;' 'return nqv_900_x+ 2;'
pair distinct-mapping-reuse 1 \
    $'nqv_12_x nqv_12_x nqv_13_y nqv_13_y\n' \
    $'nqv_900_x nqv_901_x nqv_902_y nqv_902_y\n'
pair malformed-prefix-tokens-are-preserved 0 \
    'nqv_ nqv_x_ nqv_7_ nq_tmp_x' \
    'nqv_ nqv_x_ nqv_7_ nq_tmp_x'
pair changed-malformed-prefix-token 1 \
    'nqv_ nqv_x_ nqv_7_ nq_tmp_x' \
    'nqv_ nqv_y_ nqv_7_ nq_tmp_x'

long_suffix=''
for ((i = 1; i <= 512; i++)); do
    long_suffix+=" nqv_${i}_suffix${i};"
done
pair current-line-full-normalization 1 \
    "return 1;${long_suffix}" "return 2;${long_suffix}"

later_lines=''
for ((i = 1; i <= 512; i++)); do
    later_lines+=$'\n'
    later_lines+="nqv_${i}_suffix${i};"
done
pair early-mismatch-before-later-lines 1 \
    "return 1;${later_lines}" "return 2;${later_lines}"

printf 'P2 normalizer regressions passed (%s additional pairs; E1 baseline passed above)\n' "$count"
