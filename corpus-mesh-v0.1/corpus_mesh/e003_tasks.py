"""Task battery for CM-E003 (real-model long-horizon reliability).

Design goals:
- every operation is deterministic integer math, objectively gradable by the
  harness without any model involvement;
- per-step difficulty is stationary (state stays bounded), so an exponential
  reliability-decay model R(h) ~ exp(-lambda*h) is well-posed;
- the operation mix is calibrated against the real model so the per-step error
  rate is measurable (neither ~0% nor ~100%), otherwise the experiment has no
  statistical sensitivity;
- prompts are built ONLY from the task definition and the evolving state. The
  expected value never appears in any prompt.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence, Tuple


def _reverse_digits(n: int) -> int:
    return int(str(abs(n))[::-1])


def _digit_sum(n: int) -> int:
    return sum(int(c) for c in str(abs(n)))


@dataclass(frozen=True)
class OpInstance:
    op_name: str
    params: Dict[str, int]
    description: str

    def apply(self, current: int) -> int:
        return OPS[self.op_name].apply(current, self.params)


@dataclass(frozen=True)
class OpType:
    name: str
    gen_params: Callable[[random.Random], Dict[str, int]]
    apply: Callable[[int, Dict[str, int]], int]
    describe: Callable[[Dict[str, int]], str]

    def instance(self, rng: random.Random) -> OpInstance:
        params = self.gen_params(rng)
        return OpInstance(self.name, params, self.describe(params))


OPS: Dict[str, OpType] = {}


def _register(op: OpType) -> None:
    OPS[op.name] = op


_register(OpType(
    name="mul3_mod",
    gen_params=lambda rng: {"k": rng.randint(101, 997), "m": 9973},
    apply=lambda cur, p: (cur * p["k"]) % p["m"],
    describe=lambda p: (
        f"Multiply the current value by {p['k']}, then take the result modulo {p['m']}."
    ),
))

_register(OpType(
    name="mul2_mod",
    gen_params=lambda rng: {"k": rng.randint(11, 99), "m": 9973},
    apply=lambda cur, p: (cur * p["k"]) % p["m"],
    describe=lambda p: (
        f"Multiply the current value by {p['k']}, then take the result modulo {p['m']}."
    ),
))

_register(OpType(
    name="add_mul",
    gen_params=lambda rng: {"a": rng.randint(100, 999), "b": rng.randint(3, 9)},
    apply=lambda cur, p: ((cur + p["a"]) * p["b"]) % 10000,
    describe=lambda p: (
        f"Add {p['a']} to the current value, multiply that sum by {p['b']}, "
        f"then take the result modulo 10000."
    ),
))

_register(OpType(
    name="rev_add",
    gen_params=lambda rng: {"k": rng.randint(100, 999)},
    apply=lambda cur, p: _reverse_digits(cur) + p["k"],
    describe=lambda p: (
        f"Reverse the decimal digits of the current value (for example 1230 "
        f"becomes 0321 which is 321), then add {p['k']}."
    ),
))

_register(OpType(
    name="xor_add",
    gen_params=lambda rng: {"k": rng.randint(1000, 9999), "j": rng.randint(10, 99)},
    apply=lambda cur, p: (cur ^ p["k"]) + p["j"],
    describe=lambda p: (
        f"Compute the bitwise XOR of the current value and {p['k']} "
        f"(both as binary integers), then add {p['j']}."
    ),
))

_register(OpType(
    name="digit_mul",
    gen_params=lambda rng: {"k": rng.randint(10, 99)},
    apply=lambda cur, p: cur + _digit_sum(cur) * p["k"],
    describe=lambda p: (
        f"Compute the sum of the decimal digits of the current value, multiply "
        f"that digit sum by {p['k']}, and add the product to the current value."
    ),
))


@dataclass(frozen=True)
class Chain:
    """A long-horizon task: fold `ops` over `start`.

    `expected_final` is harness-side ground truth. It must never be passed to
    any architecture or included in any prompt.
    """

    chain_id: str
    start: int
    ops: Tuple[OpInstance, ...]

    @property
    def horizon(self) -> int:
        return len(self.ops)

    @property
    def expected_final(self) -> int:
        cur = self.start
        for op in self.ops:
            cur = op.apply(cur)
        return cur

    def expected_states(self) -> List[int]:
        """All intermediate ground-truth states (harness-side scoring only)."""
        states = []
        cur = self.start
        for op in self.ops:
            cur = op.apply(cur)
            states.append(cur)
        return states


def make_chain(horizon: int, seed: int, op_mix: Sequence[str]) -> Chain:
    if not op_mix:
        raise ValueError("op_mix must name at least one registered op")
    for name in op_mix:
        if name not in OPS:
            raise ValueError(f"unknown op: {name}")
    rng = random.Random(seed)
    start = rng.randint(1000, 9999)
    ops = tuple(OPS[rng.choice(list(op_mix))].instance(rng) for _ in range(horizon))
    return Chain(chain_id=f"chain-{seed}", start=start, ops=ops)


def step_prompt(current: int, op: OpInstance) -> str:
    """The task statement shown to worker/verifier agents. Contains no truth."""
    return (
        f"Current value: {current}.\n"
        f"Operation: {op.description}\n"
        'Compute the new value. Show your working briefly, then give the final '
        'answer as a JSON object of the exact form {"value": <integer>} on the '
        "last line of your reply."
    )
