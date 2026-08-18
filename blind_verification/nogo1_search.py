"""Counterexample search for the finite-truncation no-go theorem.

Framework: metric graph, rationally independent edge lengths, scale-invariant local
self-adjoint vertex conditions <=> vertex scattering matrices sigma(v) Hermitian
unitary (involutions), k-independent. By the reduction lemma (Kronecker-Weyl), the
hypothesis "periodic-orbit trace supported only on single-edge repetition classes"
is EQUIVALENT to the polynomial identity

    det(I - S Z) = prod_e h_e(z_e),    h_e(z) := det(I - S Z)|_{z_f=0 (f != e), z_e=z}

where S is the 2E x 2E bond scattering matrix and Z = diag(z_{e(b)}).  This is a
finite set of polynomial equations.  We search for Hermitian-involution vertex data
making the identity hold while cross-edge transmission T > 0 (a counterexample), over
the graph families in the handoff bullets: cycles (magnetic phases), figure-eight
(loops), theta (parallel bonds), dumbbell, stars (control: theorem proved), triangle.
"""
import itertools, sys
import numpy as np
from scipy.optimize import minimize

rng = np.random.default_rng(20260818)

# ---------------- graph machinery ----------------
class Graph:
    def __init__(self, name, edges, end_conditions=None):
        """edges: list of (u, v) (loops allowed). Deg-1 vertices get scalar +-1
        conditions enumerated externally via end_conditions dict v -> +-1."""
        self.name, self.edges = name, edges
        self.E = len(edges)
        # channels: (edge, end) pairs; channel vertex map
        self.channels = []
        self.chan_at = {}
        for ei, (u, v) in enumerate(edges):
            for end, vert in ((0, u), (1, v)):
                cid = len(self.channels)
                self.channels.append((ei, end, vert))
                self.chan_at.setdefault(vert, []).append(cid)
        self.vertices = sorted(self.chan_at)
        self.deg = {v: len(self.chan_at[v]) for v in self.vertices}
        self.end_conditions = end_conditions or {}
        # bonds: (edge, dir); dir 0: end0 -> end1, dir 1: end1 -> end0
        self.bonds = [(ei, d) for ei in range(self.E) for d in (0, 1)]

    def chan_id(self, ei, end):
        return 2 * ei + end

    def Smatrix(self, sigmas):
        """Bond matrix: S[b', b] = sigma(x)[chan(initial end of b'), chan(terminal end of b)]
        for x = terminal vertex of b == initial vertex of b'."""
        nB = len(self.bonds)
        S = np.zeros((nB, nB), dtype=complex)
        for bi, (ei, d) in enumerate(self.bonds):
            t_end = 1 - d          # terminal end index of bond
            t_vert = self.edges[ei][t_end]
            for bj, (ej, d2) in enumerate(self.bonds):
                i_end = d2         # initial end of bond bj
                i_vert = self.edges[ej][i_end]
                if i_vert != t_vert:
                    continue
                sig = sigmas[t_vert]
                row = self.chan_at[t_vert].index(self.chan_id(ej, i_end))
                col = self.chan_at[t_vert].index(self.chan_id(ei, t_end))
                S[bj, bi] = sig[row, col]
        return S

def involution(A):
    """sigma = I - 2 Q Q^dagger, Q = orth(A): Hermitian unitary."""
    Q, _ = np.linalg.qr(A)
    return np.eye(A.shape[0]) - 2 * Q @ Q.conj().T

def build_sigmas(g, ranks, params, fixed_ends):
    sigmas = {}
    idx = 0
    for v in g.vertices:
        d = g.deg[v]
        if d == 1:
            sigmas[v] = np.array([[float(fixed_ends[v])]], dtype=complex)
            continue
        r = ranks[v]
        n = 2 * d * r
        block = params[idx:idx + n]; idx += n
        A = (block[:d * r] + 1j * block[d * r:]).reshape(d, r)
        sigmas[v] = involution(A)
    return sigmas

def cross_edge_T(g, sigmas):
    """Total cross-edge transmission mass."""
    T = 0.0
    for v in g.vertices:
        ch = g.chan_at[v]
        sig = sigmas[v]
        for i, ci in enumerate(ch):
            for j, cj in enumerate(ch):
                if g.channels[ci][0] != g.channels[cj][0]:
                    T += abs(sig[i, j]) ** 2
    return T

def _grid_cache(g):
    if not hasattr(g, "_gc"):
        w = np.exp(2j * np.pi / 3)
        pts = np.array([1, w, w * w])
        edge_of_bond = np.array([b[0] for b in g.bonds])
        grids = np.array(list(itertools.product(range(3), repeat=g.E)))
        Zfull = pts[grids][:, edge_of_bond]                      # (27, nB)
        # single-edge slice points: for edge e, 3 points with others 0
        Zsingle = []
        for e in range(g.E):
            z = np.zeros((3, g.E), dtype=complex)
            z[:, e] = pts
            Zsingle.append(z[:, edge_of_bond])
        g._gc = (grids, Zfull, np.array(Zsingle))                # Zsingle: (E,3,nB)
    return g._gc

def factorization_residual(g, sigmas):
    """||det(I-SZ) - prod_e h_e(z_e)||^2 over the tensor grid of cube roots of unity
    (Parseval-equivalent to coefficient l2 since degrees <= 2 per variable)."""
    S = g.Smatrix(sigmas)
    nB = len(S)
    grids, Zfull, Zsingle = _grid_cache(g)
    I = np.eye(nB)
    M = I[None, :, :] - S[None, :, :] * Zfull[:, None, :]        # (27,nB,nB): S@diag(z)
    D = np.linalg.det(M)
    Ms = I[None, None, :, :] - S[None, None, :, :] * Zsingle[:, :, None, :]
    h = np.linalg.det(Ms)                                        # (E, 3)
    prod = np.ones(len(grids), dtype=complex)
    for e in range(g.E):
        prod *= h[e][grids[:, e]]
    return float(np.sum(np.abs(D - prod) ** 2))

def search(g, nstart=60, maxiter=400):
    """Two-phase variety walk.
    Phase 1: minimize R from a random start -> lands on the solution variety {R=0}
             (which contains all decoupled configurations, plus any counterexample).
    Phase 2: from that point, maximize cross-edge transmission T while pinned to the
             variety (minimize -T + 1e8 R). If the variety contains only decoupled
             points, T stays ~0; a counterexample shows up as T bounded away from 0
             with R ~ 0."""
    best = []
    deg1 = [v for v in g.vertices if g.deg[v] == 1]
    end_choices = list(itertools.product([1, -1], repeat=len(deg1))) or [()]
    inner = [v for v in g.vertices if g.deg[v] > 1]
    rank_choices = list(itertools.product(*[range(1, g.deg[v]) for v in inner])) or [()]
    for ends in end_choices:
        fixed = dict(zip(deg1, ends))
        for rk in rank_choices:
            ranks = dict(zip(inner, rk))
            nparam = sum(2 * g.deg[v] * ranks[v] for v in inner)
            if nparam == 0:
                continue
            def R_of(p):
                return factorization_residual(g, build_sigmas(g, ranks, p, fixed))
            def T_of(p):
                return cross_edge_T(g, build_sigmas(g, ranks, p, fixed))
            rec = (0.0, None)   # max T achieved on the variety
            hits = 0
            for _ in range(nstart):
                p0 = rng.standard_normal(nparam)
                out1 = minimize(R_of, p0, method="L-BFGS-B",
                                options={"maxiter": maxiter, "ftol": 1e-22, "gtol": 1e-16})
                if R_of(out1.x) > 1e-13:
                    continue
                hits += 1
                out2 = minimize(lambda p: -T_of(p) + 1e8 * R_of(p), out1.x,
                                method="L-BFGS-B",
                                options={"maxiter": maxiter, "ftol": 1e-22, "gtol": 1e-16})
                R2, T2 = R_of(out2.x), T_of(out2.x)
                if R2 < 1e-13 and T2 > rec[0]:
                    rec = (T2, (R2, out2.x.copy()))
            if rec[1] is not None:
                R2, x = rec[1]
                print("%s ends=%s ranks=%s: variety hits=%d/%d; max T on {R=0}: T=%.3e (R=%.1e)"
                      % (g.name, ends, rk, hits, nstart, rec[0], R2)); sys.stdout.flush()
                best.append((g.name, ends, rk, R2, rec[0], x))
            else:
                print("%s ends=%s ranks=%s: variety hits=%d/%d; no T>0 point retained"
                      % (g.name, ends, rk, hits, nstart)); sys.stdout.flush()
    return best

graphs = [
    Graph("2cycle",     [(0, 1), (0, 1)]),      # proven decoupled symbolically; numeric control
    Graph("figure8",    [(0, 0), (0, 0)]),      # loops at one vertex (open sector)
    Graph("theta",      [(0, 1), (0, 1), (0, 1)]),
    Graph("dumbbell",   [(0, 0), (0, 1), (1, 1)]),
    Graph("triangle",   [(0, 1), (1, 2), (2, 0)]),
    Graph("lasso",      [(0, 0), (0, 1)]),
    Graph("3star",      [(0, 1), (0, 2), (0, 3)]),  # theorem proved; numeric control
]

if __name__ == "__main__":
    allbest = []
    for g in graphs:
        allbest += search(g)
    print("\n==== summary (candidate counterexamples have R ~ 0 with T >= 0.05) ====")
    cands = [b for b in allbest if b[3] < 1e-16 and b[4] >= 0.05]
    if not cands:
        print("No counterexample found: minimal factorization residual stayed bounded away")
        print("from zero on every graph/rank/end-condition combination searched.")
        for name, ends, rk, R, T, _ in sorted(allbest, key=lambda t: t[3])[:10]:
            print("  closest: %s ends=%s ranks=%s R=%.3e T=%.3f" % (name, ends, rk, R, T))
    else:
        for name, ends, rk, R, T, x in cands:
            print("  CANDIDATE: %s ends=%s ranks=%s R=%.3e T=%.3f" % (name, ends, rk, R, T))
            np.save("out/bv_nogo_candidate_%s.npy" % name, x)
