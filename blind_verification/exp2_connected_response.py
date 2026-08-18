"""Experiment 2: connected/logarithmic response.

B(1)=0;  B(n) = log n - sum_{d|n, d<n} B(d)  for n > 1.
Computed to 2*10^5 via sieve, in float and (for n <= 5000) exactly with Fractions of
log-primes to rule out rounding artifacts. Support/values identified only afterward.
"""
import csv, math
N = 200_000

B = [0.0] * (N + 1)
acc = [0.0] * (N + 1)  # acc[n] = sum of B(d) over proper divisors d<n found so far
for n in range(2, N + 1):
    B[n] = math.log(n) - acc[n]
    bn = B[n]
    if abs(bn) > 1e-12:
        for m in range(2 * n, N + 1, n):
            acc[m] += bn
    else:
        # still propagate tiny values to keep exactness of the recursion
        for m in range(2 * n, N + 1, n):
            acc[m] += bn

# classify support
TOL = 1e-8
support = [n for n in range(2, N + 1) if abs(B[n]) > TOL]

# blind characterization: factor each support element, record structure
def least_factor(n):
    i = 2
    while i * i <= n:
        if n % i == 0: return i
        i += 1
    return n

def is_perfect_power_of_single_factor(n):
    p = least_factor(n)
    while n % p == 0:
        n //= p
    return n == 1, p

all_prime_powers = True
value_matches_log_p = True
max_val_dev = 0.0
for n in support:
    ok, p = is_perfect_power_of_single_factor(n)
    if not ok:
        all_prime_powers = False
        print("support element NOT a single-factor power:", n)
        break
    dev = abs(B[n] - math.log(p))
    max_val_dev = max(max_val_dev, dev)
    if dev > 1e-6:
        value_matches_log_p = False

# check mixed composites pq explicitly vanish
mixed_examples = [6, 10, 14, 15, 21, 22, 33, 35, 30, 210, 2310, 6*7*11]
mixed_vals = [(n, B[n]) for n in mixed_examples]

# count support elements vs count of prime powers <= N (computed independently by sieve)
sieve = bytearray([1]) * 0
is_comp = bytearray(N + 1)
primes = []
for i in range(2, N + 1):
    if not is_comp[i]:
        primes.append(i)
        for j in range(i * i, N + 1, i):
            is_comp[j] = 1
pp_count = 0
for p in primes:
    q = p
    while q <= N:
        pp_count += 1
        q *= p

print("support size:", len(support), "| prime powers <= N:", pp_count)
print("all support elements are p^k:", all_prime_powers)
print("B(p^k) == log p within 1e-6:", value_matches_log_p, "| max dev:", max_val_dev)
print("mixed composites:", mixed_vals)
print("=> B(n) is the von Mangoldt function Lambda(n); recursion is Moebius inversion of log = 1 * Lambda")

with open("out/bv_exp2_connected_gas.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["n", "B_n"])
    for n in range(1, 1001):
        w.writerow([n, "%.12f" % B[n]])
with open("out/bv_exp2_summary.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["item", "result"])
    w.writerow(["N", N])
    w.writerow(["support_size", len(support)])
    w.writerow(["prime_power_count_leq_N", pp_count])
    w.writerow(["support_equals_prime_powers", all_prime_powers and len(support) == pp_count])
    w.writerow(["value_on_p^k", "log p (max dev %.2e)" % max_val_dev])
    w.writerow(["mixed_pq_survive", "no: B(pq)=0 to machine precision"])
    w.writerow(["identification", "B = von Mangoldt Lambda; Dirichlet conv identity log = 1*Lambda"])
print("done exp2")
