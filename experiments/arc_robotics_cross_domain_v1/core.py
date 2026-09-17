from __future__ import annotations

import hashlib
import itertools
import json
import random
from typing import Iterable

TRIPLES = tuple(itertools.product((0, 1), repeat=3))
SOURCE_POSITIONS = ((1, 1), (1, 3), (3, 1))
SOURCE_OUTPUT_POSITION = (3, 3)


def truth_output(code: int, bits: tuple[int, int, int]) -> int:
    if not 0 <= code <= 255:
        raise ValueError(f"truth-table code out of range: {code}")
    a, b, c = bits
    if any(v not in (0, 1) for v in bits):
        raise ValueError(f"bits must be binary: {bits}")
    idx = (a << 2) | (b << 1) | c
    return (code >> idx) & 1


def _code_from_fn(fn) -> int:
    code = 0
    for bits in TRIPLES:
        idx = (bits[0] << 2) | (bits[1] << 1) | bits[2]
        code |= (int(fn(*bits)) & 1) << idx
    return code


def parity3_code() -> int:
    return _code_from_fn(lambda a, b, c: a ^ b ^ c)


def majority3_code() -> int:
    return _code_from_fn(lambda a, b, c: int(a + b + c >= 2))


def _empty_grid() -> list[list[int]]:
    return [[0 for _ in range(5)] for _ in range(5)]


def source_examples() -> list[dict]:
    examples = []
    target = parity3_code()
    for bits in TRIPLES:
        inp = _empty_grid()
        for (y, x), bit in zip(SOURCE_POSITIONS, bits):
            inp[y][x] = 2 if bit else 1
        out = [row[:] for row in inp]
        out_y, out_x = SOURCE_OUTPUT_POSITION
        out[out_y][out_x] = 4 if truth_output(target, bits) else 3
        examples.append({"input": inp, "output": out})
    return examples


def _parse_source_example(example: dict) -> tuple[tuple[int, int, int], int]:
    inp = example["input"]
    out = example["output"]
    bits = []
    for y, x in SOURCE_POSITIONS:
        cell = inp[y][x]
        if cell not in (1, 2):
            raise ValueError(f"unexpected source input token: {cell}")
        bits.append(1 if cell == 2 else 0)
    oy, ox = SOURCE_OUTPUT_POSITION
    result = out[oy][ox]
    if result not in (3, 4):
        raise ValueError(f"unexpected source output token: {result}")
    return tuple(bits), 1 if result == 4 else 0


def discover_source_operator(examples: Iterable[dict]) -> tuple[int, int]:
    parsed = [_parse_source_example(example) for example in examples]
    survivors = []
    evaluations = 0
    for code in range(256):
        ok = True
        for bits, expected in parsed:
            evaluations += 1
            if truth_output(code, bits) != expected:
                ok = False
        if ok:
            survivors.append(code)
    if len(survivors) != 1:
        raise RuntimeError(f"source operator not unique: {survivors}")
    return survivors[0], evaluations


def _transform_code(
    code: int,
    input_flips: tuple[int, int, int],
    output_flip: int,
) -> int:
    transformed = 0
    for bits in TRIPLES:
        source_bits = tuple(v ^ f for v, f in zip(bits, input_flips))
        value = truth_output(code, source_bits) ^ output_flip
        idx = (bits[0] << 2) | (bits[1] << 1) | bits[2]
        transformed |= value << idx
    return transformed


def operator_orbit(code: int) -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                _transform_code(code, flips, output_flip)
                for flips in TRIPLES
                for output_flip in (0, 1)
            }
        )
    )


def serialize_capability(code: int) -> str:
    if not 0 <= code <= 255:
        raise ValueError(f"truth-table code out of range: {code}")
    body = {"schema": "binary_relation_v1", "truth_table": code}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    payload = dict(body)
    payload["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_capability(payload: str) -> int:
    data = json.loads(payload)
    body = {"schema": data.get("schema"), "truth_table": data.get("truth_table")}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if data.get("sha256") != expected:
        raise ValueError("capability digest mismatch")
    if body["schema"] != "binary_relation_v1":
        raise ValueError(f"unsupported capability schema: {body['schema']}")
    code = int(body["truth_table"])
    if not 0 <= code <= 255:
        raise ValueError(f"truth-table code out of range: {code}")
    return code


def _target_setup(seed: int) -> tuple[int, dict, random.Random]:
    rng = random.Random(seed)
    input_flips = tuple(rng.randrange(2) for _ in range(3))
    output_flip = rng.randrange(2)
    target_code = _transform_code(parity3_code(), input_flips, output_flip)
    return target_code, {
        "input_flips": list(input_flips),
        "output_flip": output_flip,
    }, rng


def _observe(target_code: int, bits: tuple[int, int, int]) -> tuple[tuple[int, int, int], int]:
    return bits, truth_output(target_code, bits)


def _filter_once(candidates: list[int], observation: tuple[tuple[int, int, int], int]) -> tuple[list[int], int]:
    bits, expected = observation
    survivors = []
    evaluations = 0
    for code in candidates:
        evaluations += 1
        if truth_output(code, bits) == expected:
            survivors.append(code)
    return survivors, evaluations


def _cold_calibration(
    target_code: int,
    existing_observations: list[tuple[tuple[int, int, int], int]] | None = None,
) -> tuple[int | None, list[tuple[tuple[int, int, int], int]], int]:
    observations = list(existing_observations or [])
    candidates = list(range(256))
    evaluations = 0

    for observation in observations:
        candidates, used = _filter_once(candidates, observation)
        evaluations += used

    already_seen = {bits for bits, _ in observations}
    for bits in TRIPLES:
        if bits in already_seen:
            continue
        observation = _observe(target_code, bits)
        observations.append(observation)
        candidates, used = _filter_once(candidates, observation)
        evaluations += used
        if len(candidates) == 1:
            break

    learned = candidates[0] if len(candidates) == 1 else None
    return learned, observations, evaluations


def _transferred_calibration(
    target_code: int,
    family: tuple[int, ...],
) -> tuple[
    int | None,
    list[tuple[tuple[int, int, int], int]],
    int,
    bool,
]:
    candidates = list(family)
    observations: list[tuple[tuple[int, int, int], int]] = []
    evaluations = 0
    unique_at: int | None = None

    for bits in TRIPLES:
        observation = _observe(target_code, bits)
        observations.append(observation)
        candidates, used = _filter_once(candidates, observation)
        evaluations += used

        if not candidates:
            return None, observations, evaluations, True

        if len(candidates) == 1:
            if unique_at is None:
                unique_at = len(observations)
            elif len(observations) > unique_at:
                return candidates[0], observations, evaluations, False
        else:
            unique_at = None

    learned = candidates[0] if len(candidates) == 1 else None
    return learned, observations, evaluations, False


def run_arm(arm: str, seed: int, n_worlds: int = 64) -> dict:
    if arm not in {"COLD", "WARM", "SHAM", "ABLATION", "RESTART"}:
        raise ValueError(f"unknown arm: {arm}")
    if n_worlds < 1:
        raise ValueError("n_worlds must be positive")

    source_code, source_discovery_evaluations = discover_source_operator(source_examples())
    target_code, target_adapter, rng = _target_setup(seed)

    transferred_rejected = False
    retained_code: int | None = None

    if arm in {"COLD", "ABLATION"}:
        learned_code, observations, operator_evaluations = _cold_calibration(target_code)
    else:
        if arm == "SHAM":
            retained_code = majority3_code()
        else:
            retained_code = source_code
            if arm == "RESTART":
                retained_code = deserialize_capability(serialize_capability(retained_code))

        learned_code, observations, operator_evaluations, transferred_rejected = _transferred_calibration(
            target_code,
            operator_orbit(retained_code),
        )

        if transferred_rejected:
            learned_code, observations, fallback_evaluations = _cold_calibration(
                target_code,
                existing_observations=observations,
            )
            operator_evaluations += fallback_evaluations

    predictions = []
    truths = []
    if learned_code is None:
        predictions = [None for _ in range(n_worlds)]
        truths = [None for _ in range(n_worlds)]
        correct = 0
        unknown = n_worlds
    else:
        for _ in range(n_worlds):
            bits = tuple(rng.randrange(2) for _ in range(3))
            truth = truth_output(target_code, bits)
            prediction = truth_output(learned_code, bits)
            truths.append(truth)
            predictions.append(prediction)
        correct = sum(int(p == t) for p, t in zip(predictions, truths))
        unknown = sum(int(p is None) for p in predictions)

    calibration_interventions = len(observations)
    developmental_cost = operator_evaluations + calibration_interventions

    return {
        "arm": arm,
        "seed": seed,
        "n_worlds": n_worlds,
        "source_code": source_code,
        "source_discovery_evaluations": source_discovery_evaluations,
        "retained_code": retained_code,
        "target_code": target_code,
        "target_adapter": target_adapter,
        "learned_code": learned_code,
        "transferred_rejected": transferred_rejected,
        "calibration_interventions": calibration_interventions,
        "operator_evaluations": operator_evaluations,
        "developmental_cost": developmental_cost,
        "execution_probes": 3 * n_worlds,
        "correct": correct,
        "unknown": unknown,
        "predictions": predictions,
        "truths": truths,
        "calibration_trace": [
            {"bits": list(bits), "answer": answer}
            for bits, answer in observations
        ],
    }
