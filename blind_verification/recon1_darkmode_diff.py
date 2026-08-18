"""Reconciliation step 1: are ChatGPT's dark-mode outputs mathematically equivalent to mine?"""
import mpmath as mp
mp.mp.dps = 30

# ChatGPT roots (float64) for F_eps(s) = eta(s) + eps*eta(s+0.2), per their n1_relative_weight = 1+eps
gpt = {
    "-0.1": ("0.5186630640561819", "14.134668364297438"),
    "-0.05": ("0.5089122736569214", "14.134698515011697"),
    "-0.01": ("0.5017206484756488", "14.134720078092279"),
    "0.01": ("0.49830866354361664", "14.13473008090107"),
    "0.05": ("0.4918218554736896", "14.13474865314848"),
    "0.1": ("0.4842901890033272", "14.134769415884808"),
}
delta = mp.mpf("0.2")
eta = mp.altzeta
print("eps | my root (dps30) | |diff vs ChatGPT| | |F_eps(their root)|")
for e, (re_s, im_s) in gpt.items():
    eps = mp.mpf(e)
    seed = mp.mpc(mp.mpf(re_s), mp.mpf(im_s))
    mine = mp.findroot(lambda z: eta(z) + eps * eta(z + delta), mp.mpc("0.5", "14.1347"), solver="muller")
    resid = abs(eta(seed) + eps * eta(seed + delta))
    print("%6s  %s  %s  %s" % (e, mp.nstr(mine, 17), mp.nstr(abs(mine - seed), 3), mp.nstr(resid, 3)))

# their blind dark modes: consistent with truncated-eta extraction?
print("\nblind dark modes: their E vs eta residual at that E (exact altzeta)")
for E, res in [("14.134725137046878", "8.83754851697684e-09"),
               ("21.02203964075157", "2.3122660113756904e-09"),
               ("25.010857599979584", "1.5062920310201096e-08"),
               ("30.424876435295538", "8.077733126971262e-07"),
               ("32.93506324723639", "2.458951106754339e-06"),
               ("37.58619348681452", "3.1296889111642905e-05")]:
    v = abs(eta(mp.mpc("0.5", E)))
    print("  E=%s  |eta| = %s (their operator residual %s)" % (E[:12], mp.nstr(v, 3), res))
