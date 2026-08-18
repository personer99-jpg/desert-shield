"""Experiment 4: finite-field control universe.

E1: y^2 = x^3 + x + 1 over F_5.  Direct point counts over F_{5^n} via explicit
field arithmetic (polynomial representation, irreducible modulus found by search),
Frobenius recurrence prediction, Moebius-inverted primitive closed points, zeta
function two ways, smooth-bulk ablation, and a second curve E2: y^2 = x^3 + 2.
"""
import csv, math
from fractions import Fraction

p = 5

# ---------- polynomial arithmetic over F_p ----------
def pmul(a, b, mod):
    # a,b lists of coeffs (low->high) reduced mod `mod` (monic, list)
    n = len(mod) - 1
    res = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                res[i + j] = (res[i + j] + ai * bj) % p
    # reduce
    for i in range(len(res) - 1, n - 1, -1):
        c = res[i]
        if c:
            res[i] = 0
            for j in range(n):
                res[i - n + j] = (res[i - n + j] - c * mod[j]) % p
    res = res[:n]
    while len(res) < n: res.append(0)
    return res

def padd(a, b):
    return [(x + y) % p for x, y in zip(a, b)]

def ppow(a, e, mod):
    n = len(mod) - 1
    r = [1] + [0] * (n - 1)
    base = a[:]
    while e:
        if e & 1: r = pmul(r, base, mod)
        base = pmul(base, base, mod)
        e >>= 1
    return r

def is_irreducible(mod):
    # x^(p^n) == x mod (mod), and x^(p^(n/l)) != x for prime divisors l of n
    n = len(mod) - 1
    x = [0, 1] + [0] * (n - 2) if n >= 2 else [0]
    def frob_iter(times):
        r = x[:]
        for _ in range(times):
            r = ppow(r, p, mod)
        return r
    if frob_iter(n) != x: return False
    for l in set(factorize(n)):
        if frob_iter(n // l) == x: return False
    return True

def factorize(n):
    f, i = [], 2
    while i * i <= n:
        while n % i == 0: f.append(i); n //= i
        i += 1
    if n > 1: f.append(n)
    return f

def find_irreducible(n):
    # search monic x^n + c_{n-1}x^{n-1}+...+c_0
    import itertools
    for tail in itertools.product(range(p), repeat=n):
        mod = list(tail) + [1]
        if mod[0] == 0: continue
        if is_irreducible(mod):
            return mod
    raise RuntimeError

def count_points(n, A, Bc):
    """#E(F_{p^n}) for y^2 = x^3 + A x + B, projective (includes point at infinity)."""
    if n == 1:
        cnt = 1
        for x in range(p):
            rhs = (x**3 + A * x + Bc) % p
            for y in range(p):
                if (y * y) % p == rhs: cnt += 1
        return cnt
    mod = find_irreducible(n)
    q = p ** n
    # enumerate all field elements as coefficient vectors
    import itertools
    cnt = 1  # infinity
    half = (q - 1) // 2
    Apoly = [A % p] + [0]*(n-1)
    Bpoly = [Bc % p] + [0]*(n-1)
    zero = [0]*n
    for vec in itertools.product(range(p), repeat=n):
        x = list(vec)
        x3 = pmul(pmul(x, x, mod), x, mod)
        rhs = padd(padd(x3, pmul(Apoly, x, mod)), Bpoly)
        if rhs == zero:
            cnt += 1
        else:
            # Euler criterion: rhs^((q-1)/2) == 1 -> two sqrt, == -1 -> none
            e = ppow(rhs, half, mod)
            if e == [1] + [0]*(n-1):
                cnt += 2
    return cnt

def mobius(n):
    fs = factorize(n)
    if len(set(fs)) != len(fs): return 0
    return -1 if len(fs) % 2 else 1

def run_curve(A, Bc, name, nmax_direct=6):
    print(f"=== curve {name}: y^2 = x^3 + {A}x + {Bc} over F_5 ===")
    direct = {}
    for n in range(1, nmax_direct + 1):
        direct[n] = count_points(n, A, Bc)
    print("direct counts:", direct)
    N1 = direct[1]
    a = p + 1 - N1
    print("Frobenius trace a =", a, "| char poly T^2 - (%d)T + %d" % (a, p))
    disc = a * a - 4 * p
    print("a^2 - 4p =", disc, "(Hasse:", abs(a) <= 2 * math.sqrt(p), ")")
    # recurrence: t_n = a t_{n-1} - p t_{n-2}, t_0 = 2, t_1 = a ; N_n = p^n + 1 - t_n
    t = {0: 2, 1: a}
    pred = {}
    for n in range(2, nmax_direct + 1):
        t[n] = a * t[n - 1] - p * t[n - 2]
    for n in range(1, nmax_direct + 1):
        pred[n] = p ** n + 1 - t[n]
    match = all(pred[n] == direct[n] for n in direct)
    print("recurrence prediction matches direct counts:", match, pred)
    # primitive closed points: a_d = (1/d) sum_{e|d} mu(d/e) N_e
    prim = {}
    for d in range(1, nmax_direct + 1):
        s = sum(mobius(d // e) * direct.get(e, pred.get(e)) for e in range(1, d + 1) if d % e == 0)
        assert s % d == 0, (d, s)
        prim[d] = s // d
    print("primitive closed points a_d (orbit length d):", prim)
    # zeta two ways as power series in T up to T^6
    M = nmax_direct
    # way 1: exp(sum N_n T^n / n)
    logZ = [Fraction(0)] * (M + 1)
    for n in range(1, M + 1):
        logZ[n] = Fraction(direct[n], n)
    Z1 = [Fraction(0)] * (M + 1); Z1[0] = Fraction(1)
    # exp of power series
    for k in range(1, M + 1):
        s = Fraction(0)
        for j in range(1, k + 1):
            s += j * logZ[j] * Z1[k - j]
        Z1[k] = s / k
    # way 2: product over primitive points prod (1 - T^d)^{-a_d}  -> log = sum a_d * sum_m T^{dm}/m
    logZ2 = [Fraction(0)] * (M + 1)
    for d, ad in prim.items():
        m = 1
        while d * m <= M:
            logZ2[d * m] += Fraction(ad, m)
            m += 1
    Z2 = [Fraction(0)] * (M + 1); Z2[0] = Fraction(1)
    for k in range(1, M + 1):
        s = Fraction(0)
        for j in range(1, k + 1):
            s += j * logZ2[j] * Z2[k - j]
        Z2[k] = s / k
    # way 3: rational formula (1 - aT + pT^2)/((1-T)(1-pT)) expanded
    num = [1, -a, p]
    den_inv = [Fraction(0)] * (M + 1)
    # 1/((1-T)(1-pT)) = sum ( (p^{k+1}-1)/(p-1) ) T^k
    for k in range(M + 1):
        den_inv[k] = Fraction(p ** (k + 1) - 1, p - 1)
    Z3 = [Fraction(0)] * (M + 1)
    for k in range(M + 1):
        s = Fraction(0)
        for j, c in enumerate(num):
            if k - j >= 0: s += c * den_inv[k - j]
        Z3[k] = s
    print("zeta series agree (exp-counts vs orbit-product vs rational):",
          Z1 == Z2 == Z3)
    # inverse zeros of numerator: alpha, beta with |alpha| = sqrt(5)
    import cmath
    alpha = (a + cmath.sqrt(disc)) / 2
    print("Frobenius eigenvalues:", alpha, "| |alpha| =", abs(alpha), "sqrt(5) =", math.sqrt(5))
    return direct, a, prim, (Z1, Z2, Z3)

d1, a1, prim1, _ = run_curve(1, 1, "E1")
print()
# ablation: replace N_n by smooth bulk p^n + 1
print("=== ablation: N_n -> p^n + 1 (smooth bulk only) ===")
M = 6
prim_bulk = {}
for d in range(1, M + 1):
    s = sum(mobius(d // e) * (p ** e + 1) for e in range(1, d + 1) if d % e == 0)
    prim_bulk[d] = Fraction(s, d)
print("bulk 'primitive counts':", {d: str(v) for d, v in prim_bulk.items()})
print("bulk zeta = 1/((1-T)(1-5T)): numerator degenerates to 1, spectrum (nontrivial zeros) vanishes")

print()
d2, a2, prim2, _ = run_curve(0, 2, "E2")

with open("out/bv_exp4_point_counts.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["n", "E1_direct", "E1_predicted", "E2_direct"])
    t = {0: 2, 1: a1}
    for n in range(2, 7): t[n] = a1 * t[n-1] - p * t[n-2]
    for n in range(1, 7):
        w.writerow([n, d1[n], p**n + 1 - t[n], d2[n]])
with open("out/bv_exp4_primitive_points.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["degree_d", "E1_primitive_closed_points", "E2_primitive_closed_points"])
    for d in range(1, 7):
        w.writerow([d, prim1[d], prim2[d]])
print("done exp4")
