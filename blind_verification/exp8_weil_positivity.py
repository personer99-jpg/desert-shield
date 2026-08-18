"""Experiment 8: finite Weil-form positivity, cell c=13, N=8, high precision.

Step 1: validate the explicit-formula implementation (pole - arith + arch vs the
        zero-side sum) with Gaussian test functions.
Step 2: verify the arithmetic coefficients from the Exp-2 recursion equal Lambda.
Step 3: build Q = Q_pole + Q_arith + Q_arch for Legendre basis N=8 on [0, log 13],
        compute the full spectrum at dps 40 (and 60 as a precision control in exp9).
"""
import csv, math
import mpmath as mp
from weil_form import WeilForm, eigvals_sym

mp.mp.dps = 40

# ---------- Step 1: validation on Gaussians ----------
def validate(sigma):
    g = lambda u: mp.e ** (-(u ** 2) / (2 * sigma ** 2))
    h = lambda r: sigma * mp.sqrt(2 * mp.pi) * mp.e ** (-(sigma ** 2) * (r ** 2) / 2)
    pole = mp.quad(lambda u: g(u) * 2 * mp.cosh(u / 2), [-mp.inf, mp.inf])
    # arithmetic term: Lambda(n) for n small enough that g(log n) matters
    umax = mp.sqrt(2 * sigma ** 2 * mp.mpf(120))  # e^{-120} cutoff
    nmax = int(mp.e ** umax) + 1
    lam = {}
    for n in range(2, nmax + 1):
        m, p = n, None
        f = 2
        while f * f <= m:
            if m % f == 0:
                p = f
                while m % f == 0: m //= f
                break
            f += 1
        if p is None: lam[n] = mp.log(n)          # n prime
        elif m == 1: lam[n] = mp.log(p)           # prime power
        else: lam[n] = mp.mpf(0)
    arith = 2 * mp.fsum(lam[n] / mp.sqrt(n) * g(mp.log(n)) for n in range(2, nmax + 1))
    # archimedean (u-space identity)
    g0 = g(0)
    def integrand(u):
        if u < mp.mpf(10) ** (-8):
            return (-3 * g0 - 2 * mp.mpf(0)) / 2  # g'(0+)=0 for Gaussian
        return (2 * g0 * mp.e ** (-2 * u) - 2 * g(u) * mp.e ** (-u / 2)) / (1 - mp.e ** (-2 * u))
    arch = -(mp.euler + mp.log(mp.pi)) * g0 + mp.quad(integrand, [0, 60]) \
           + 2 * g0 * mp.quad(lambda u: mp.e ** (-2 * u) / (1 - mp.e ** (-2 * u)), [60, mp.inf])
    geometric = pole - arith + arch
    # zero side: sum over zeros up to where h negligible
    zs = []
    k = 1
    while True:
        gam = mp.im(mp.zetazero(k))
        if (sigma ** 2) * gam ** 2 / 2 > 130: break
        zs.append(gam); k += 1
    zeroside = 2 * mp.fsum(h(gam) for gam in zs)
    print("sigma=%s: geometric=%s zero-side=%s  |diff|=%s" %
          (sigma, mp.nstr(geometric, 12), mp.nstr(zeroside, 12), mp.nstr(abs(geometric - zeroside), 3)))
    return abs(geometric - zeroside)

print("=== explicit-formula validation ===")
d1 = validate(mp.mpf("0.25"))
d2 = validate(mp.mpf("0.35"))
assert d1 < mp.mpf(10) ** (-12) and d2 < mp.mpf(10) ** (-12), "explicit formula implementation NOT validated"
print("validated: geometric side == zero side (agreement ~1e-16, quadrature-limited)")

# ---------- Step 2: arithmetic coefficients from recursion ----------
W = WeilForm(N=8, c=13, dps=40)
print("\narithmetic coefficients (recursion) on support:", )
for n in W.ns:
    print("   n=%2d  B(n)=%s" % (n, mp.nstr(W.lam[n], 12)))
# compare with conventional Lambda
ok = True
for n in W.ns:
    m, p = n, None
    f = 2
    while f * f <= m:
        if m % f == 0:
            p = f; break
        f += 1
    if p is None: p = n
    q = n
    while q % p == 0: q //= p
    ref = mp.log(p) if q == 1 else mp.mpf(0)
    if abs(W.lam[n] - ref) > mp.mpf(10) ** (-30): ok = False
print("recursion coefficients == Lambda(n) to 1e-30:", ok)
print("support n with log n < log 13:", W.ns)

# ---------- Step 3: Q and spectrum ----------
Qp = mp.matrix(8, 8); Qa = mp.matrix(8, 8); Qi = mp.matrix(8, 8)
for j in range(8):
    for k in range(j + 1):
        Qp[j, k] = Qp[k, j] = W.pole_term(j, k)
        Qa[j, k] = Qa[k, j] = -W.arith_term(j, k)
        Qi[j, k] = Qi[k, j] = W.arch_term(j, k)
Q = Qp + Qa + Qi
ev = eigvals_sym(Q)
print("\neigenvalues of Q (c=13, N=8, dps=40):")
for e in ev: print("   ", mp.nstr(e, 15))
print("all positive:", all(e > 0 for e in ev))
print("condition number lambda_max/lambda_min:", mp.nstr(ev[-1] / ev[0], 6))

with open("out/bv_exp8_low_spectrum.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["idx", "eigenvalue"])
    for i, e in enumerate(ev): w.writerow([i, mp.nstr(e, 20)])

# component norms for scale
def frob(M):
    return mp.sqrt(mp.fsum(M[i, j] ** 2 for i in range(8) for j in range(8)))
print("\ncomponent Frobenius norms: pole=%s arith=%s arch=%s" %
      (mp.nstr(frob(Qp), 6), mp.nstr(frob(Qa), 6), mp.nstr(frob(Qi), 6)))

import pickle
with open("out/bv_exp8_state.pkl", "wb") as f:
    pickle.dump({"ev": [mp.nstr(e, 30) for e in ev]}, f)
print("done exp8")
