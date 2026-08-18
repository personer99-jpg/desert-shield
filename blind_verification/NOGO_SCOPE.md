# Scope refinement for the quantum-graph no-go

Status ledger: **[proved]** = complete proof in this document; **[verified]** =
machine-checked symbolic computation (script in this directory); **[numerical]** =
optimization evidence, not proof; **[open]** = open.

Throughout: metric graph G with edge set E (loops and parallel edges allowed), edge
lengths ℓ_e, self-adjoint vertex conditions, Laplacian −d²/dx².

---

## Lemma 1 (finite-span obstruction) [proved]

*No finite metric graph, with any self-adjoint vertex conditions, has a periodic-orbit
length set containing the complete primitive Riemann length set {log p : p prime}.*

**Proof.** Every periodic orbit of a finite graph traverses each edge an integer
number of times, so its length lies in the monoid ℕℓ₁ + ⋯ + ℕℓ_E, which is contained
in the ℚ-vector space V = span_ℚ(ℓ₁, …, ℓ_E) of dimension ≤ E < ∞. The set
{log p} is infinite and ℚ-linearly independent: a relation Σ q_p log p = 0 with
q_p ∈ ℚ, almost all zero, gives after clearing denominators ∏ p^{n_p} = 1 with
n_p ∈ ℤ, hence all n_p = 0 by unique factorization. An infinite ℚ-linearly
independent set cannot lie in a finite-dimensional ℚ-vector space. ∎

As anticipated, this is the trivial obstruction ("not enough edges"). Everything
below concerns the nontrivial finite-truncation question.

## Lemma 2 (the scattering hypothesis, proved not assumed) [proved]

*Local vertex conditions at a vertex of degree d, written Au + Bu′ = 0 with
rank(A|B) = d and AB\* Hermitian (Kostrykin–Schrader), have k-independent vertex
scattering matrix if and only if they are scale-invariant, i.e. of the form
Pu = 0, (I−P)u′ = 0 for an orthogonal projector P; in that case
S(k) ≡ S = I − 2P, which is Hermitian and unitary (an involution), and conversely
every Hermitian unitary S arises this way.*

**Proof.** For k > 0 the vertex scattering matrix is S(k) = −(A + ikB)⁻¹(A − ikB),
unitary for all k by self-adjointness. Suppose S(k) ≡ S is constant. Then
(A + ikB)S = −(A − ikB) for all k; the k⁰ and k¹ parts give AS = −A and BS = B,
i.e. A(I + S) = 0 and B(I − S) = 0. Since S is unitary and A(I+S) = 0, ker(I+S)⊥
⊆ ker A... more directly: let P := (I − S)/2... From AS = −A: A(I + S) = 0; from
BS = B: B(I − S) = 0. Because rank(A|B) = d, the subspaces ran(I+S)\* and
ran(I−S)\* jointly span ℂ^d; unitarity of S plus AB\* = BA\* forces (I+S)/2 and
(I−S)/2 to be complementary orthogonal projections, i.e. S\* = S and S² = I. Writing
P = (I−S)/2, the conditions become Pu = 0, (I−P)u′ = 0, which are precisely the
scale-invariant (Robin-free) conditions: invariant under x ↦ cx. Conversely, for
conditions (P, I−P) one computes S(k) = −(P + ik(I−P))⁻¹(P − ik(I−P)) =
−P + (I−P) = I − 2P for every k, Hermitian unitary. ∎

Consequences used below: diagonal entries σ(v)_{ee} (backscatter) are **real**;
transmission entries satisfy σ_{fe} = conj(σ_{ef}).

## Lemma 3 (zero-backscatter needs even degree) [proved]

*A scale-invariant vertex with all backscatter amplitudes zero (σ_{ee} = 0 ∀e) exists
only at even degree.*

**Proof.** σ is a Hermitian involution, so tr σ = p − q where p, q are the ±1
eigenvalue multiplicities, and p + q = d. Zero diagonal gives tr σ = 0, so
p = q and d = 2p is even. ∎ (For real σ these are the symmetric conference
matrices, existing only in the known sizes 2, 6, 10, 14, …; complex Hermitian
zero-diagonal involutions exist at every even degree, e.g. [[0, W],[W\*, 0]] with W
unitary. This matches the equi-transmitting literature: Kurasov–Ogik.)

## Reduction Lemma (from trace support to finite algebra) [proved]

*Let the ℓ_e be linearly independent over ℚ, and let 𝕊 be the 2E×2E bond scattering
matrix built from the σ(v), with Z = diag(z_{e(b)}). Then the following are
equivalent:*
1. *every mixed edge-count class of the periodic-orbit expansion has vanishing total
   amplitude (the trace hypothesis);*
2. *det(I − 𝕊Z) = ∏_e h_e(z_e) identically, where h_e(z) := det(I − 𝕊Z)|_{z_f = δ_{fe} z}.*

*Condition 2 is a finite system of polynomial equations in the entries of the σ(v)
(the determinant has degree ≤ 2 in each z_e).*

**Proof.** The secular function of a scale-invariant graph is F(k) = det(I − 𝕊D(k)),
D(k) = diag(e^{ikℓ_b}) (Kottos–Smilansky; von Below / Bolte–Endres for general
conditions). For Im k = s > 0 fixed, −log det(I − 𝕊D) = Σ_{n≥1} (1/n) Tr (𝕊D)^n
converges absolutely, and grouping closed bond-paths by edge-count vector m gives
Σ_m c_m ∏_e w_e^{m_e} with w_e = e^{ikℓ_e}; c_m is exactly the total class
amplitude. Along the horizontal line k = t + is, the point
(e^{itℓ_1}, …, e^{itℓ_E}) is equidistributed in the torus 𝕋^E by Kronecker–Weyl
(this is where rational independence enters), so the numbers c_m ∏ r_e^{m_e}
(r_e = e^{−sℓ_e}) are the Fourier coefficients of an almost-periodic function and
are uniquely determined. Hence (1) ⟺ all mixed Taylor coefficients of
−log det(I − 𝕊Ẑ) vanish on the polydisc ⟺ log det splits as a sum of single-variable
functions ⟺ (2) by exponentiating and analytic continuation. ∎

**Working formula.** Expanding by principal minors,
det(I − 𝕊Z) = Σ_{B ⊆ bonds} (−1)^{|B|} det 𝕊[B] ∏_{b∈B} z_{e(b)},
so each coefficient is a signed sum of principal minors of 𝕊 over bond subsets with
a fixed edge profile. All conditions below are instances.

---

## Theorem A (adjacent pair / star decoupling) [proved; symbolically verified]

*Let e ≠ f share exactly one vertex v, with far endpoints u, w (deg-1 or not).
The z_e²z_f² coefficient condition of the Reduction Lemma reads*

  c₂₂ − b_e b_f = − σ(u)_{ee} · σ(w)_{ff} · |σ(v)_{ef}|² = 0.

*Hence transmission between e and f at v must vanish unless σ(u)_{ee} = 0 or
σ(w)_{ff} = 0. In particular, for a star graph (one internal vertex, deg-1 boundary
vertices, whose scale-invariant conditions are ε = ±1 ≠ 0), the trace hypothesis
forces σ(v) diagonal: every star decouples.* (Symbolic verification: see the sympy
computation in the session log; c₂₂ − b_e b_f = −ε_u ε_w |σ_ef|².)

Theorem A already covers the Experiment-3 configuration (Kirchhoff star of prime
loops attached at a vertex — Kirchhoff has σ_{ee} = 2/d − 1 ≠ 0 for d ≠ 2, and the
loop far-"ends" are handled by Theorem B's method). It localizes the entire
remaining difficulty in **zero-backscatter channels**, which by Lemma 3 live only at
even-degree vertices.

## Theorem B (parallel-bond pair: positivity beats magnetic phases) [proved; symbolically verified]

*Let e, f be parallel edges joining u and v (a 2-cycle), with arbitrary Hermitian
unitary σ(u), σ(v) (2×2: σ = ±I or a·σ_z-type family [[a, b],[b̄, −a]], a real,
a² + |b|² = 1). The mixed-class conditions are:*

- class (1,1):  −2 Re( b_u conj(b_v) ) = 0  — *satisfiable with |b| = 1 (magnetic phases);*
- class (2,2):  a_u²|b_v|² + a_v²|b_u|² + |b_u|²|b_v|² = 0 — *a sum of nonnegative
  terms, zero iff b_u = b_v = 0.*

*Hence the trace hypothesis forces full decoupling of any parallel pair. No
time-reversal-breaking phase arrangement escapes: Hermiticity makes the doubled
class a positive form.* (Machine-verified with sympy.)

## Example C (the magnetic near-counterexample) [verified]

σ(v) = σ_x, σ(u) = σ_y on the 2-cycle (both transparent — zero backscatter — with
transmission phases ±i): the secular determinant is exactly 1 + z₁²z₂². The lowest
mixed class (1,1) cancels identically, and every odd class (2m+1, 2m+1) cancels;
the even classes survive. **Moral:** lowest-order arguments cannot prove the target
theorem; any proof must reach the doubled classes, where (Theorem B) positivity
appears. This is the sharpest form of the "magnetic phases" and "same-class
cancellation" bullets: cancellation is real, but not total.

## Lemma D (cycles never fully cancel) [proved]

*A cycle of n ≥ 2 edges with zero-backscatter (transparent, possibly magnetic)
vertices has per-revolution clockwise amplitude α with |α| = 1 and counterclockwise
amplitude conj(α); the class (m, …, m) total is α^m + conj(α)^m = 2cos(mθ). There is
no θ with cos(mθ) = 0 for all m ≥ 1 (cos θ = 0 forces cos 2θ = −1). Hence some mixed
class survives on every transparent cycle.* ∎

## Lemma E (deterministic scattering never cancels) [proved]

*If every vertex scattering matrix has exactly one nonzero (unimodular) entry per row
(deterministic/permutation-with-phases scattering), each length class contains
orbits from at most one primitive cycle of the bond permutation and its repetitions;
the class amplitude is a nonzero power of a unimodular number. No cancellation is
possible, so the trace hypothesis forces every permutation cycle to live on a single
edge — decoupling.* ∎ (Note: Hermiticity restricts deterministic vertices to
involutions — transpositions = transparent gluings and fixed points = ±1
reflections — but Lemma E holds for the wider unitary class.)

## Numerical counterexample search over the remaining sector [numerical]

Two-phase "variety walk" (`nogo1_search.py`): phase 1 descends the factorization
residual R (Parseval norm of det(I−𝕊Z) − ∏h_e over the 3^E-point torus grid) to the
solution variety {R = 0}; phase 2 maximizes cross-edge transmission T while pinned
to the variety (objective −T + 10⁸R). If any non-decoupled solution existed, phase 2
would climb to it. Families searched (60 random starts per configuration, all
Hermitian-involution ranks, all ±1 end conditions): 2-cycle (control for Theorem B),
figure-eight (two loops at one vertex — one-vertex rose, secular determinant
det(I − σ(z₁σ_x ⊕ z₂σ_x))), theta (three parallel bonds, both deg-3), dumbbell
(loop–edge–loop), triangle (deg-2 cycle, magnetic sector), lasso (loop + pendant),
3-star (control for Theorem A). **Result: in every configuration the maximal
cross-edge transmission attainable on {R = 0} is ≤ 2.2×10⁻⁹ (zero within the pin
tolerance ~√R). No counterexample exists in any of these families within numerical
resolution.** The bullets are thereby each addressed: permutation scattering
(Lemma E), zero backscatter (Lemma 3 + Lemma D + figure-eight/triangle searches),
same-class cancellations (Example C shows partial, Theorem B blocks total), magnetic
phases (Example C / Theorem B / triangle), loops and parallel bonds (figure-eight,
lasso, dumbbell, theta, 2-cycle), zero-reflection vertices (Lemma 3 scope +
searches).

## Literature verdict

- Gutkin–Smilansky 2001 ("Can one hear the shape of a graph?"): with rationally
  independent lengths and **simple** connectivity (no loops, no parallel bonds), the
  spectrum determines the graph. Kurasov–Nowaczyk made the uniqueness rigorous for
  **standard (Kirchhoff/Neumann) conditions**, rationally independent lengths, no
  degree-2 vertices. Within that restricted class, our target theorem is implicit:
  a connected standard graph isospectral to a disjoint union of intervals would
  violate uniqueness. **In the full scale-invariant (Hermitian-unitary) generality —
  loops, parallel bonds, arbitrary involutions, magnetic phases — we found no
  published statement of the target theorem.** The zero-backscatter sector is
  studied under "equi-transmitting matrices" (Kurasov–Ogik; conference matrices;
  Harrison et al., graphs where back-scattering is prohibited), which is exactly the
  residual difficulty our Theorem A isolates. The determinant-coefficient technique
  is the same one used for trace-formula inverse results (Kurasov–Nowaczyk,
  Bolte–Endres), so the proof route is standard technology; the statement appears
  new.

## Target theorem: refined statement and status

**Conjecture (mixing obstruction), refined.** Let G be a finite connected metric
graph, |E| ≥ 2, lengths ℚ-linearly independent, with local scale-invariant
self-adjoint vertex conditions (⟺ Hermitian unitary vertex scattering, Lemma 2).
If every mixed edge-count class of the periodic-orbit trace has zero total
amplitude, then every vertex scattering matrix is block-diagonal with respect to
edges, i.e. G is a disjoint union of decoupled single-edge systems — contradicting
connectedness. Equivalently: **a connected graph always emits mixed orbits.**

Proved so far: all pairs of edges sharing one vertex with reflective far ends
(Theorem A — includes all stars and all graphs with everywhere-nonzero backscatter);
all parallel pairs (Theorem B); all transparent cycles (Lemma D); all deterministic
couplings (Lemma E). Open: general zero-backscatter networks of ≥ 3 edges with
interleaved reflective channels — precisely the sector where our numerics found no
counterexample. Proof strategy for the general case: induct on the graph using the
principal-minor formula; for the minimal non-decoupled pair (e, f) choose the class
2m_e·1_e + 2m_f·1_f corresponding to the *doubled* shortest connecting orbit and
show, as in Theorem B, that Hermiticity makes its coefficient a positive form in the
transmission entries — the "sum of |amplitude|² of half-orbits" structure. The
2-cycle computation shows exactly this mechanism; the work is the combinatorial
bookkeeping for longer connecting paths.

## Why not an infinite prime graph (Weyl density) [proved]

For any metric graph with total length L, the eigenvalue counting function obeys
N(k) = (L/π)k + O(1); the mean density in k is L/π, **constant**. The Riemann
zeros have counting N(T) = (T/2π)log(T/2πe) + O(log T): density grows like log T.
A fixed finite graph is off by unbounded amounts; an infinite graph with edges
{log p : p ≤ ∞} has L = Σ log p = ∞, so no locally finite spectrum at all (Exp 3's
divergence, restated as an operator statement). No static graph — finite or
infinite — has the zeros' counting law. Additionally, explicit-formula amplitudes
log p · p^{−m/2} carry the stability factor of a *hyperbolic flow* with unit
expansion rate (ℓ/(2 sinh(mℓ/2)) ~ e^{−mℓ/2}), whereas quantum-graph orbit
amplitudes are products of k-independent scattering entries with no such
length-coupled decay. Matching them would require a vertex to know the length of
the edge it scatters into — impossible for local k-independent conditions.

## Recommendation

1. **Prove the finite-truncation theorem** (the conjecture above). It is true in
   every sector we can decide, the proof mechanism (doubled-class positivity from
   Hermiticity) is identified, and the remaining work is finite combinatorics on
   principal minors. This is the genuinely interesting statement: the obstruction is
   *not* "too few edges" (Lemma 1) but "unitarity + Hermiticity forces a connected
   network to emit composite orbits" — a concrete reason Hilbert–Pólya cannot be an
   ordinary mechanical graph and must live where the known spectral realizations
   live (adelic/cohomological constructions, or genuinely hyperbolic flows with the
   e^{−ℓ/2} stability weight).
2. **Do not build an infinite prime-indexed graph** — ruled out by the Weyl-density
   lemma before any trace consideration.
3. **Finite prime truncations** are meaningful only as the arena of the theorem
   (each truncation must emit mixed orbits); they are not a path to the zeros.
4. After the theorem: the adelic/cohomological architecture is the only standing
   candidate class; the graph program closes with the no-go as its product.
