"""Shared machinery for Experiments 8-9: finite Weil quadratic form.

Conventions (explicit formula, Iwaniec-Kowalski style):
  g even (or Hermitian-symmetrized), h(r) = int g(u) e^{iru} du.
  sum_rho h(gamma_rho) = [pole] h(i/2) + h(-i/2)
                         - [arith] sum_{n>=2} Lambda(n) n^{-1/2} (g(log n) + g(-log n))
                         + [arch]  (1/2pi) int h(r) (Re psi(1/4 + ir/2) - log pi) dr.
  The archimedean term is evaluated in u-space via the identity (derived from
  psi(z) = -gamma + int_0^1 (1-t^{z-1})/(1-t) dt, t = e^{-2u}):
     A_inf(g) = -(euler_gamma + log pi) g(0)
                + int_0^inf [2 g(0) e^{-2u} - 2 g(u) e^{-u/2}] / (1 - e^{-2u}) du
  (g even). Signs validated numerically against the zero-side sum (see exp8 script).

Weil positivity: RH <=> W(f * f~) >= 0 for all test f. The finite form is
Q_{jk} = W(sym(f_j * f~_k)) for a polynomial basis f_j on [0, log c].
"""
import mpmath as mp
import sympy as sp

U = sp.symbols('u', real=True)
V = sp.symbols('v', real=True)

def legendre_basis(N, L):
    """Shifted Legendre polynomials P_j(2u/L - 1) on [0, L], as sympy polys in U."""
    return [sp.expand(sp.legendre(j, 2 * U / L - 1)) for j in range(N)]

def autocorrelation(fj, fk, L):
    """g(u) = int_0^{L-u} fj(v+u) fk(v) dv for 0 <= u <= L (poly in U).
    For u < 0 use g_{jk}(-u) = g_{kj}(u). Returns sympy polynomial (piece u in [0,L])."""
    integrand = sp.expand(fj.subs(U, V + U) * fk.subs(U, V))
    g = sp.integrate(integrand, (V, 0, L - U))
    return sp.expand(g)

class WeilForm:
    def __init__(self, N, c, dps=40, lam=None):
        """lam: dict n -> Lambda(n)-like coefficient (mpf). If None, computed from
        the Experiment-2 recursion B(n) (no prime list used)."""
        self.N, self.dps = N, dps
        mp.mp.dps = dps
        self.Lc = mp.log(c)
        Lsym = sp.Rational(0)  # placeholder
        # build symbolic basis with L as exact log(c) via a symbol substituted numerically:
        # simpler: use L as a sympy Float at high precision
        self.Lsp = sp.Float(mp.nstr(self.Lc, dps + 5), dps + 5)
        self.basis = legendre_basis(N, self.Lsp)
        # symmetrized autocorrelation pieces G[j][k](u) = (g_jk(u) + g_kj(u))/2, u in [0,L]
        self.G = [[None] * N for _ in range(N)]
        for j in range(N):
            for k in range(j + 1):
                gjk = autocorrelation(self.basis[j], self.basis[k], self.Lsp)
                gkj = autocorrelation(self.basis[k], self.basis[j], self.Lsp)
                Gsym = sp.expand((gjk + gkj) / 2)
                self.G[j][k] = self.G[k][j] = Gsym
        # compile to mpmath-evaluable coefficient lists
        self.Gcoef = [[self._coeffs(self.G[j][k]) for k in range(N)] for j in range(N)]
        # arithmetic coefficients from Experiment-2 recursion
        if lam is None:
            lam = self.recursion_lambda(int(mp.floor(mp.e ** self.Lc)) + 1)
        self.lam = lam
        self.ns = sorted(n for n in lam if lam[n] != 0 and mp.log(n) < self.Lc)

    @staticmethod
    def recursion_lambda(Nmax):
        """B(n) from Experiment 2 recursion at working precision (no prime list)."""
        B = {1: mp.mpf(0)}
        for n in range(2, Nmax + 1):
            s = mp.mpf(0)
            for d in range(1, n):
                if n % d == 0:
                    s += B[d]
            B[n] = mp.log(n) - s
        return {n: (B[n] if abs(B[n]) > mp.mpf(10) ** (-self_dps_guess()) else mp.mpf(0))
                for n in range(2, Nmax + 1)}

    def _coeffs(self, poly):
        p = sp.Poly(poly, U)
        return [mp.mpf(str(c)) for c in reversed(p.all_coeffs())]  # low -> high

    def _eval(self, coefs, u):
        tot = mp.mpf(0)
        up = mp.mpf(1)
        for c in coefs:
            tot += c * up
            up *= u
        return tot

    def Geval(self, j, k, u):
        """Symmetrized autocorrelation at u >= 0 (0 outside [0, L])."""
        if u < 0: u = -u
        if u >= self.Lc: return mp.mpf(0)
        return self._eval(self.Gcoef[j][k], u)

    # ----- explicit-formula components (for even g given by (j,k) pair) -----
    def pole_term(self, j, k):
        f = lambda u: self.Geval(j, k, u) * 2 * mp.cosh(u / 2)
        return 2 * mp.quad(f, [0, self.Lc])  # int over R = 2 * int_0^L for even g

    def arith_term(self, j, k, lam=None):
        lam = lam or self.lam
        tot = mp.mpf(0)
        for n in self.ns:
            tot += lam[n] / mp.sqrt(n) * self.Geval(j, k, mp.log(n))
        return 2 * tot  # g(log n) + g(-log n) = 2 g(log n)

    def arch_term(self, j, k):
        c = self.Gcoef[j][k]
        g0 = c[0]
        gp0 = c[1] if len(c) > 1 else mp.mpf(0)  # right-derivative at 0+ (even ext. has kink)
        def integrand(u):
            if u < mp.mpf(10) ** (-8):
                return (-3 * g0 - 2 * gp0) / 2  # removable-singularity limit
            return (2 * g0 * mp.e ** (-2 * u) - 2 * self.Geval(j, k, u) * mp.e ** (-u / 2)) / (1 - mp.e ** (-2 * u))
        main = mp.quad(integrand, [0, self.Lc])
        tail = -g0 * mp.log(1 - mp.e ** (-2 * self.Lc))
        return -(mp.euler + mp.log(mp.pi)) * g0 + main + tail

    def Q_entry(self, j, k, lam=None, arch_scale=1, pole_scale=1):
        return (pole_scale * self.pole_term(j, k)
                - self.arith_term(j, k, lam)
                + arch_scale * self.arch_term(j, k))

    def Q_matrix(self, lam=None, arch_scale=1, pole_scale=1):
        N = self.N
        Q = mp.matrix(N, N)
        for j in range(N):
            for k in range(j + 1):
                v = self.Q_entry(j, k, lam, arch_scale, pole_scale)
                Q[j, k] = Q[k, j] = v
        return Q

def self_dps_guess():
    return max(10, mp.mp.dps - 8)

def eigvals_sym(Q):
    E = mp.eigsy(Q, eigvals_only=True)
    return sorted([E[i] for i in range(len(E))])
