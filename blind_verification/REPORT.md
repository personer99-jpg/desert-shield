# Blind Verification Report — Prime / Riemann "Machine" Research

Independent replication performed 2026-08-18. All code is in this directory
(`exp1`–`exp9b`, `weil_form.py`); all fresh outputs are under `out/` with `bv_` prefixes.

## Preliminary finding: the sealed comparison data does not exist

The handoff names 25 sealed CSV files (plus PNGs) to be compared against after blind
replication. **None of these files exist in this repository, in its git history, or
anywhere on this machine's filesystem.** The repository (`desert-shield`) contains only a
static website for an auto-body business. Consequently:

- The blind-verification protocol was trivially honored (nothing to peek at).
- **No comparison with the previous run's numbers is possible.** Everything below is a
  from-scratch replication of the *described* experiments, judged on its own results.
- Any statement in the previous analysis about specific numerical values is therefore
  **unverifiable**, and the previous conclusions should be treated as unsupported until
  the original data or code is produced.

---

## A. Independent replication results

### Experiment 1 — Multiplicative circle dynamics (fully reproduced)
- **Composition:** T_m∘T_n = T_{mn} exactly (2000 exact rational trials). The semigroup
  {T_n} is isomorphic to (ℕ_{≥2}, ×).
- **Indecomposables:** brute-force search through n = 1000 yields 168 indecomposables,
  first 15: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47 — exactly the primes
  (168 = π(1000)). This is the definition of primality restated; no discovery.
- **Periodic points:** #Fix(T_n^r) = n^r − 1, verified by direct orbit enumeration for
  n ∈ {2,…,6,10}, r ≤ 3. Entropy h_n = log n (max deviation 2.3·10⁻¹⁴ at r = 40).
- **Commutator:** U_n e_k = e_{nk}; with D e_k = (log k) e_k the relation
  **[D, U_n] = (log n)·U_n holds exactly** (verified coefficientwise, error ≤ 1.3·10⁻¹⁵;
  it is an algebraic identity: log(nk) − log(k) = log n).
- **Thermal trace:** Tr e^{−βD} = Σ k^{−β} = ζ(β), matching independent high-precision
  ζ values to ≥ 15 digits for β ∈ {1.5, 2, 2.5, 3, 4}.

### Experiment 2 — Connected response (fully reproduced)
Computed B(n) through 2·10⁵ (handoff asked ≥10⁵). Support = exactly the 18,120 prime
powers ≤ 2·10⁵; value on p^k is log p (max deviation 1.6·10⁻¹⁵); B(pq) = 0 to machine
precision for all mixed composites tested (6, 10, …, 2310). **B is the von Mangoldt
function Λ.** The recursion is precisely the Dirichlet-convolution identity
log = 1 ∗ Λ, i.e. Λ = μ ∗ log. Mixed composites do not survive.

### Experiment 3 — Prime-loop obstruction (fully reproduced)
- **No finite low-energy limit.** Modes below E for loops L_p = log p, p ≤ P:

  | P | E≤5 | E≤10 | E≤14 |
  |---|-----|------|------|
  | 10³ | 684 | 1,429 | 2,052 |
  | 10⁶ | 748,132 | 1,546,343 | 2,185,542 |
  | 2·10⁶ | 1,522,358 | 3,103,050 | 4,380,632 |

  Growth is ~(E/2π)·θ(P) ~ (E/2π)·P: linear divergence. A literal one-loop-per-prime
  spectrum has no low-energy limit — every prime past e^{2π/E} contributes.
- **Kirchhoff coupling creates forbidden orbits.** For a 3-bond star (lengths log 2,
  log 3, log 5; Neumann ends, Kirchhoff vertex) I computed 32,479 eigenvalues to
  k = 30,000 (Weyl count expected 32,479.04). The length spectrum (windowed Fourier
  transform of the level density) shows unmistakable peaks at 2·log 10, 2·log 12,
  2·log 15, 2·log 18, 2·log 24, 2·log 36, 2·log 50, 2·log 54 — mixed composites with
  positions matched to 4 decimal places. **The arithmetic trace has Λ = 0 exactly at
  these lengths (Exp 2), so ordinary prime-channel quantum graphs are structurally
  incompatible with the Riemann explicit formula.** Any vertex coupling generic enough
  to mix channels generates composite-length orbits that the arithmetic side forbids.

### Experiment 4 — Finite-field control (fully reproduced)
E1: y² = x³ + x + 1 / F₅. Direct counts (own field-arithmetic implementation, irreducible
moduli found by search): N₁…N₆ = 9, 27, 108, 675, 3069, 15552. Frobenius trace a = −3,
char. poly T² + 3T + 5, |α| = √5 (Hasse/"RH" verified). The 2-term recurrence predicts
all direct counts exactly. Möbius inversion gives primitive closed points
a_d = 9, 9, 33, 162, 612, 2571 (all non-negative integers — a real consistency check).
Zeta computed three independent ways (exp of count series, product over primitive
orbits, Frobenius determinant formula) — identical power series.
**Ablation:** replacing N_n by the smooth bulk 5ⁿ + 1 collapses the numerator to 1: the
nontrivial spectrum vanishes, and the "primitive counts" stay integral but lose all
curve information. **Second curve** y² = x³ + 2 / F₅: a = 0 (supersingular), counts
6, 36, 126, 576, 3126, 15876. Same base-field clock, different spectrum ⇒ **the
logarithmic clock (powers of q = 5) does not determine the spectrum; the geometry
(cohomology of the specific curve) does.**

### Experiment 5 — Finite additive/Fourier dilation model (fully reproduced)
M = 255255, T(x) = 2x. Fix(T^n) = gcd(2ⁿ − 1, M), verified by direct enumeration; CRT
local factorization Fix = ∏_q q^{[ord_q(2) | n]} verified for n ≤ 60 with orders
{3:2, 5:4, 7:3, 11:10, 13:12, 17:8}. Fourier characters: U χ_a = χ_{2a};
Tr(Uⁿ) = #fixed characters = Fix(Tⁿ), verified. Full cycle decomposition
(1,1),(2,1),(3,2),(4,3),(6,2),(8,30),(10,3),(12,111),(20,6),(24,900),(30,6),(40,60),
(60,222),(120,1800) satisfies the Lefschetz relation Fix(Tⁿ) = Σ_{d|n} d·c_d for all
n ≤ 60. Möbius inversion of log Fix isolates **exactly** log q at n = ord_q(2)
(errors ≤ 4·10⁻¹⁶): perfect local separation. No information about Riemann zeros is
produced (and none was claimed by the computation itself).

### Experiment 6 — Global dilation sum (reproduced)
- **Mellin action:** for Zf(x) = Σ f(nx), the multiplier is ζ(s): verified numerically to
  30+ digits for f = e^{−x} at s = 2, 3, 2+i (Mellin(Zf) = ζ(s)Γ(s)).
- **Blind scan:** minima of |η(½ + iE)|, E ∈ (0.5, 60), grid 0.01, refined by ternary
  search — 13 deep minima (|η| < 10⁻¹⁶) at E = 14.134725…, 21.022040…, …, 59.347044…,
  plus 6 shallow non-zero dips. Compared *afterward* against mpmath's independently
  computed zeros: all 13 match to ~10⁻¹⁷; counts in (0,60) agree exactly.
- **Caveat stated up front:** η(s) = (1 − 2^{1−s})ζ(s) *identically*, and the extra
  factor has zeros only on Re s = 1. This scan is a test of numerical hygiene, **not
  independent evidence about zeta zeros** — the multiplier is analytically equivalent
  to ζ.

### Experiment 7 — Critical-line deformation control (reproduced; conclusion is negative)
F_ε(s) = η(s) + ε·η(s + δ), δ = 0.2 (the exact deformation a_n = (−1)^{n−1}(1 + εn^{−δ})).
Tracking the first dark mode with unconstrained 2-D root solving:

| ε | Re s − ½ | Im s |
|---|----------|------|
| −0.1 | +0.018663 | 14.134668 |
| −0.01 | +0.0017206 | 14.134720 |
| 0 | 0 | 14.1347251417 |
| +0.01 | −0.0016913 | 14.134730 |
| +0.1 | −0.015710 | 14.134769 |

**The root leaves the critical line immediately and linearly.** First-order sensitivity
ds/dε = −η(ρ+δ)/η′(ρ) = −0.17058657 + 0.00050009 i, confirmed by finite differences to
7 digits; stable at 50-digit precision and under truncation depth N = 2000 → 20000; the
effect is larger at δ = 0.5 (slope −0.34). **Generic nearby dilation systems destroy
critical-line behavior**; the critical line is not an attractor of this family.

### Experiment 8 — Finite Weil positivity (implemented from primary formulas; reproduced in structure)
Implemented the Weil explicit formula from scratch (Iwaniec–Kowalski normalization),
with the archimedean distribution converted to a u-space integral via
ψ(z) = −γ + ∫₀¹(1−t^{z−1})/(1−t)dt. **Validation:** for Gaussian test functions the
geometric side (pole − prime + archimedean, three O(1) terms) equals the independently
computed sum over Riemann zeros to ~4·10⁻¹⁶ absolute — a 13–16 digit cancellation that
pins every sign and constant. The arithmetic coefficients were generated from the
Experiment-2 recursion (no prime list) and agree with Λ(n) to 10⁻³⁰.

Q_{jk} = W(sym(f_j ⋆ f_k)) for shifted-Legendre basis N = 8 on [0, log 13]
(exact symbolic autocorrelation polynomials, dps = 40):

eigenvalues = {9.6497·10⁻⁸, 1.5135·10⁻⁷, 3.87·10⁻⁵, 1.14·10⁻³, 1.65·10⁻², 3.23·10⁻²,
0.307, 0.392} — **all positive**, condition number 4.06·10⁶, with a two-dimensional
near-null subspace. Stable to 9 digits between dps 25 and dps 40 (not a floating-point
artifact). At N = 12 the near-null space deepens (λ_min = 7.5·10⁻¹¹, four eigenvalues
below 10⁻⁶); at c = 20, λ_min = 4.1·10⁻⁸. This matches the known picture
(Connes–Consani "zeta cycles"): restricted-support Weil forms are positive but
asymptotically degenerate, the near-null vectors being the interesting objects.

### Experiment 9 — Same-deformation bridge (reproduced; the bridge fails)
Deforming w_n → w_n(1 + εn^{−δ}) in Q_arith only (δ = 0.2, holding pole and archimedean
fixed):

| ε | λ_min (Weil) | Re s − ½ (dark mode) |
|---|---|---|
| −0.05 | −0.0467 | +0.00891 |
| −0.01 | −0.00774 | +0.00172 |
| −10⁻⁶ | −3.3·10⁻⁷ | +1.7·10⁻⁷ (linear) |
| −10⁻⁷ | +5.4·10⁻⁸ | … |
| 0 | +9.6·10⁻⁸ | 0 |
| +10⁻⁷ | +7.7·10⁻⁸ | … |
| +10⁻⁶ | −6.3·10⁻⁷ | −1.7·10⁻⁷ |
| +0.01 | −0.0337 | −0.00169 |
| +0.05 | −0.2226 | −0.00818 |

Key facts established:
1. **Finite positivity does not survive**: it breaks at |ε| ≈ 2–3·10⁻⁷ for **both signs**
   of ε. The reason is fully diagnosed: the projection of dQ/dε onto the 2-dim near-null
   subspace is the indefinite block diag(+0.4216, −0.7401), so ε of either sign drives
   one branch negative at ε* ≈ λ_min/|block eigenvalue| ~ 10⁻⁷. This is textbook
   degenerate perturbation theory, nothing arithmetic.
2. **No stable quantitative bridge**: dark-mode drift is smooth and O(ε) with slope
   −0.171 (δ = 0.2); Weil λ_min response is a non-smooth min-of-branches collapse with
   characteristic scale 10⁻⁷. The slope "ratio" between the two sides is 15.99 at
   δ = 0.1 and 2.64 at δ = 0.5 — no persistent relationship under change of δ (nor of
   c or N: slopes −3.16 at c = 20, −1.76 at N = 12).
3. **Controls:** uniform deformation (1+ε), archimedean-only scaling, pole-only scaling,
   and 4 random coefficient-space directions of matched norm all *also* destroy
   positivity at the same generic scale. Nothing is special about the scale-dependent
   arithmetic direction.
4. **Synthetic control (the decisive one):** a random PSD matrix with the *same
   eigenvalue profile* perturbed by a random symmetric matrix of the *same Frobenius
   norm* gives λ_min(±0.01) ≈ −0.020/−0.022 and λ_min(±0.05) ≈ −0.128/−0.137 — the same
   order and the same both-signs collapse as the real Weil form (−0.0077/−0.0337 and
   −0.047/−0.223). **The observed sensitivity carries no information beyond the generic
   behavior of an ill-conditioned near-singular PSD matrix.**

## B. Failures / disagreements

- No numerical output of the previous run exists, so no line-item comparison is possible.
- Two *conclusions* implied by the handoff's framing fail replication outright:
  1. Any suggestion that the deformed dark mode "remains on the critical line" is
     **false** — it departs linearly (Exp 7).
  2. Any suggestion that Weil positivity and the dark modes respond to the "same"
     deformation in a correlated way is **unsupported** — the responses have different
     analytic character, scales differing by 5 orders of magnitude, and no δ-stable
     relationship (Exp 9). Note also that the two deformations are not actually the same
     object: on the dilation side ε multiplies the *Dirichlet coefficients* of η
     (η → η + εη(·+δ)); on the Weil side ε multiplies the *log-derivative coefficients*
     Λ(n) (−ζ′/ζ → −ζ′/ζ − ε·(−ζ′/ζ)(·+δ)-type term). These are different deformations
     of different functions that merely share a bookkeeping formula.

## C. Known mathematics versus experimental contribution

Everything in Experiments 1, 2, 4, 5, and 6 is classical, and the numerics confirm known
identities rather than discovering anything:

| "Result" | Status |
|---|---|
| Indecomposables of {T_n} = primes | Definition of primality (unique factorization) |
| Fix(T_nʳ) = nʳ−1, h_n = log n | Standard expanding-map dynamics |
| [D,U_n] = (log n)U_n | Algebraic identity log(nk) − log k = log n |
| Tr e^{−βD} = ζ(β) | Definition of ζ as a Dirichlet series |
| B = Λ, support = prime powers | Möbius inversion: Λ = μ∗log (standard) |
| E.C. point counts ↔ Frobenius, zeta rationality, |α|=√q | Hasse's theorem (proved, 1930s); Weil conjectures |
| Fix/trace/Lefschetz identities on Z/M | Elementary group theory + CRT |
| Mellin multiplier ζ(s); η zero scan | Classical; η ≡ (1−2^{1−s})ζ, so the scan is circular by construction |
| Weil form positivity for restricted support (small c) | Known: Yoshida, Bombieri; recent quantitative structure by Connes–Consani |

Genuine *experimental contributions* of this replication (none of them evidence for a
"machine", but real, checkable observations):
- The quantitative demonstration that Kirchhoff-coupled prime loops generate
  composite-length orbits with O(1) amplitudes (Exp 3) — a concrete no-go for naive
  quantum-graph realizations of the explicit formula, consistent with the known
  requirement that any Hilbert–Pólya dynamics must have orbit lengths log(p^k) with
  amplitudes that do *not* mix channels (the p-adic/adelic structure does exactly this).
- The measured first-order off-line drift coefficient (−0.1706 at δ = 0.2) of the first
  zero under coefficient deformation (Exp 7) — a clean quantification of the
  non-genericity of the critical line within this deformation family.
- The complete diagnosis of the Weil-form deformation response as degenerate
  perturbation theory on an indefinite near-null block (Exp 9/9b).

## D. Circularity / bias audit

Where the sequence was circular or self-confirming:
1. **Exp 1D/6:** the "thermal trace" and Mellin multiplier *are* ζ by definition of the
   construction. Finding ζ there is input, not output.
2. **Exp 6 blind scan:** scanning η on the critical line finds ζ zeros because η is
   analytically ζ times an explicit nonvanishing-on-the-line factor. The "blindness" of
   the scan is procedural, not mathematical.
3. **Exp 2 feeding Exp 8:** deriving Λ from the recursion instead of a prime list is
   cosmetically non-circular but mathematically identical (μ∗log). Fine as a hygiene
   check; adds no independence.
4. **Exp 9 framing:** calling the two deformations "the same" presupposes the bridge
   the experiment was meant to test (see B.2).
5. **Not circular:** Exps 3, 4, 5, 7 and the Exp 9 controls are honest tests, and
   notably three of them (3, 7, 9) returned *negative/obstruction* results.

## E. Assessment of the candidate architecture

The circle-dilation semigroup {T_n} is a faithful but *representation-theoretic* shell:
its indecomposables, entropies, commutators and traces re-encode unique factorization
and the Dirichlet series of ζ without producing any new operator whose spectrum is the
zeros. The finite-field control (Exp 4) makes explicit what is missing: there, one space
(the curve over F̄_q) carries *both* a Frobenius dynamics whose orbits are the closed
points *and* a finite-dimensional cohomology on which the same Frobenius acts with
eigenvalues of modulus √q — with an intersection-theoretic positivity
(Castelnuovo–Severi / Hodge index) forcing "RH". In every construction examined here,
the arithmetic side is inserted (as Λ, as the Euler product, as η) rather than emerging
from a dynamics, and no analogue of the cohomological finiteness + positivity pair
appears. The prime-loop no-go (Exp 3) sharpens this: a genuine realization cannot be an
ordinary coupled 1-D wave system, because coupling inevitably creates composite-length
periodic orbits, while the explicit formula demands single-prime-power support with
amplitudes log p·p^{−k/2}. Whatever object realizes the zeros spectrally must suppress
inter-prime orbit mixing exactly — which is what the adelic/idele-class constructions
(Connes, Meyer) achieve by fiat of their function spaces, at the cost of losing the
positivity that would prove RH.

## F. Recommended next experiment

The one live, falsifiable target that survives this audit is the *structure of the
near-null subspace* of the restricted Weil form (not its deformation sensitivity):

**Experiment:** For c ∈ {5, 7, 11, 13, 17, 20} and N large enough that λ_min(c, N) has
converged (N ≈ 2·log c·γ_max/π + margin), compute at dps ≥ 60: (i) the dimension and
decay rate of the near-null space as a function of c; (ii) the Fourier profiles
|v̂₀(γ)|² of the near-null eigenvectors against the first zeros; (iii) whether λ_min(c)
follows the Connes–Consani zeta-cycle prediction (degeneracy deepening when 2π·k/log c
crosses a zero ordinate). **Falsifiable outcome:** if the near-null vectors' spectral
concentration on the actual zero ordinates fails to sharpen as prescribed, the
zeta-cycle picture is wrong; if it sharpens, this replicates (not extends) the published
mechanism and quantifies its rate — either way it produces information, unlike further
deformation studies, which this audit shows measure only generic matrix conditioning.

## G. Overall verdict

**Useful constraints only.** Reasons: every positive numerical observation reproduced
here is a restatement of established mathematics (unique factorization, Möbius
inversion, Hasse–Weil, CRT/Lefschetz, Mellin/η identities, known restricted-support
Weil positivity). The genuinely informative outputs of the program are its three
*negative* results, which are solid and worth keeping: (1) literal prime-loop quantum
graphs are structurally incompatible with the arithmetic trace; (2) the critical line is
not stable under generic dilation-coefficient deformations — it is not an attractor,
so "dynamical" explanations must explain an exact symmetry, not a stability phenomenon;
(3) the finite Weil form's deformation sensitivity is generic near-singular-matrix
behavior and cannot be used as an RH-adjacent signal. There is no evidence here of a
new "machine casting both shadows," and the deformation-bridge direction should be
retired. The near-null structure of the Weil form remains the only component with real
mathematical leverage, and it is already the subject of an active professional program
(Connes–Consani–Moscovici; Suzuki), against which any further work should be benchmarked.

---

## Answers to the specific questions

**1. Which results survive?** All structural identities (Exps 1, 2, 4, 5, 6-Mellin)
reproduce exactly. The Exp 8 positivity (λ_min ≈ 9.65·10⁻⁸ > 0 at c=13, N=8) survives
at two precisions and two truncations. What does *not* survive: on-line stability of the
deformed dark mode (Exp 7) and any arithmetic-specific content in the Weil-form
deformation response (Exp 9).

**2. Which "discoveries" are established identities?** Exp 1 (all parts), Exp 2
(Λ = μ∗log), Exp 4 (Hasse/Weil, proven theorems), Exp 5 (CRT + Burnside/Lefschetz
bookkeeping), Exp 6 (Mellin multiplier and η-scan; circular), the positivity of Exp 8
in this support range (known: Yoshida 1992, Bombieri, Connes–Consani).

**3. Did we make a wrong turn?** Yes, at two points. First, Exps 1→2→6 form a closed
loop: they re-derive the Euler-product/Möbius layer three times in different clothes;
nothing after Exp 2 in that thread could have produced new information. Second and more
serious: Exp 9's premise ("same deformation") is a category error — the dilation-side
deformation perturbs Dirichlet coefficients of η, the Weil-side deformation perturbs
explicit-formula coefficients Λ(n); they are different objects, so a correlation would
not have meant what the design assumed, and in the event there is none.

**4. Is the finite Weil positivity result genuinely informative?** The *positivity
itself* at small c is real mathematics (and known unconditionally in this support
range). The *deformation sensitivity* is **not informative**: it is reproduced
quantitatively by a synthetic random near-singular PSD matrix with matched spectrum and
perturbation norm, breaks for both signs of ε via an indefinite near-null block, at a
threshold (≈2·10⁻⁷) set purely by λ_min/‖perturbation‖ — generic degenerate
perturbation theory.

**5. Does the dark-mode/Weil-positivity connection survive stronger controls?** No.
Different analytic character (smooth linear drift vs. branch collapse), scales apart by
~10⁵, slope ratios unstable in δ (16.0 → 2.6 between δ = 0.1 and 0.5) and in c, N; all
control deformations (uniform, archimedean, pole, random) behave the same as the
"arithmetic" one. Both phenomena relate to RH mathematically; the experiments provide
no additional link.

**6. Strongest nontrivial conclusion supported by the experiments?** Conservatively:
*within the tested families, the critical-line phenomenon behaves as an exact rigid
identity, not as a stable/attracting property* — generic coefficient deformations
destroy it at first order on the zero side and at infinitesimal threshold on the
positivity side, while the finite-field control shows what a mechanism that genuinely
enforces it (cohomological positivity) looks like. Additionally, the prime-loop no-go:
1-D wave channels coupled by any standard vertex cannot reproduce the arithmetic trace.

**7. What remains genuinely unknown?** The specific missing structure, made concrete by
Exp 4's control: a finite-rank-like "cohomology" H attached to Spec ℤ carrying an
endomorphism (Frobenius-analogue = scaling flow, per Deninger/Connes) such that
(a) a Lefschetz fixed-point formula over the *closed points* (primes, orbit length
log p) reproduces the explicit formula with the exact amplitudes p^{−k/2}·log p and *no
mixed-composite orbits*; and (b) an intrinsic positivity of Hodge-index type on H forces
the eigenvalue symmetry. Meyer's construction supplies (a) without positivity on nuclear
Fréchet spaces; Hilbert-space versions supply positivity only for on-line zeros. The
unknown is a single natural space where both hold simultaneously — specifically, what
plays the role of the *intersection pairing on a surface* (the ingredient that proves
positivity in the function-field case and has no known analogue for Spec ℤ; this is
exactly the "component with no counterpart" the handoff asked to identify).

**8. Recommendation.**
- **Highest priority:** the near-null-subspace experiment in §F (zeta-cycle structure of
  the restricted Weil form) — it is falsifiable, benchmarked against a live professional
  program, and the only place where these finite matrices contain non-generic
  information. Equally important: recover or regenerate the original sealed outputs, since
  the previous run's claims are currently unverifiable.
- **Worth testing:** formalize the Exp 3 no-go — determine precisely which vertex
  scattering matrices (if any, beyond the trivial decoupled one) kill all
  mixed-composite orbit amplitudes; a short proof that none exist for finite quantum
  graphs would be a publishable obstruction result and would explain *why* adelic
  function spaces are forced.
- **Probably stop pursuing:** all deformation-bridge work (Exps 7/9 style), the η dark-
  mode scans, and further circle-dilation/thermal-trace numerology. These measure known
  identities or generic matrix conditioning; this audit indicates further numerical
  effort there will not produce new information.

## Literature status (verified against current sources, Aug 2026)

| Construction | Status |
|---|---|
| Hilbert–Pólya | Heuristic program; no operator known. Numerical support (GUE statistics: Montgomery, Odlyzko) is evidence, not theorem. |
| Weil positivity ⇔ RH | **Proven theorem** (Weil 1952; Bombieri's account). Restricted-support positivity proven unconditionally in small ranges (Yoshida 1992; Bombieri 2001–03; Connes–Consani 2021/23). |
| Frobenius cohomology over finite fields | **Proven** (Weil for curves; Deligne in general). The model for everything else. |
| Deninger program | Conjectural framework (infinite-dim. cohomology with flow); no construction of the required cohomology to date; recent progress is on analogies (dynamical systems, foliations), not the arithmetic case. |
| Bost–Connes | **Proven theorem** (1995): QSM system with spontaneous symmetry breaking, partition function ζ(β); class field theory of ℚ. Does not localize zeros. |
| Connes adele-class trace formula | Trace formula proven in specific functional settings; **RH equivalent to a positivity** that remains open. Spectral realization on Hilbert space captures only on-line zeros (conditional character). |
| Meyer cokernel realization | **Proven theorem** (Duke Math. J. 127, 2005): all zeros realized spectrally on nuclear Fréchet/bornological spaces; unconditional precisely because Hilbert positivity is abandoned; **does not imply RH** — the missing piece is positivity of the trace pairing. |
| Connes–Consani–Moscovici zeta spectral triples | Active: "Zeta zeros and prolate wave operators" (Ann. Funct. Anal. 15, 2024, peer-reviewed); "Zeta Spectral Triples" (arXiv 2511.22755, Nov 2025, **preprint, not yet peer-reviewed**): striking numerics (first 50 zeros from primes ≤ 13, errors down to 10⁻⁵⁵) with on-line-by-construction approximants via a Carathéodory–Fejér/Toeplitz argument; a *strategy* toward RH, not a proof. |
| Suzuki screw-function/canonical systems | Peer-reviewed core (J. London Math. Soc. 2023; JFA 2020); "Weil's quadratic form via the screw function" (arXiv 2606.09096, 2026, **preprint**) unifies Yoshida/Bombieri/CC/CCM finite forms; self-adjoint-limit statement is a **conjecture**. |

Primary sources: [arXiv:2511.22755](https://arxiv.org/abs/2511.22755),
[arXiv:2310.18423](https://arxiv.org/abs/2310.18423),
[PNAS 2123174119](https://www.pnas.org/doi/10.1073/pnas.2123174119),
[arXiv:2106.01715](https://arxiv.org/abs/2106.01715),
[arXiv:math/0311468 (Meyer)](https://arxiv.org/abs/math/0311468),
[arXiv:2606.09096 (Suzuki)](https://arxiv.org/abs/2606.09096),
[arXiv:2301.00421 (Suzuki)](https://arxiv.org/abs/2301.00421).
