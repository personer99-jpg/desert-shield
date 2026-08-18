"""Experiment 3: literal prime-loop spectra and Kirchhoff coupling.

Part 1: independent loops, circumference L_p = log p, modes E_k = 2 pi k / L_p (k>=1).
Count modes with E <= threshold as prime cutoff P grows. Question: finite low-energy limit?

Part 2: Kirchhoff star graph with 3 bonds of lengths log 2, log 3, log 5
(Neumann outer ends, Kirchhoff central vertex). Compute ~10^4 eigenvalues from the
secular equation, Fourier-transform the fluctuating spectral density, and look for
orbit-length peaks. Question: do mixed lengths log p + log q (i.e. log pq) appear,
which have Lambda(pq)=0 in the arithmetic trace?
"""
import csv, math
import numpy as np

# primes by sieve
N = 2_000_000
is_comp = bytearray(N + 1)
primes = []
for i in range(2, N + 1):
    if not is_comp[i]:
        primes.append(i)
        for j in range(i * i, N + 1, i):
            is_comp[j] = 1

# ---------- Part 1: mode counts ----------
thresholds = [5.0, 10.0, 14.0]
cutoffs = [10, 100, 1000, 10_000, 100_000, 1_000_000, 2_000_000]
rows = []
for P in cutoffs:
    counts = {}
    for E in thresholds:
        c = 0
        for p in primes:
            if p > P: break
            c += int(E * math.log(p) / (2 * math.pi))
        counts[E] = c
    rows.append([P] + [counts[E] for E in thresholds])
print("P_cutoff, N(E<=5), N(E<=10), N(E<=14):")
for r in rows: print("  ", r)
with open("out/bv_exp3_low_energy_counts.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["prime_cutoff", "modes_E_le_5", "modes_E_le_10", "modes_E_le_14"])
    w.writerows(rows)
# theoretical growth: sum_p floor(E log p / 2pi) ~ (E/2pi) * theta(P) ~ (E/2pi) P -> diverges

# ---------- Part 2: Kirchhoff star graph ----------
L = [math.log(2), math.log(3), math.log(5)]
# Secular equation for star, Neumann ends + Kirchhoff center: sum_i tan(k L_i) = 0
# (poles at k L_i = pi/2 + m pi). Find roots by dense scan + bisection on
# F(k) = sum_i sin(kL_i) prod_{j!=i} cos(kL_j)   (smooth version, zeros = eigenvalues incl. pole-crossings handled)
def F(k):
    s = 0.0
    c = [math.cos(k * l) for l in L]
    sn = [math.sin(k * l) for l in L]
    for i in range(3):
        term = sn[i]
        for j in range(3):
            if j != i: term *= c[j]
        s += term
    return s

KMAX = 30000.0
dk = 0.002
ks = np.arange(1e-6, KMAX, dk)
c0 = np.cos(np.outer(ks, L)); s0 = np.sin(np.outer(ks, L))
Fv = (s0[:,0]*c0[:,1]*c0[:,2] + c0[:,0]*s0[:,1]*c0[:,2] + c0[:,0]*c0[:,1]*s0[:,2])
sign = np.sign(Fv)
idx = np.where(sign[:-1] * sign[1:] < 0)[0]
roots = []
for i in idx:
    a, b = ks[i], ks[i+1]
    fa = F(a)
    for _ in range(60):
        m = 0.5 * (a + b)
        fm = F(m)
        if fa * fm <= 0: b = m
        else: a, fa = m, fm
    roots.append(0.5 * (a + b))
roots = np.array(roots)
print("Kirchhoff star: found", len(roots), "eigenvalues up to k =", KMAX)

# Weyl law check: mean density = total length / pi
Ltot = sum(L)
expected = Ltot * KMAX / math.pi
print("Weyl expectation:", expected)

# length spectrum: C(l) = |sum_n w(k_n) exp(i l k_n)| with Hann window.
# The smooth (Weyl) part only contributes near l=0; we scan l >= 0.8 where the
# shortest orbit is 2*log 2 = 1.386, so no smooth subtraction is needed.
kmax = roots.max()
w = 0.5 * (1 - np.cos(2 * np.pi * roots / kmax))  # Hann over [0,kmax]
lgrid = np.arange(0.8, 8.0, 0.001)
Cl = np.zeros(len(lgrid))
chunk = 400
for i0 in range(0, len(lgrid), chunk):
    ll = lgrid[i0:i0+chunk][:, None]
    Cl[i0:i0+chunk] = np.abs((w[None, :] * np.exp(1j * ll * roots[None, :])).sum(axis=1))

# peak detection
peaks = []
for i in range(2, len(lgrid) - 2):
    if Cl[i] > Cl[i-1] and Cl[i] > Cl[i+1] and Cl[i] > 0.12 * Cl.max():
        peaks.append((lgrid[i], Cl[i]))
# merge nearby
merged = []
for l, a in peaks:
    if merged and l - merged[-1][0] < 0.02:
        if a > merged[-1][1]: merged[-1] = (l, a)
    else:
        merged.append((l, a))

# candidate orbit lengths: 2*(m1 L1 + m2 L2 + m3 L3), m_i >= 0 not all zero
cands = {}
for m1 in range(0, 6):
    for m2 in range(0, 5):
        for m3 in range(0, 4):
            if m1 + m2 + m3 == 0: continue
            ell = 2 * (m1 * L[0] + m2 * L[1] + m3 * L[2])
            if ell < 8.0:
                n = (2**m1) * (3**m2) * (5**m3)
                cands[round(ell, 6)] = n

print("\nlength-spectrum peaks (l, amplitude) and nearest candidate 2*log(n):")
out_rows = []
for l, a in merged:
    best = min(cands.items(), key=lambda kv: abs(kv[0] - l))
    tag = "n=%d (dist %.4f)" % (best[1], abs(best[0] - l))
    is_mixed = False
    n = best[1]
    # mixed = divisible by at least two distinct primes
    distinct = sum(1 for p in [2, 3, 5] if n % p == 0)
    is_mixed = distinct >= 2
    out_rows.append([round(l, 4), round(a, 2), best[1], round(best[0], 4), is_mixed])
    print("  l=%.4f amp=%8.1f -> 2*log(%d)=%.4f mixed=%s" % (l, a, best[1], best[0], is_mixed))

with open("out/bv_exp3_star_graph_orbits.csv", "w", newline="") as f:
    wcsv = csv.writer(f)
    wcsv.writerow(["peak_length", "amplitude", "nearest_n", "2log_n", "mixed_composite"])
    wcsv.writerows(out_rows)

mixed_present = any(r[4] for r in out_rows)
print("\nMixed composite orbits (e.g. 2*log 6) present in quantum-graph length spectrum:", mixed_present)
print("Arithmetic trace (Exp 2) has Lambda=0 at mixed composites -> structural conflict:", mixed_present)
print("done exp3")
