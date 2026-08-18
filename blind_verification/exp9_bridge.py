"""Experiment 9: same-deformation bridge + controls.

Weil side: lam(n) -> lam(n)(1 + eps n^{-delta}) in Q_arith only; lowest eigenvalue(s).
Dilation side: root of eta(s) + eps*eta(s+delta) (recomputed here on the same eps grid).
Controls: uniform deformation, arch-only, pole-only, delta in {0.1,0.2,0.5}, c=20,
N=12, dps 25 vs 40, random coefficient directions, synthetic near-singular PSD matrix.
"""
import csv, math, random
import mpmath as mp
import numpy as np
from weil_form import WeilForm, eigvals_sym

mp.mp.dps = 40
EPS_GRID = ["-0.5", "-0.2", "-0.1", "-0.05", "-0.01", "0", "0.01", "0.05", "0.1", "0.2", "0.5"]

def lam_deformed(W, eps, delta):
    return {n: W.lam[n] * (1 + eps * mp.power(n, -delta)) for n in W.lam}

def low_spectrum(W, Qfixed, lam=None, arch_scale=1, pole_scale=1):
    N = W.N
    Qa = mp.matrix(N, N)
    for j in range(N):
        for k in range(j + 1):
            Qa[j, k] = Qa[k, j] = -W.arith_term(j, k, lam)
    Q = Qfixed[0] * pole_scale + Qfixed[1] * arch_scale + Qa
    return eigvals_sym(Q)

def build_fixed(W):
    N = W.N
    Qp = mp.matrix(N, N); Qi = mp.matrix(N, N)
    for j in range(N):
        for k in range(j + 1):
            Qp[j, k] = Qp[k, j] = W.pole_term(j, k)
            Qi[j, k] = Qi[k, j] = W.arch_term(j, k)
    return (Qp, Qi)

print("building W(c=13,N=8,dps=40) ...")
W8 = WeilForm(N=8, c=13, dps=40)
F8 = build_fixed(W8)

# ---------- main bridge table ----------
delta = mp.mpf("0.2")
def dark_mode(eps, dl):
    eta = mp.altzeta
    rho1 = mp.mpc(mp.mpf("0.5"), mp.mpf("14.134725141734693790457251983562"))
    return mp.findroot(lambda z: eta(z) + eps * eta(z + dl), rho1, solver="muller")

rows = []
print("eps, lambda_min, lambda_2, Re s(dark), Im s(dark)")
for e in EPS_GRID:
    eps = mp.mpf(e)
    ev = low_spectrum(W8, F8, lam_deformed(W8, eps, delta))
    if abs(eps) <= mp.mpf("0.2"):
        s = dark_mode(eps, delta)
        res, ims = mp.re(s), mp.im(s)
    else:
        res, ims = mp.nan, mp.nan
    rows.append([e, mp.nstr(ev[0], 12), mp.nstr(ev[1], 12), mp.nstr(res, 15), mp.nstr(ims, 15)])
    print("  ", rows[-1])
with open("out/bv_exp9_bridge.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["eps", "lambda_min", "lambda_2", "Re_dark", "Im_dark"])
    w.writerows(rows)

# slopes at eps=0 (finite difference with +-0.01)
ev_p = low_spectrum(W8, F8, lam_deformed(W8, mp.mpf("0.01"), delta))
ev_m = low_spectrum(W8, F8, lam_deformed(W8, mp.mpf("-0.01"), delta))
slope_weil = (ev_p[0] - ev_m[0]) / mp.mpf("0.02")
eta = mp.altzeta
rho1 = mp.findroot(lambda z: eta(z), mp.mpc("0.5", "14.1347"), solver="muller")
def dark_slope(dl):
    return -mp.re(eta(rho1 + dl) / mp.diff(eta, rho1))
print("\nslopes at eps=0 (delta=0.2): dlam_min/deps =", mp.nstr(slope_weil, 8),
      " dRe(s)/deps =", mp.nstr(dark_slope(delta), 8))
for dl in [mp.mpf("0.1"), mp.mpf("0.5")]:
    ev_p2 = low_spectrum(W8, F8, lam_deformed(W8, mp.mpf("0.01"), dl))
    ev_m2 = low_spectrum(W8, F8, lam_deformed(W8, mp.mpf("-0.01"), dl))
    sw = (ev_p2[0] - ev_m2[0]) / mp.mpf("0.02")
    print("delta=%s: dlam_min/deps = %s   dRe(s)/deps = %s   ratio = %s" %
          (dl, mp.nstr(sw, 8), mp.nstr(dark_slope(dl), 8), mp.nstr(sw / dark_slope(dl), 6)))

# ---------- controls ----------
print("\n=== controls (all at eps = +-0.05 unless noted) ===")
e05, em05 = mp.mpf("0.05"), mp.mpf("-0.05")
base = low_spectrum(W8, F8)
print("baseline lam_min:", mp.nstr(base[0], 10))

# uniform deformation
for eps in [em05, e05]:
    lam_u = {n: W8.lam[n] * (1 + eps) for n in W8.lam}
    ev = low_spectrum(W8, F8, lam_u)
    print("uniform (1+eps), eps=%s: lam_min = %s" % (mp.nstr(eps, 3), mp.nstr(ev[0], 10)))
# arch-only and pole-only
for eps in [em05, e05]:
    ev = low_spectrum(W8, F8, None, arch_scale=1 + eps)
    print("arch*(1+eps), eps=%s: lam_min = %s" % (mp.nstr(eps, 3), mp.nstr(ev[0], 10)))
for eps in [em05, e05]:
    ev = low_spectrum(W8, F8, None, pole_scale=1 + eps)
    print("pole*(1+eps), eps=%s: lam_min = %s" % (mp.nstr(eps, 3), mp.nstr(ev[0], 10)))

# random directions in coefficient space, |r_n| <= Lambda(n) n^{-delta} scale
rng = random.Random(7)
for trial in range(4):
    lam_r = {}
    for n in W8.lam:
        r = rng.uniform(-1, 1)
        lam_r[n] = W8.lam[n] * (1 + e05 * r * mp.power(n, -delta))
    ev = low_spectrum(W8, F8, lam_r)
    print("random direction trial %d (|eps|=0.05 scale): lam_min = %s" % (trial, mp.nstr(ev[0], 10)))

# precision control: dps 25 rebuild
print("\nprecision control:")
mp.mp.dps = 25
W8lo = WeilForm(N=8, c=13, dps=25)
F8lo = build_fixed(W8lo)
ev_lo = low_spectrum(W8lo, F8lo)
print("dps=25 lam_min:", mp.nstr(ev_lo[0], 10), " (dps=40 gave %s)" % mp.nstr(base[0], 10))
mp.mp.dps = 40

# larger cell c=20 and larger basis N=12
print("\ntruncation controls:")
W8c20 = WeilForm(N=8, c=20, dps=40)
Fc20 = build_fixed(W8c20)
b20 = low_spectrum(W8c20, Fc20)
evp = low_spectrum(W8c20, Fc20, lam_deformed(W8c20, e05, delta))
evm = low_spectrum(W8c20, Fc20, lam_deformed(W8c20, em05, delta))
print("c=20,N=8: lam_min(0)=%s lam_min(+.05)=%s lam_min(-.05)=%s slope~%s" %
      (mp.nstr(b20[0], 8), mp.nstr(evp[0], 8), mp.nstr(evm[0], 8), mp.nstr((evp[0]-evm[0])/mp.mpf('0.1'), 6)))

W12 = WeilForm(N=12, c=13, dps=40)
F12 = build_fixed(W12)
b12 = low_spectrum(W12, F12)
evp = low_spectrum(W12, F12, lam_deformed(W12, e05, delta))
evm = low_spectrum(W12, F12, lam_deformed(W12, em05, delta))
print("c=13,N=12: lam_min(0)=%s lam_min(+.05)=%s lam_min(-.05)=%s slope~%s" %
      (mp.nstr(b12[0], 8), mp.nstr(evp[0], 8), mp.nstr(evm[0], 8), mp.nstr((evp[0]-evm[0])/mp.mpf('0.1'), 6)))
print("c=13,N=12 full low spectrum:", [mp.nstr(x, 6) for x in b12[:6]])

# ---------- synthetic near-singular PSD control ----------
print("\nsynthetic control:")
# deformation-direction matrix on the real problem, for norm calibration
Dq = mp.matrix(8, 8)
lamd = lam_deformed(W8, mp.mpf(1), delta)
for j in range(8):
    for k in range(j + 1):
        v = -(W8.arith_term(j, k, lamd) - W8.arith_term(j, k))
        Dq[j, k] = Dq[k, j] = v  # dQ/deps
frob = lambda M: mp.sqrt(mp.fsum(M[i, jj] ** 2 for i in range(8) for jj in range(8)))
nD = frob(Dq)
print("||dQ/deps||_F (real deformation direction):", mp.nstr(nD, 8))
# Rayleigh prediction: dlam_min/deps = v0^T Dq v0
Qfull = F8[0] + F8[1] + mp.matrix([[-W8.arith_term(j, k) for k in range(8)] for j in range(8)])
Evals, EV = mp.eigsy(Qfull)
i0 = min(range(8), key=lambda i: Evals[i])
v0 = mp.matrix([EV[i, i0] for i in range(8)])
ray = mp.fsum(v0[i] * Dq[i, j] * v0[j] for i in range(8) for j in range(8))
print("Rayleigh prediction v0^T (dQ/deps) v0 =", mp.nstr(ray, 8), " vs measured slope", mp.nstr(slope_weil, 8))

np.random.seed(3)
base_ev = [float(x) for x in eigvals_sym(Qfull)]
A = np.random.randn(8, 8); Qrot, _ = np.linalg.qr(A)
G0 = Qrot @ np.diag(base_ev) @ Qrot.T
S = np.random.randn(8, 8); S = (S + S.T) / 2
S *= float(nD) / np.linalg.norm(S, 'fro')
print("synthetic PSD with same spectrum, random symmetric perturbation of equal norm:")
for e in ["-0.05", "-0.01", "0.01", "0.05"]:
    eps = float(e)
    evs = np.linalg.eigvalsh(G0 + eps * S)
    print("   eps=%s: lam_min = %.6e" % (e, evs[0]))
slope_syn = (np.linalg.eigvalsh(G0 + 0.01 * S)[0] - np.linalg.eigvalsh(G0 - 0.01 * S)[0]) / 0.02
print("synthetic slope ~", "%.4e" % slope_syn, " vs real Weil slope", mp.nstr(slope_weil, 6))
print("done exp9")
