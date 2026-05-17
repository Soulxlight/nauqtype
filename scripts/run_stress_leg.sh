#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

stamp="$(date +%Y%m%d-%H%M%S)"
work="${TMPDIR:-/tmp}/nauqtype-stress-leg-$stamp-$$"
mkdir -p "$work/build"

cat > "$work/math.nq" <<'NQ'
pub fn add(left: i32, right: i32) -> i32
audit {
    intent("Add two values for the stress leg.");
    mutates();
    effects();
}
{
    return left + right;
}

pub fn double(value: i32) -> i32
audit {
    intent("Double a value for the stress leg.");
    mutates();
    effects();
}
{
    return value + value;
}
NQ

cat > "$work/data.nq" <<'NQ'
use math;

pub type Packet {
    seed: i32,
    total: i32,
}

pub enum Choice {
    Keep(i32),
    Boost(i32),
    Stop,
}

pub fn make_packet(seed: i32, total: i32) -> Packet
audit {
    intent("Build the stress-leg packet.");
    mutates();
    effects();
}
{
    return Packet { seed: seed, total: total };
}

pub fn bump(packet: Packet, bonus: i32) -> Packet
audit {
    intent("Use record update and a qualified named call.");
    mutates();
    effects();
}
{
    let next = math::add(left: packet.total, right: bonus);
    return Packet { from packet, total: next };
}

pub fn choose(value: i32) -> Choice
audit {
    intent("Choose a qualified enum path for match-expression coverage.");
    mutates();
    effects();
}
{
    if value > 8 {
        return Boost(value);
    }
    if value == 0 {
        return Stop;
    }
    return Keep(value);
}
NQ

cat > "$work/io_util.nq" <<'NQ'
pub fn load_text(path: str) -> result<str, io_err>
audit {
    intent("Load text for the stress leg and propagate unchanged IO errors.");
    mutates();
    effects(io);
    propagates(io_err);
}
{
    let text = read_file(path)?;
    return Ok(text);
}
NQ

cat > "$work/main.nq" <<'NQ'
use data;
use io_util;
use math;

fn load_bonus() -> result<i32, io_err>
audit {
    intent("Exercise statement-boundary propagation through an imported helper.");
    mutates();
    effects(io);
    propagates(io_err);
}
{
    let text = io_util::load_text("stress_input.txt")?;
    return Ok(str_len(text));
}

fn loop_score(limit: i32) -> i32
audit {
    intent("Exercise nested if with break and continue inside while.");
    mutates();
    effects();
}
{
    let mut index = 0;
    let mut total = 0;
    while index < limit {
        index = index + 1;
        if index < 5 {
            if index == 2 {
                continue;
            }
            if index == 4 {
                break;
            }
            total = total + index;
        }
    }
    return total;
}

fn score_choice(choice: Choice) -> i32
audit {
    intent("Exercise qualified enum constructors in a match expression.");
    mutates();
    effects();
}
{
    let score = match choice {
        data::Keep(value) => value,
        data::Boost(value) => value + 1,
        data::Stop => 0,
    };
    return score;
}

fn main() -> i32
audit {
    intent("Run the dense stress leg.");
    mutates();
    effects(print, io);
}
{
    let loaded = load_bonus();
    let Ok(bonus) = loaded else {
        return 2;
    };

    let packet = data::make_packet(seed: 2, total: 3);
    let updated = data::bump(packet, bonus);
    let choice = data::choose(updated.total);
    let choice_score = score_choice(choice);
    let looped = loop_score(6);
    let numbers: list<i32> = [updated.total, bonus, looped, math::double(2)];
    let first = list_get(ref numbers, 0);
    let Some(first_value) = first else {
        return 3;
    };

    let total = math::add(left: first_value, right: choice_score) + list_len(ref numbers);
    if total == 20 and looped == 4 {
        print_line("stress ok");
        return 0;
    }
    return 1;
}
NQ

printf 'hello' > "$work/stress_input.txt"

bin/nauqc check "$work/main.nq"
bin/nauqc review "$work/main.nq" --format v2 > "$work/build/review-v2.json"
bin/nauqc facts "$work/main.nq" --format v2 > "$work/build/facts-v2.json"
grep -q '"propagation_sites"' "$work/build/review-v2.json"
grep -q '"propagation_site"' "$work/build/facts-v2.json"
bin/nauqc fmt --check "$work/main.nq"
bin/nauqc fmt --check "$work/data.nq"
bin/nauqc fmt --check "$work/io_util.nq"
bin/nauqc fmt --check "$work/math.nq"
bin/nauqc emit-c "$work/main.nq" -o "$work/build/stress.c"
bin/nauqc build "$work/main.nq" -o "$work/build/stress"
run_output="$(cd "$work" && build/stress)"
if [[ "$run_output" != "stress ok" ]]; then
    printf 'stress leg: unexpected runtime output: %s\n' "$run_output" >&2
    printf 'stress leg workspace kept at %s\n' "$work" >&2
    exit 1
fi

printf 'stress leg ok\n'
printf 'stress leg workspace: %s\n' "$work"
