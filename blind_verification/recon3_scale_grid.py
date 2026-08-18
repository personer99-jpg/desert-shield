"""Reconciliation step 3: compare ChatGPT's (prime_scale, arch_scale) grid points
against my geometric Weil form at N=24 (separate pole/arith/arch matrices)."""
import time
import mpmath as mp
import recon2_weil_nscaling as R

mp.mp.dps = 60
N = 24
Lc = R.Lc
basis = R.shifted_legendre(N, Lc)
M = R.precompute_M(N - 1, Lc)
G = {}
for j in range(N):
    for k in range(j + 1):
        gjk = R.autocorr(basis[j], basis[k], M)
        gkj = R.autocorr(basis[k], basis[j], M)
        G[(j, k)] = [(x + y) / 2 for x, y in zip(gjk, gkj)]

Qp = mp.matrix(N, N); Qa = mp.matrix(N, N); Qi = mp.matrix(N, N)
for j in range(N):
    for k in range(j + 1):
        g = G[(j, k)]
        Qp[j, k] = Qp[k, j] = R.pole_term(g)
        Qa[j, k] = Qa[k, j] = R.arith_term(g)   # positive-sign prime matrix
        Qi[j, k] = Qi[k, j] = R.arch_term(g)
print("matrices built")

gpt = {(1.0, 1.0): 4.44e-23, (0.998, 1.0): -0.003407, (1.002, 1.0): -0.005276,
       (1.0, 0.998): -0.001773, (1.0, 1.002): -0.005712, (0.998, 0.998): -0.001054,
       (1.002, 1.002): -0.010728, (0.99, 0.99): -0.005689, (0.99, 1.0): -0.017948,
       (1.0, 0.99): -0.009485, (0.95, 1.0): -0.031517, (1.0, 0.95): -0.020357}
print("(s_prime, s_arch): my N=24 lam_min  |  ChatGPT calibrated_lambda_min")
for (sp, sa), ref in gpt.items():
    Q = Qp - mp.mpf(str(sp)) * Qa + mp.mpf(str(sa)) * Qi
    E = mp.eigsy(Q, eigvals_only=True)
    lam = min(E[i] for i in range(N))
    print("  (%.3f, %.3f): %s   |  %g" % (sp, sa, mp.nstr(lam, 6), ref))
