#!/usr/bin/env bash
set -euo pipefail

# Focused oracle comparison, not a cache publisher or replacement seed proof.
(( $# == 2 )) || { printf 'Usage: scripts/check_e1_normalizer.sh <frozen-reference-driver> <candidate-driver>\n' >&2; exit 2; }
reference=$(realpath -- "$1")
candidate=$(realpath -- "$2")
[[ -x "$reference" && -x "$candidate" ]] || exit 2
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
    printf 'PASS normalizer oracle: %s\n' "$label"
    count=$((count + 1))
}

base=$'int nqv_13_x = 1;\nint nq_tmp_8 = nqv_13_x + 2;\nreturn nq_tmp_8;\n'
pair identity 0 "$base" "$base"
pair remap 0 "$base" $'int nqv_90_x = 1;\nint nq_tmp_34 = nqv_90_x + 2;\nreturn nq_tmp_34;\n'
pair trim-and-empty-lines 0 "$base" $' \n\tint nqv_90_x = 1;  \n\n int nq_tmp_34 = nqv_90_x + 2;\t\nreturn nq_tmp_34;\n\n'
pair final-newline 0 "$base" $'int nqv_90_x = 1;\nint nq_tmp_34 = nqv_90_x + 2;\nreturn nq_tmp_34;'
pair binding-name 1 "$base" $'int nqv_90_y = 1;\nint nq_tmp_34 = nqv_90_y + 2;\nreturn nq_tmp_34;\n'
pair operator 1 "$base" $'int nqv_90_x = 1;\nint nq_tmp_34 = nqv_90_x - 2;\nreturn nq_tmp_34;\n'
pair control-flow 1 "$base" $'int nqv_90_x = 1;\nint nq_tmp_34 = nqv_90_x + 2;\nif (0) return nq_tmp_34;\n'
pair mapping-reuse 1 "$base" $'int nqv_90_x = 1;\nint nq_tmp_34 = nqv_91_x + 2;\nreturn nq_tmp_34;\n'
pair order 1 $'int nqv_1_x;\nint nqv_2_y;\n' $'int nqv_90_y;\nint nqv_91_x;\n'
pair empty 0 $' \n\t\n' ''
pair internal-space 1 'return 1 + 2;' 'return 1+2;'
pair token-boundaries 0 $'nqv_7_ nq_tmp_x nqv_x_name nq_tmp_004 nq_tmp_004\n' $'nqv_7_ nq_tmp_x nqv_x_name nq_tmp_33 nq_tmp_33\n'
pair leading-zero-distinction 1 'nqv_01_x nqv_1_x' 'nqv_1_x nqv_1_x'
printf -v long '%20000s' ''
long=${long// /x}
pair long-line 0 "$long" "$long"
pair long-line-mismatch 1 "$long" "${long}y"
printf 'normalizer oracle passed (%s pairs)\n' "$count"
