"""Experiments 6 & 7: global dilation sum, blind dark-mode scan, deformation control.

Exp 6:
 - Verify Mellin action of Zf(x) = sum_n f(nx): multiplier zeta(s).
 - Blind scan of |eta(1/2 + iE)| on E in (0.5, 60): locate minima with NO reference
   to known zeta zeros; refine; only afterwards compare with independently computed
   zeros (mpmath.zetazero).
Exp 7:
 - Deform a_n(eps) = (-1)^{n-1}(1 + eps n^{-delta}) => F_eps(s) = eta(s) + eps*eta(s+delta).
 - Track the root evolving from the first dark mode, solving both Re s and Im s.
 - First-order sensitivity, both signs of eps, precision and truncation-depth checks.
"""
import csv
import mpmath as mp

mp.mp.dps = 30

# ---------- Exp 6: Mellin multiplier ----------
# test f(x) = exp(-x): Zf(x) = 1/(e^x - 1). Mellin(Zf)(s) should equal zeta(s)*Mellin(f)(s) = zeta(s)*Gamma(s)
for s in [mp.mpf(2), mp.mpf(3), mp.mpc(2, 1)]:
    mel = mp.quad(lambda x: (1 / (mp.e**x - 1)) * x**(s - 1), [0, mp.inf])
    ref = mp.zeta(s) * mp.gamma(s)
    print("Mellin check s =", s, "|Zf_mellin - zeta*Gamma| =", mp.nstr(abs(mel - ref), 5))

# ---------- Exp 6: blind dark-mode scan ----------
def eta(s):
    return mp.altzeta(s)

def eta_trunc(s, N):
    # truncated alternating sum with half-terminal correction (regularization depth N)
    tot = mp.mpf(0)
    sgn = 1
    for n in range(1, N + 1):
        tot += sgn * mp.power(n, -s)
        sgn = -sgn
    tot += sgn * mp.power(N + 1, -s) / 2
    return tot

# scan |eta(1/2+iE)| on a grid; record local minima; refine by minimizing |eta|^2
Es = [mp.mpf("0.5") + i * mp.mpf("0.01") for i in range(int((60 - 0.5) / 0.01) + 1)]
vals = [abs(eta(mp.mpc(0.5, E))) for E in Es]
minima = []
for i in range(1, len(vals) - 1):
    if vals[i] < vals[i - 1] and vals[i] < vals[i + 1]:
        # refine with ternary search
        a, b = Es[i - 1], Es[i + 1]
        f = lambda E: abs(eta(mp.mpc(0.5, E)))
        for _ in range(80):
            m1 = a + (b - a) / 3; m2 = b - (b - a) / 3
            if f(m1) < f(m2): b = m2
            else: a = m1
        E0 = (a + b) / 2
        depth = f(E0)
        minima.append((E0, depth))

dark = [(E, d) for E, d in minima if d < 1e-6]   # true zeros vs shallow dips
print("\nblind dark modes on critical line (|eta| < 1e-6):")
for E, d in dark:
    print("   E = %s  |eta| = %s" % (mp.nstr(E, 12), mp.nstr(d, 3)))
shallow = [(mp.nstr(E, 8), mp.nstr(d, 3)) for E, d in minima if d >= 1e-6]
print("shallow (non-zero) minima:", shallow)

# only NOW source zeros independently
ref_zeros = []
k = 1
while True:
    z = mp.zetazero(k)
    if mp.im(z) > 60: break
    ref_zeros.append(mp.im(z))
    k += 1
print("\ncomparison with independently sourced zeta zeros:")
rows = []
for (E, d), g in zip(dark, ref_zeros):
    rows.append([mp.nstr(E, 15), mp.nstr(g, 15), mp.nstr(abs(E - g), 3)])
    print("   found %s  vs zetazero %s   diff %s" % (mp.nstr(E, 10), mp.nstr(g, 10), mp.nstr(abs(E - g), 3)))
print("counts match in (0,60):", len(dark) == len(ref_zeros))
with open("out/bv_exp6_dark_modes.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["blind_E", "independent_zeta_zero", "abs_diff"])
    w.writerows(rows)

# note: eta = (1 - 2^{1-s}) zeta; the extra factor vanishes only on Re s = 1,
# so on the critical line eta-zeros are exactly zeta-zeros. State this in report.

# ---------- Exp 7: deformation ----------
delta = mp.mpf("0.2")
def F(s, eps, dl=delta):
    return eta(s) + eps * eta(s + dl)

def dF(s, eps, dl=delta):
    h = mp.mpf(10) ** (-10)
    return (F(s + h, eps, dl) - F(s - h, eps, dl)) / (2 * h)

rho1 = mp.mpc(mp.mpf("0.5"), dark[0][0])   # first blind dark mode as seed
print("\nExp 7: root tracking of F_eps(s) = eta(s) + eps eta(s+delta), delta =", delta)

def track(eps_list, dl, seed):
    out = []
    s = seed
    for eps in eps_list:
        s = mp.findroot(lambda z: F(z, eps, dl), s, solver="muller")
        out.append((eps, s))
    return out

eps_pos = [mp.mpf(e) for e in ["0.001", "0.005", "0.01", "0.05", "0.1", "0.2"]]
eps_neg = [-e for e in eps_pos]
res_pos = track(eps_pos, delta, rho1)
res_neg = track(eps_neg, delta, rho1)

rows = []
for eps, s in sorted(res_neg + [(mp.mpf(0), rho1)] + res_pos, key=lambda t: t[0]):
    rows.append([mp.nstr(eps, 6), mp.nstr(mp.re(s), 15), mp.nstr(mp.im(s), 15),
                 mp.nstr(mp.re(s) - mp.mpf("0.5"), 6)])
    print("   eps=%8s  Re s = %s  Im s = %s  (Re s - 1/2 = %s)" %
          (mp.nstr(eps, 4), mp.nstr(mp.re(s), 12), mp.nstr(mp.im(s), 12), mp.nstr(mp.re(s) - mp.mpf('0.5'), 4)))
with open("out/bv_exp7_deformed_root.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["eps", "Re_s", "Im_s", "Re_s_minus_half"])
    w.writerows(rows)

# analytic first-order sensitivity ds/deps = -eta(rho+delta)/eta'(rho)
etap = mp.diff(eta, rho1)
sens = -eta(rho1 + delta) / etap
print("\nfirst-order ds/deps = -eta(rho+delta)/eta'(rho) =", mp.nstr(sens, 10))
print("   d(Re s)/deps =", mp.nstr(mp.re(sens), 8), " d(Im s)/deps =", mp.nstr(mp.im(sens), 8))
# finite-difference check
fd = (res_pos[0][1] - res_neg[0][1]) / (2 * eps_pos[0])
print("   finite-diff  ds/deps  =", mp.nstr(fd, 8))

# controls: delta = 0.5; higher precision; truncated eta (depth check)
res_d5 = track([mp.mpf("0.05")], mp.mpf("0.5"), rho1)
print("\ncontrol delta=0.5, eps=0.05: s =", mp.nstr(res_d5[0][1], 15))

mp.mp.dps = 50
s_hp = mp.findroot(lambda z: F(z, mp.mpf("0.05")), rho1, solver="muller")
print("control dps=50, eps=0.05, delta=0.2: s =", mp.nstr(s_hp, 20))
mp.mp.dps = 30

def F_trunc(s, eps, N):
    return eta_trunc(s, N) + eps * eta_trunc(s + delta, N)
for N in [2000, 20000]:
    s_tr = mp.findroot(lambda z: F_trunc(z, mp.mpf("0.05"), N), rho1, solver="muller")
    print("control truncated eta, depth N=%d: s = %s" % (N, mp.nstr(s_tr, 15)))
print("done exp6/7")
