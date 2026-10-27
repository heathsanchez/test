"""Independent CPU quantification of native H100 logit variation.

Requires the full raw-BF16 replay and input/reference repeatability checks
to pass before attributing variation to native execution. Reports exact bit
changes, numerical drift, winner-score changes and top-token stability.
Does not diagnose the source of nondeterminism or prove future repeatability.
"""
import argparse
import base64
import json
import math
import struct
import zlib
from itertools import combinations
from pathlib import Path

from independent_consequence_assurance import load_json
from independent_full_logit_replay import decode, N
from independent_repeatability_assurance import audit as repeat_audit


def ensure(yes, message):
    if not yes:
        raise ValueError("REJECTED_REPEAT_VARIANCE: " + message)


def raw_words(rec):
    # Decode performs bounded zlib, SHA-256 and finite-value verification.
    floats = decode(rec)
    compressed = base64.b64decode(rec["zlib_base64"], validate=True)
    raw = zlib.decompress(compressed)
    words = [w for (w,) in struct.iter_unpack("<H", raw)]
    ensure(len(words) == N == len(floats), "BF16 word count")
    return words, floats


def pairwise_variance(first, second):
    a, av = first
    b, bv = second
    changed = sum(x != y for x, y in zip(a, b))
    absdiff = [abs(x-y) for x, y in zip(av, bv)]
    mx = max(absdiff)
    ix = absdiff.index(mx)
    return {
        "elements": N,
        "different_bf16_words": changed,
        "different_word_fraction": changed / N,
        "max_abs_difference": mx,
        "mean_abs_difference": math.fsum(absdiff) / N,
        "rms_difference": math.sqrt(math.fsum(x*x for x in absdiff) / N),
        "max_diff_index": ix,
        "max_diff_first": av[ix],
        "max_diff_second": bv[ix],
    }


def audit(report):
    prior = repeat_audit(report)
    ensure(prior["status"] == "REFERENCE_AND_INPUT_REPEATABILITY_ESTABLISHED",
           "no stable sampled initial state and full reference output")
    ensure(prior["all_six_reference_native_top1_agree"] is True,
           "top-token parity failed in repeated execution")
    cache = {
        key: raw_words(report["checks"][key]["raw_logits_bf16"]["native"])
        for key in prior["cases"]
    }
    pair_metrics = {}
    grouped = {}
    for sched in ("rr", "dag"):
        keys = [f"rep{i}_{sched}" for i in (1, 2, 3)]
        names = []
        for a,b in combinations(keys, 2):
            name = f"{a}__vs__{b}"
            pair_metrics[name] = pairwise_variance(cache[a], cache[b])
            names.append(name)
        grouped[sched] = {
            "pair_count": len(names),
            "all_pairwise_bitwise_identical": all(
                pair_metrics[n]["different_bf16_words"] == 0 for n in names),
            "min_changed_elements": min(pair_metrics[n]["different_bf16_words"] for n in names),
            "max_changed_elements": max(pair_metrics[n]["different_bf16_words"] for n in names),
            "max_run_to_run_abs_difference": max(
                pair_metrics[n]["max_abs_difference"] for n in names),
            "min_top1_gap": min(report["checks"][key]["logit_choice"]["native_top1_margin"]
                                for key in keys),
            "tolerance_violations_by_rep": {
                key: report["checks"][key]["fields"]["logits"]["violations"]
                for key in keys
            },
        }
    for i in (1, 2, 3):
        name = f"rep{i}_rr__vs__rep{i}_dag"
        pair_metrics[name] = pairwise_variance(cache[f"rep{i}_rr"], cache[f"rep{i}_dag"])
    return {
        "schema": "mathgraph-h100-independent-repeat-variance-v1",
        "status": ("NATIVE_BF16_OUTPUTS_NONREPEATABLE_TOP1_STABLE"
                   if not all(grouped[s]["all_pairwise_bitwise_identical"] for s in ("rr","dag"))
                   else "NATIVE_BF16_OUTPUTS_BITWISE_REPEATABLE_IN_SAMPLE"),
        "source_pin": prior["source_pin"],
        "cases_checked": prior["cases_checked"],
        "sampled_initial_states_equal": prior["input_sample_digest_distinct_count"] == 1,
        "reference_logit_bits_equal": prior["reference_output_digest_distinct_count"] == 1,
        "all_six_top1_winners_equal": prior["all_six_native_winners_equal"],
        "native_matches_reference_top1_in_all_six": prior["all_six_reference_native_top1_agree"],
        "by_scheduler": grouped,
        "pairwise": pair_metrics,
        "trusted_boundary": (
            "exact retained native BF16 logit bits independently compared; "
            "sampled input fingerprint and bitwise reference output, "
            "no independent GPU re-execution or cause-of-variation determination"
        ),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("evidence", type=Path)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    result = json.dumps(audit(load_json(a.evidence)), indent=2, sort_keys=True) + "\n"
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(result)
    print(result, end="")


if __name__ == "__main__":
    main()
