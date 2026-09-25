#!/usr/bin/env python3
"""Hosted exact H2 separator check for the frozen ac-03887 V1 collision."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import future_quotient_v1 as fq

OFFICIAL_PIN = "99a65377c5c4f412cd9af7b8d31c41464a855736"
SOURCE_HEAD = "ce752b5813b557ac5cc06d3df5e12df7f233bb1c"
SOURCE_ARTIFACT = 10838365781
CONTACT = (
    (2,1,2,-1,-1,-2,-2,1,1,2,1,2,-1,-2),
    (-2,-1,-2,-1,2,1,-2,-1,-1),
)
REPRESENTATIVE = (
    (2,1,2,2,2,1,-2,-1,-1,1,2,1),
    (-2,-1,-2,-1,1,2,2,-1,-1,-2),
)
EXPECTED_H1 = "bd6a8f51a1573c865f1d204b206733fe3dab9d36600e5eba86c6fffb82cf19cb"
EXPECTED_CONTACT_H2 = "e3b8400b970b3b285ceae77238450f9834aab39ef4e7410d44cf02865c62130b"
EXPECTED_REP_H2 = "54bd39e2ad509c3961891957bfd969bb0ed6c7816717ee097eca0966a6726777"

def h2_signature(core, state, total_cap=10000):
    root = fq.base_signature(state)
    children = []
    for move in range(core.NUM_MOVES):
        child = core.apply_move(state, move)
        if sum(map(len, child)) > total_cap:
            children.append(b"X")
        else:
            children.append(fq.future_signature(core, child, total_cap)[0])
    return fq.digest_parts((root, *children))

def main():
    acc_root = Path(sys.argv[1])
    sys.path.insert(0, str(acc_root / "competition/tools"))
    from verifier import core

    c1 = fq.future_signature(core, CONTACT, 10000)[0].hex()
    r1 = fq.future_signature(core, REPRESENTATIVE, 10000)[0].hex()
    c2 = h2_signature(core, CONTACT).hex()
    r2 = h2_signature(core, REPRESENTATIVE).hex()

    assert fq.OFFICIAL_PIN == OFFICIAL_PIN
    assert c1 == r1 == EXPECTED_H1
    assert c2 == EXPECTED_CONTACT_H2
    assert r2 == EXPECTED_REP_H2
    assert c2 != r2

    out = {
        "version": "acc-future-quotient-h2-separator-v1",
        "status": "WARRANTED_SEPARATOR",
        "official_pin": OFFICIAL_PIN,
        "source_head": SOURCE_HEAD,
        "source_artifact": SOURCE_ARTIFACT,
        "contact_state_key": fq.key_state(CONTACT).hex(),
        "representative_state_key": fq.key_state(REPRESENTATIVE).hex(),
        "v1_h1": c1,
        "contact_h2": c2,
        "representative_h2": r2,
        "h2_separates_v1_collision": True,
        "claim_boundary": "Exact H2 separation only; H2 remains search guidance, not proof equivalence or a certificate."
    }
    Path("h2-separator-evidence.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print("ACC_H2_SEPARATOR", json.dumps(out, sort_keys=True))

if __name__ == "__main__":
    main()
