#!/usr/bin/env python3
"""Generate tests/fixtures/m56_2_f64/runtime_vectors.h.

Expected values come only from Python 3: repr() gives the shortest
round-tripping digits (adjusted below to ECMAScript Number::toString
notation), and float() is a correctly rounded decimal parser. Nothing here
runs the C runtime under test.
"""
import re
import struct
import sys
from decimal import Decimal, getcontext
from fractions import Fraction

getcontext().prec = 2000


def f2b(x):
    return struct.unpack('<Q', struct.pack('<d', x))[0]


def b2f(b):
    return struct.unpack('<d', struct.pack('<Q', b))[0]


def es(bits):
    x = b2f(bits)
    if x != x:
        return 'NaN'
    if x == float('inf'):
        return 'Infinity'
    if x == float('-inf'):
        return '-Infinity'
    if x == 0.0:
        return '-0' if bits >> 63 else '0'
    t = Decimal(repr(abs(x))).as_tuple()
    digits = ''.join(map(str, t.digits))
    # value = int(digits) * 10**exponent; strip trailing zeros
    exp = t.exponent
    stripped = digits.rstrip('0')
    exp += len(digits) - len(stripped)
    digits = stripped or '0'
    k = len(digits)
    n = exp + k  # value = 0.d1..dk * 10**n
    sign = '-' if x < 0 else ''
    if k <= n <= 21:
        body = digits + '0' * (n - k)
    elif 0 < n <= 21:
        body = digits[:n] + '.' + digits[n:]
    elif -6 < n <= 0:
        body = '0.' + '0' * (-n) + digits
    else:
        e = n - 1
        mant = digits[0] + ('.' + digits[1:] if k > 1 else '')
        body = mant + 'e' + ('-' if e < 0 else '+') + str(abs(e))
    return sign + body


def c_string(data):
    out = []
    for ch in data:
        if 32 <= ch < 127 and ch not in (34, 92, 63):
            out.append(chr(ch))
        else:
            out.append('\\%03o' % ch)
    return '"' + ''.join(out) + '"'


# ---------------------------------------------------------------- rendering
render = []


def add_bits(b):
    render.append((b, es(b)))


def add_f(x):
    add_bits(f2b(x))


MAXF = b2f(0x7FEFFFFFFFFFFFFF)
for x in [
    0.0, 1.0, -1.0, 0.5, -0.5, 1.5, 2.0, 10.0, 100.0, 123.0, 0.1, -0.1, 0.2, 0.3,
    0.1 + 0.2, 1.0 / 3.0, 2.0 / 3.0, 123.456, -123.456, 3.141592653589793,
    2.718281828459045, 4.35, 1e5, 1e15, 1e16, 1e20, 1e21, 1e22, 1e23, 1e-5, 1e-6,
    1e-7, 1.5e-6, 1.5e-7, 1.2345e-7, 1.0000001e-6, 9.999999999999999e-7,
    9.999999999999999e20, 123456789012345680000.0, 1.5e300, 1.0e100, 2.5e-300,
    5e-324, -5e-324, 1.5e-323, 1e-310, MAXF, -MAXF, 2.0**52, 2.0**53, 2.0**53 + 2.0,
    2.0**60, 2.0**63, 2.0**64, 2.0**70, 2.0**-1, 2.0**-10, 2.0**-20, 2.0**-24,
    2.0**-44, 2.0**-1022, 2.0**-1074, 123456789.123456789, 0.000123, 1234.5678,
    4294967295.0, 2147483648.0, -2147483648.0, 9007199254740993.0, 1.7976931348623157e308,
    8.41e21, 5.0e-7, 0.000001, 0.0000011, 100000000000000000000.0, 12345678901234567890.0,
]:
    add_f(x)
# named bit patterns
for b in [
    0x0000000000000000, 0x8000000000000000,  # +0 -0
    0x7FF0000000000000, 0xFFF0000000000000,  # +-inf
    0x7FF8000000000000, 0xFFF8000000000000,  # quiet NaN, negative NaN
    0x7FF0000000000001, 0x7FFFFFFFFFFFFFFF,  # signalling NaN, max payload
    0x000FFFFFFFFFFFFF,  # largest subnormal
    0x0010000000000000,  # smallest normal
    0x0000000000000001,  # smallest subnormal
    0x7FEFFFFFFFFFFFFF,  # max finite
    0x800FFFFFFFFFFFFF, 0x8010000000000000,
    0x3FF0000000000001,  # 1 + ulp
    0x3FEFFFFFFFFFFFFF,  # 1 - ulp/2
    0x433FFFFFFFFFFFFF,  # 2^53 - 1
]:
    add_bits(b)
# powers of two whose shortest round-trip digits are not the nearest decimal
# (asymmetric round-trip interval), plus a sampled sweep of all binades
def nearest_only(x):
    for p in range(1, 18):
        s = '%.*e' % (p - 1, abs(x))
        if float(s) == abs(x):
            m, e = s.split('e')
            return (m.replace('.', '').rstrip('0') or '0', int(e))


def shortest_digits(x):
    t = Decimal(repr(abs(x))).as_tuple()
    d = ''.join(map(str, t.digits)).rstrip('0') or '0'
    return (d, len(t.digits) - 1 + t.exponent)


asym = [k for k in range(-1074, 1024) if shortest_digits(2.0**k) != nearest_only(2.0**k)]
assert len(asym) >= 40, asym
seen = set(f2b(b2f(b)) for b, _ in render)
for k in asym + list(range(-1074, 1024, 37)):
    b = f2b(2.0**k)
    if b not in seen:
        seen.add(b)
        add_bits(b)
dedup = []
seen2 = set()
for b, s in render:
    if b not in seen2:
        seen2.add(b)
        dedup.append((b, s))
render = dedup
assert len(render) >= 150, len(render)

# ----------------------------------------------------------------- parsing
GRAMMAR = re.compile(rb'-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?')


def exact_decimal(fr):
    """Exact decimal expansion of a dyadic Fraction (string, no exponent)."""
    d = Decimal(fr.numerator) / Decimal(fr.denominator)
    s = format(d, 'f')
    assert Fraction(s) == fr
    return s


parse = []  # (bytes, expect_bits or None)


def add_parse(data):
    if isinstance(data, str):
        data = data.encode('latin-1')
    if GRAMMAR.fullmatch(data):
        v = float(data.decode('ascii'))
        if v in (float('inf'), float('-inf')):
            parse.append((data, None))
        else:
            parse.append((data, f2b(v)))
    else:
        parse.append((data, None))


rejects = [
    b'', b'-', b'+1', b'1.', b'.5', b' 1', b'1 ', b'01', b'00', b'-01', b'1e', b'1e+',
    b'1E-', b'1.e5', b'0x10', b'inf', b'Infinity', b'-inf', b'NaN', b'nan', b'1_0',
    b'1,5', b'--1', b'1.5.5', b'1e5.5', b'\x00', b'1\x00', b'1\x002', b'0\x00',
    b'1e5\x00', b'\xd9\xa1', b'1e 5', b'\n1', b'1\n', b'1f', b'1.5d', b'e5', b'-.5',
    b'1..5', b'-', b'-e5', b'1e+-5', b'\t1', b'1\r', b'0.', b'-0.', b'0e', b'1.0e',
    b'1.0e-', b'+0', b'1 e5', b'0b1', b'1.5f', b'1.5e5x', b'\xff',
]
for r in rejects:
    assert not GRAMMAR.fullmatch(r), r
    parse.append((r, None))

valid = [
    '0', '-0', '0.0', '-0.0', '1', '-1', '0.5', '1.5', '10', '123456789', '1e5', '1E5',
    '1e+5', '1e-5', '1.0e5', '1.0E+5', '-1.5e-3', '0e0', '0e999', '-0e-999', '0.1', '0.2',
    '0.3', '0.30000000000000004', '3.14159265358979323846', '2.718281828459045',
    '123456789012345678901234567890', '4.35', '5e-324', '4.9406564584124654e-324',
    '2.4703282292062327e-324', '2.4703282292062328e-324', '1e-323', '1.5e-323',
    '2.2250738585072009e-308', '2.2250738585072011e-308', '2.2250738585072014e-308',
    '2.225073858507201e-308', '1.7976931348623157e308', '1.7976931348623158e308',
    '1.7976931348623159e308', '-1.7976931348623157e308', '-1.7976931348623159e308',
    '1e308', '1e309', '-1e309', '1e-400', '-1e-400', '1e-1000', '0.0000000001',
    '9007199254740992', '9007199254740993', '9007199254740994', '9007199254740995',
    '9007199254740997', '1e22', '1e23', '8.41e21', '1e0', '1E0', '100', '1000000',
]
for v in valid:
    add_parse(v)

# exact halfway ties (and one step either side) built from exact fractions
one = Fraction(1)
ulp1 = Fraction(1, 2**52)
ties = {
    'tie 1+2^-53 (even: down to 1)': one + ulp1 / 2,
    'tie 1+3*2^-53 (even: up to 1+2^-51)': one + ulp1 + ulp1 / 2,
    'tie 2^53+1': Fraction(2**53 + 1),
    'tie 2^53+3': Fraction(2**53 + 3),
    'tie 2^54+2': Fraction(2**54 + 2),
    'tie 0.5-2^-54 (below 0.5 by half ulp)': Fraction(1, 2) - Fraction(1, 2**54),
    'subnormal/normal boundary midpoint': Fraction(1, 2**1022) - Fraction(1, 2**1075),
    'zero/min-subnormal midpoint': Fraction(1, 2**1075),
    'min-subnormal/2*min midpoint': Fraction(3, 2**1075),
    '2*min/3*min midpoint': Fraction(5, 2**1075),
    'largest/next subnormal': Fraction(2**52 - 1, 2**1074) + Fraction(1, 2**1075),
    'min normal / next midpoint': Fraction(1, 2**1022) + Fraction(1, 2**1075),
    'overflow bound B = 2^1024 - 2^970': Fraction(2**1024 - 2**970),
}
for name, fr in ties.items():
    s = exact_decimal(fr)
    if '.' not in s:
        s += '.0'
    add_parse(s)
    # just below and just above the tie (tiny perturbation: append digits)
    add_parse(s + '0' * 5 + '1')
    below = exact_decimal(fr - Fraction(1, 2**1100)) if fr > Fraction(1, 2**1100) else None
    if below is not None:
        add_parse(below)
# B written with the last digit reduced by one (still below B)
bs = exact_decimal(Fraction(2**1024 - 2**970))
assert len(bs) == 309, len(bs)
add_parse(bs[:-1] + str(int(bs[-1]) - 1) + '.0')
add_parse(bs + '.0')
add_parse('-' + bs + '.0')
add_parse('0.' + '0' * 400 + '1')
add_parse('-0.' + '0' * 400 + '1')

# very long inputs (1000-digit mantissa and exponent, leading zeros, ...)
digits1000 = ('1234567890' * 100)
add_parse('0.' + digits1000)
add_parse(digits1000)  # integer part of 1000 digits -> overflow
add_parse('1.' + digits1000 + 'e-5')
add_parse('1.' + '0' * 998 + '1')
add_parse('1' + '0' * 999)
add_parse('0.' + '0' * 999 + '1')
add_parse('1e' + '9' * 1000)
add_parse('1e-' + '9' * 1000)
add_parse('0e' + '9' * 1000)
add_parse('1e' + '0' * 999 + '1')
add_parse('1e-' + '0' * 999 + '1')
add_parse('5e-324' if False else '1e' + '0' * 990 + '308')
add_parse('1.' + '0' * 1000 + '5e1000' if False else '1.5e' + '0' * 990 + '2')

# explicit length-boundary inputs around the 512-byte stack buffer
for total in (511, 512, 513, 600, 1024):
    body = '1.' + '0' * (total - 5) + '25'
    assert len(body) == total - 1
    add_parse(body + '3')  # exactly `total` bytes
assert all(len(d) >= 0 for d, _ in parse)
assert len(parse) >= 150, len(parse)

# Extra rendered strings must also be inside the parser grammar (round trip)
for b, s in render:
    if s in ('NaN', 'Infinity', '-Infinity'):
        continue
    assert GRAMMAR.fullmatch(s.encode()), s

# ------------------------------------------------------------------ output
out = []
out.append('/* GENERATED by gen_vectors.py from Python 3 repr()/float(); do not edit. */')
out.append('/* Expected values are independent of the C runtime under test. */')
out.append('typedef struct { uint64_t bits; const char* expect; } NQ_RenderVector;')
out.append('static const NQ_RenderVector nq_render_vectors[] = {')
for b, s in render:
    out.append('    { UINT64_C(0x%016X), %s },' % (b, c_string(s.encode())))
out.append('};')
out.append('typedef struct { const char* data; size_t len; int ok; uint64_t bits; } NQ_ParseVector;')
out.append('static const NQ_ParseVector nq_parse_vectors[] = {')
for data, bits in parse:
    if bits is None:
        out.append('    { %s, %d, 0, 0 },' % (c_string(data), len(data)))
    else:
        out.append('    { %s, %d, 1, UINT64_C(0x%016X) },' % (c_string(data), len(data), bits))
out.append('};')
out.append('')
sys.stdout.write('\n'.join(out))
sys.stderr.write('render vectors: %d, parse vectors: %d, asymmetric pow2: %d\n' % (len(render), len(parse), len(asym)))
