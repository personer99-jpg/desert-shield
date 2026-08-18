"""Supplement: positivity-breaking threshold eps* and near-null block analysis."""
import mpmath as mp
from weil_form import WeilForm, eigvals_sym

mp.mp.dps = 40
W = WeilForm(N=8, c=13, dps=40)
Qp = mp.matrix(8, 8); Qi = mp.matrix(8, 8); Qa0 = mp.matrix(8, 8); Dq = mp.matrix(8, 8)
delta = mp.mpf("0.2")
lam1 = {n: W.lam[n] * (1 + mp.power(n, -delta)) for n in W.lam}
for j in range(8):
    for k in range(j + 1):
        Qp[j, k] = Qp[k, j] = W.pole_term(j, k)
        Qi[j, k] = Qi[k, j] = W.arch_term(j, k)
        a0 = -W.arith_term(j, k)
        Qa0[j, k] = Qa0[k, j] = a0
        Dq[j, k] = Dq[k, j] = -W.arith_term(j, k, lam1) - a0
Q0 = Qp + Qi + Qa0

for e in ["1e-8", "1e-7", "1e-6", "1e-5", "1e-4", "1e-3"]:
    for sgn in [1, -1]:
        eps = sgn * mp.mpf(e)
        ev = eigvals_sym(Q0 + eps * Dq)
        print("eps=%9s: lam_min = %s  lam_2 = %s" % (mp.nstr(eps, 3), mp.nstr(ev[0], 8), mp.nstr(ev[1], 8)))

# project deformation onto the 2-dim near-null subspace
Ev, V = mp.eigsy(Q0)
idx = sorted(range(8), key=lambda i: Ev[i])[:2]
import itertools
print("\nnear-null eigenvalues:", [mp.nstr(Ev[i], 8) for i in idx])
B = mp.matrix(2, 2)
for a, ia in enumerate(idx):
    for b, ib in enumerate(idx):
        B[a, b] = mp.fsum(V[i, ia] * Dq[i, j] * V[j, ib] for i in range(8) for j in range(8))
print("2x2 near-null block of dQ/deps:")
print("  [[%s, %s], [%s, %s]]" % tuple(mp.nstr(B[i, j], 6) for i in range(2) for j in range(2)))
bev = mp.eig(mp.matrix([[B[0,0], B[0,1]], [B[1,0], B[1,1]]]), left=False, right=False)
print("block eigenvalues:", [mp.nstr(mp.re(x), 6) for x in bev])
print("=> indefinite block means positivity breaks for BOTH signs at eps ~ lam_min/|block eig|")
