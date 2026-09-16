"""Disposable exact laboratory for tiny NAND-DAG range avoidance."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, combinations_with_replacement, product
from itertools import permutations
from typing import Callable, Iterable


GateList = tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class Witness:
    gates: GateList
    output_wire: int


@dataclass(frozen=True)
class Enumeration:
    state_counts: list[int]
    new_function_counts: list[int]
    min_size: dict[int, int]
    witnesses: dict[int, Witness]


@dataclass(frozen=True)
class ParitySubcubeCertificate:
    free_variables: tuple[int, ...]
    fixed_assignments: tuple[tuple[int, int], ...]
    complemented: bool


def input_masks(n: int) -> tuple[int, ...]:
    rows = 1 << n
    return tuple(
        sum(((row >> variable) & 1) << row for row in range(rows))
        for variable in range(n)
    )


def nand(left: int, right: int, n: int) -> int:
    return (~(left & right)) & ((1 << (1 << n)) - 1)


def evaluate_witness(n: int, witness: Witness) -> int:
    wires = list(input_masks(n))
    for left, right in witness.gates:
        wires.append(nand(wires[left], wires[right], n))
    return wires[witness.output_wire]


def _wire_map(n: int, gates: GateList) -> dict[int, int]:
    wires = list(input_masks(n))
    positions = {mask: index for index, mask in enumerate(wires)}
    for left, right in gates:
        output = nand(wires[left], wires[right], n)
        wires.append(output)
        positions.setdefault(output, len(wires) - 1)
    return positions


def enumerate_nand(n: int, max_gates: int) -> Enumeration:
    inputs = input_masks(n)
    states: dict[frozenset[int], GateList] = {frozenset(inputs): ()}
    minima = {mask: 0 for mask in inputs}
    witnesses = {mask: Witness((), index) for index, mask in enumerate(inputs)}
    state_counts = [1]
    new_counts = [len(inputs)]

    for size in range(1, max_gates + 1):
        next_states: dict[frozenset[int], GateList] = {}
        newly_seen: set[int] = set()
        for available, gates in states.items():
            positions = _wire_map(n, gates)
            ordered = sorted(available)
            for left_mask, right_mask in combinations_with_replacement(ordered, 2):
                output = nand(left_mask, right_mask, n)
                if output in available:
                    continue
                extended_set = available | {output}
                if extended_set in next_states:
                    continue
                extended_gates = gates + (
                    (positions[left_mask], positions[right_mask]),
                )
                next_states[extended_set] = extended_gates
                if output not in minima:
                    minima[output] = size
                    witnesses[output] = Witness(extended_gates, n + len(extended_gates) - 1)
                    newly_seen.add(output)
        states = next_states
        state_counts.append(len(states))
        new_counts.append(len(newly_seen))

    return Enumeration(state_counts, new_counts, minima, witnesses)


def singleton_relaxation_cost(
    target: int, n: int, singleton_costs: dict[int, int]
) -> int | None:
    best = None
    masks = sorted(singleton_costs)
    for left, right in combinations_with_replacement(masks, 2):
        if nand(left, right, n) != target:
            continue
        candidate = 1 + max(singleton_costs[left], singleton_costs[right])
        best = candidate if best is None else min(best, candidate)
    return best


def structural_signature(mask: int, n: int) -> tuple[int, ...]:
    """A deliberately strong bundle of standard scalar Boolean metrics."""
    width = 1 << n
    truth = [(mask >> row) & 1 for row in range(width)]
    anf = truth[:]
    for variable in range(n):
        for row in range(width):
            if row & (1 << variable):
                anf[row] ^= anf[row ^ (1 << variable)]
    walsh = [
        sum(
            (-1 if truth[row] else 1)
            * (-1 if (row & frequency).bit_count() & 1 else 1)
            for row in range(width)
        )
        for frequency in range(width)
    ]
    sensitivities = [
        sum(truth[row] != truth[row ^ (1 << variable)] for variable in range(n))
        for row in range(width)
    ]
    certificates = [
        min(
            subset.bit_count()
            for subset in range(width)
            if all(
                truth[other] == truth[row]
                for other in range(width)
                if (row & subset) == (other & subset)
            )
        )
        for row in range(width)
    ]
    automorphisms = sum(
        all(
            truth[row]
            == truth[
                sum(((row >> i) & 1) << permutation[i] for i in range(n))
            ]
            for row in range(width)
        )
        for permutation in permutations(range(n))
    )
    dependency = sum(
        any(truth[row] != truth[row ^ (1 << variable)] for row in range(width))
        for variable in range(n)
    )
    return (
        sum(truth),
        max((term.bit_count() for term in range(width) if anf[term]), default=0),
        sum(anf),
        max(sensitivities),
        sum(sensitivities),
        max((frequency.bit_count() for frequency in range(width) if walsh[frequency]), default=0),
        sum(map(abs, walsh)),
        automorphisms,
        max(certificates),
        max((certificates[row] for row in range(width) if not truth[row]), default=0),
        max((certificates[row] for row in range(width) if truth[row]), default=0),
        dependency,
    )


def minimum_exclusion_core(
    target: int, candidates: set[int], row_count: int
) -> tuple[int, ...] | None:
    for size in range(row_count + 1):
        for rows in combinations(range(row_count), size):
            row_mask = sum(1 << row for row in rows)
            if all((target ^ candidate) & row_mask for candidate in candidates):
                return rows
    return None


def truth_table(n: int, function: Callable[[tuple[int, ...]], int]) -> int:
    result = 0
    for row in range(1 << n):
        bits = tuple((row >> variable) & 1 for variable in range(n))
        result |= (function(bits) & 1) << row
    return result


def _restricted_values(
    mask: int,
    n: int,
    free: tuple[int, ...],
    fixed: tuple[tuple[int, int], ...],
) -> tuple[int, ...]:
    values = []
    for free_bits in product((0, 1), repeat=len(free)):
        assignment = dict(fixed)
        assignment.update(zip(free, free_bits))
        row = sum(assignment[index] << index for index in range(n))
        values.append((mask >> row) & 1)
    return tuple(values)


def parity_subcube_certificate(
    mask: int, n: int, min_free: int = 2
) -> ParitySubcubeCertificate | None:
    variables = tuple(range(n))
    for width in range(n, min_free - 1, -1):
        for free in combinations(variables, width):
            fixed_variables = tuple(v for v in variables if v not in free)
            for fixed_bits in product((0, 1), repeat=len(fixed_variables)):
                fixed = tuple(zip(fixed_variables, fixed_bits))
                values = _restricted_values(mask, n, free, fixed)
                parity = tuple(sum(bits) & 1 for bits in product((0, 1), repeat=width))
                if values == parity:
                    return ParitySubcubeCertificate(free, fixed, False)
                if values == tuple(1 - bit for bit in parity):
                    return ParitySubcubeCertificate(free, fixed, True)
    return None


def retained_parity_lower_bound(mask: int, n: int, enabled: bool = True) -> int | None:
    if not enabled:
        return None
    certificate = parity_subcube_certificate(mask, n)
    if certificate is None:
        return None
    return 3 * len(certificate.free_variables) - 3


def _append_xor(
    witness: list[tuple[int, int]], left: int, right: int, input_count: int
) -> int:
    t = len(witness) + input_count
    witness.append((left, right))
    u = len(witness) + input_count
    witness.append((left, t))
    v = len(witness) + input_count
    witness.append((right, t))
    out = len(witness) + input_count
    witness.append((u, v))
    return out


def _parity_witness(n: int, variables: Iterable[int]) -> Witness:
    chosen = tuple(variables)
    witness: list[tuple[int, int]] = []
    accumulator = chosen[0]
    for variable in chosen[1:]:
        accumulator = _append_xor(witness, accumulator, variable, n)
    return Witness(tuple(witness), accumulator)


def circuit_size_upper_bound(mask: int, n: int) -> int | None:
    parity = truth_table(n, lambda bits: sum(bits) & 1)
    parity_witness = _parity_witness(n, range(n))
    if mask == parity and evaluate_witness(n, parity_witness) == mask:
        return len(parity_witness.gates)

    for gate_variable in range(n):
        parity_variables = tuple(v for v in range(n) if v != gate_variable)
        candidate = truth_table(
            n,
            lambda bits, g=gate_variable, vs=parity_variables: bits[g]
            & (sum(bits[v] for v in vs) & 1),
        )
        if candidate != mask:
            continue
        witness = list(_parity_witness(n, parity_variables).gates)
        parity_wire = n + len(witness) - 1
        witness.append((gate_variable, parity_wire))
        nand_wire = n + len(witness) - 1
        witness.append((nand_wire, nand_wire))
        candidate_witness = Witness(tuple(witness), n + len(witness) - 1)
        if evaluate_witness(n, candidate_witness) == mask:
            return len(witness)
    return None
