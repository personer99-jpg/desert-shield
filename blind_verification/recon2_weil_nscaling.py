"""Reconciliation step 2: is ChatGPT's e-23 spectrum my Weil form at deeper truncation?

Rebuilds the geometric-side Weil form (identical functional to exp8, validated there
against the zero-side sum) with pure-mpmath polynomial machinery at dps 60 and a
series-expanded archimedean integrand near u=0 (the exp8 constant-branch shortcut is
fine at 1e-16 but not at 1e-23 accuracy). Runs N = 16, 24, 28, 32 on [0, log 13],
shifted-Legendre basis; prints the 8 lowest eigenvalues for comparison against
ChatGPT's ladder, plus deformed lambda_min at the bridge epsilons.
"""
import sys, csv, time
from math import comb
import mpmath as mp

mp.mp.dps = 60
Lc = mp.log(13)

# ---------- polynomial helpers (coeff arrays, low -> high) ----------
def polymul(a, b):
    r = [mp.mpf(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                r[i + j] += x * y
    return r

def evalp(c, u):
    tot = mp.mpf(0)
    p = mp.mpf(1)
    for x in c:
        tot += x * p
        p *= u
    return tot

def shifted_legendre(N, L):
    x = [mp.mpf(-1), 2 / L]
    P = [[mp.mpf(1)]]
    if N > 1:
        P.append(x[:])
    for j in range(1, N - 1):
        xP = polymul(x, P[j])
        new = [(2 * j + 1) * c for c in xP]
        for i, c in enumerate(P[j - 1]):
            new[i] -= j * c
        P.append([c / (j + 1) for c in new])
    return P

def precompute_M(dmax, L):
    """M[(a,b)](u) = int_0^{L-u} (v+u)^a v^b dv as coeff array in u."""
    M = {}
    for a in range(dmax + 1):
        for b in range(dmax + 1):
            arr = [mp.mpf(0)] * (a + b + 2)
            for i in range(a + 1):
                m = a - i + b + 1
                c0 = mp.mpf(comb(a, i)) / m
                Lp = [c0 * comb(m, t) * (L ** (m - t)) * ((-1) ** t) for t in range(m + 1)]
                for t, v in enumerate(Lp):
                    arr[i + t] += v
            M[(a, b)] = arr
    return M

def autocorr(cj, ck, M):
    deg = len(cj) + len(ck)
    g = [mp.mpf(0)] * deg
    for a, xa in enumerate(cj):
        if xa == 0: continue
        for b, xb in enumerate(ck):
            if xb == 0: continue
            arr = M[(a, b)]
            f = xa * xb
            for t, v in enumerate(arr):
                g[t] += f * v
    return g

# ---------- explicit-formula terms on an even piece G (poly on [0,L]) ----------
LAM = {}
for n in range(2, 13):
    m, p = n, None
    f = 2
    while f * f <= m:
        if m % f == 0:
            p = f; break
        f += 1
    if p is None: p = n
    q = n
    while q % p == 0: q //= p
    LAM[n] = mp.log(p) if q == 1 else mp.mpf(0)
NS = [n for n in LAM if LAM[n] != 0]

def pole_term(G):
    return 2 * mp.quad(lambda u: evalp(G, u) * 2 * mp.cosh(u / 2), [0, Lc])

def arith_term(G, lam=None):
    lam = lam or LAM
    return 2 * mp.fsum(lam[n] / mp.sqrt(n) * evalp(G, mp.log(n)) for n in NS)

U0 = mp.mpf("0.15")
KSER = 70

def arch_term(G):
    g0 = G[0]
    # series of numerator N(u) = 2 g0 e^{-2u} - 2 G(u) e^{-u/2} and D(u) = 1 - e^{-2u}
    K = KSER
    e2 = [mp.mpf(0)] * (K + 2)  # e^{-2u}
    eh = [mp.mpf(0)] * (K + 2)  # e^{-u/2}
    fact = mp.mpf(1)
    for k in range(K + 2):
        if k > 0: fact *= k
        e2[k] = (mp.mpf(-2)) ** k / fact
        eh[k] = (mp.mpf(-1) / 2) ** k / fact
    Gser = [G[i] if i < len(G) else mp.mpf(0) for i in range(K + 2)]
    Geh = [mp.mpf(0)] * (K + 2)
    for i in range(K + 2):
        s = mp.mpf(0)
        for j in range(i + 1):
            s += Gser[j] * eh[i - j]
        Geh[i] = s
    Nser = [2 * g0 * e2[k] - 2 * Geh[k] for k in range(K + 2)]
    Dser = [-e2[k] for k in range(K + 2)]
    Dser[0] += 1
    # both vanish at u=0: divide by u
    Nq = Nser[1:]
    Dq = Dser[1:]
    # power-series division R = Nq / Dq
    R = [mp.mpf(0)] * (K + 1)
    for k in range(K + 1):
        s = Nq[k]
        for j in range(1, k + 1):
            if j < len(Dq):
                s -= Dq[j] * R[k - j]
        R[k] = s / Dq[0]
    # integral over [0, U0] from series, exactly
    I0 = mp.fsum(R[k] * U0 ** (k + 1) / (k + 1) for k in range(K + 1))
    # direct integral over [U0, L]
    def integrand(u):
        return (2 * g0 * mp.e ** (-2 * u) - 2 * evalp(G, u) * mp.e ** (-u / 2)) / (1 - mp.e ** (-2 * u))
    I1 = mp.quad(integrand, [U0, Lc])
    tail = -g0 * mp.log(1 - mp.e ** (-2 * Lc))
    return -(mp.euler + mp.log(mp.pi)) * g0 + I0 + I1 + tail

def build(N, eps_list):
    t0 = time.time()
    basis = shifted_legendre(N, Lc)
    dmax = N - 1
    M = precompute_M(dmax, Lc)
    G = [[None] * N for _ in range(N)]
    for j in range(N):
        for k in range(j + 1):
            gjk = autocorr(basis[j], basis[k], M)
            gkj = autocorr(basis[k], basis[j], M)
            G[j][k] = G[k][j] = [(x + y) / 2 for x, y in zip(gjk, gkj)]
    print("N=%d: autocorrelations done (%.0fs)" % (N, time.time() - t0)); sys.stdout.flush()
    Qfix = mp.matrix(N, N)   # pole + arch
    Aρ = {}                  # per-n arithmetic point-eval matrices for fast deformation
    for n in NS:
        Aρ[n] = mp.matrix(N, N)
    for j in range(N):
        for k in range(j + 1):
            v = pole_term(G[j][k]) + arch_term(G[j][k])
            Qfix[j, k] = Qfix[k, j] = v
            for n in NS:
                w = 2 * evalp(G[j][k], mp.log(n)) / mp.sqrt(n)
                Aρ[n][j, k] = Aρ[n][k, j] = w
    print("N=%d: pole/arch/arith matrices done (%.0fs)" % (N, time.time() - t0)); sys.stdout.flush()

    def spectrum(eps, delta=mp.mpf("0.2")):
        Q = Qfix.copy()
        for n in NS:
            f = LAM[n] * (1 + eps * mp.power(n, -delta))
            for j in range(N):
                for k in range(N):
                    Q[j, k] -= f * Aρ[n][j, k]
        E = mp.eigsy(Q, eigvals_only=True)
        return sorted([E[i] for i in range(N)])

    ev0 = spectrum(mp.mpf(0))
    print("N=%d lowest 8 eigenvalues:" % N)
    for e in ev0[:8]:
        print("   ", mp.nstr(e, 8))
    print("N=%d largest:" % N, mp.nstr(ev0[-1], 8))
    out = {"ev0": ev0}
    for e in eps_list:
        ev = spectrum(mp.mpf(e))
        out[e] = ev[0]
        print("N=%d eps=%8s: lam_min = %s" % (N, e, mp.nstr(ev[0], 8))); sys.stdout.flush()
    return out

if __name__ == "__main__":
    results = {}
    for N in [16, 24, 28, 32]:
        results[N] = build(N, ["-0.05", "-0.01", "-0.0001", "0.0001", "0.01", "0.05"])
        print()

    with open("out/bv_recon_nscaling.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["N", "rank", "eigenvalue"])
        for N, r in results.items():
            for i, e in enumerate(r["ev0"][:8]):
                w.writerow([N, i + 1, mp.nstr(e, 20)])
    print("done recon2")
