"""Experiment 5: finite additive/Fourier dilation model.

X = Z/MZ, M = 3*5*7*11*13*17 = 255255 (squarefree, 2 invertible), T(x) = 2x mod M.
Direct fixed-point counts, CRT local factorization, Fourier-character trace,
primitive cycle decomposition + Lefschetz relation, Moebius inversion of log Fix.
"""
import csv, math

M = 3 * 5 * 7 * 11 * 13 * 17
assert M == 255255
NMAX = 60

def mobius(n):
    f, i, cnt = n, 2, 0
    res = 1
    while i * i <= f:
        if f % i == 0:
            f //= i; cnt += 1
            if f % i == 0: return 0
            res = -res
        i += 1
    if f > 1: res = -res
    return res

# ---------- direct fixed-point counts ----------
def fix_direct(n):
    t = pow(2, n, M)
    return sum(1 for x in range(M) if (t * x - x) % M == 0)

def fix_gcd(n):
    return math.gcd(pow(2, n) - 1, M)

direct_ns = [1, 2, 3, 4, 5, 6, 8, 10, 12, 24]
print("n, direct count, gcd(2^n-1,M):")
for n in direct_ns:
    fd, fg = fix_direct(n), fix_gcd(n)
    print("  ", n, fd, fg, fd == fg)

# ---------- CRT local factorization ----------
primes_M = [3, 5, 7, 11, 13, 17]
def ordmod(a, q):
    o = 1; t = a % q
    while t != 1:
        t = (t * a) % q; o += 1
    return o
orders = {q: ordmod(2, q) for q in primes_M}
print("multiplicative orders ord_q(2):", orders)
crt_ok = all(
    fix_gcd(n) == math.prod(q if n % orders[q] == 0 else 1 for q in primes_M)
    for n in range(1, NMAX + 1))
print("CRT local factorization Fix(T^n) = prod_q q^[ord_q(2)|n]:", crt_ok)

# ---------- Fourier character trace ----------
# characters chi_a(x) = e^{2 pi i a x / M}; U f = f o T => U chi_a = chi_{2a}.
# U permutes characters; Tr U^n = #{a : 2^n a = a mod M} -- same equation as fixed points.
trace_ok = all(
    sum(1 for a in range(M) if (pow(2, n, M) * a - a) % M == 0) == fix_gcd(n)
    for n in [1, 2, 3, 4, 6, 12])
print("Tr(U^n) (fixed characters) == Fix(T^n):", trace_ok)

# ---------- cycle decomposition ----------
seen = bytearray(M)
cycles = {}  # length -> count
for x in range(M):
    if not seen[x]:
        l = 0; y = x
        while not seen[y]:
            seen[y] = 1
            y = (2 * y) % M
            l += 1
        cycles[l] = cycles.get(l, 0) + 1
print("primitive cycle lengths -> counts:", dict(sorted(cycles.items())))

# Lefschetz/dynamical relation: Fix(T^n) = sum_{d | n} d * c_d
lef_ok = all(
    fix_gcd(n) == sum(d * c for d, c in cycles.items() if n % d == 0)
    for n in range(1, NMAX + 1))
print("Lefschetz relation Fix(T^n) = sum_{d|n} d c_d for n=1..%d:" % NMAX, lef_ok)

# ---------- Moebius inversion of log Fix ----------
# lam(n) := sum_{d|n} mu(n/d) log Fix(T^d); prediction: log q exactly at n = ord_q(2)
rows = []
print("connected trace lam(n) = sum_{d|n} mu(n/d) log Fix(T^d):")
for n in range(1, NMAX + 1):
    lam = sum(mobius(n // d) * math.log(fix_gcd(d)) for d in range(1, n + 1) if n % d == 0)
    if abs(lam) > 1e-9:
        # identify as sum of log q over q with ord_q(2) = n
        qs = [q for q in primes_M if orders[q] == n]
        pred = sum(math.log(q) for q in qs)
        rows.append([n, lam, "*".join(map(str, qs)) or "-", abs(lam - pred)])
        print("   n=%2d lam=%.6f  primes with ord=n: %s  |err|=%.1e" % (n, lam, qs, abs(lam - pred)))
with open("out/bv_exp5_connected_trace.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["n", "lambda_n", "local_primes_ord_n", "abs_err_vs_log_prod"])
    w.writerows(rows)

with open("out/bv_exp5_summary.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["item", "result"])
    w.writerow(["M", M])
    w.writerow(["fix_formula", "Fix(T^n) = gcd(2^n - 1, M), verified directly"])
    w.writerow(["orders", str(orders)])
    w.writerow(["crt_factorization", crt_ok])
    w.writerow(["fourier_trace_equals_fix", trace_ok])
    w.writerow(["cycle_counts", str(dict(sorted(cycles.items())))])
    w.writerow(["lefschetz", lef_ok])
    w.writerow(["moebius_local_separation", "lam(n) = sum_{ord_q(2)=n} log q exactly"])
print("done exp5")
