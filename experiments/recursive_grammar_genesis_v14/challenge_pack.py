#!/usr/bin/env python3
"""Post-freeze corpora for V14 recursive grammar genesis."""
from __future__ import annotations

from basis import GrammarCorpus, VerifiedPhraseAtom


A = "phr_6f2a"
B = "phr_b913"
C = "phr_0c71"
D = "phr_f24e"
E = "phr_8dd0"
BAD = "phr_bad0"


def atom(atom_id, expansion, p1, p2, verified=True):
    return VerifiedPhraseAtom(
        atom_id=atom_id,
        expansion=tuple(expansion),
        provenance=(p1, p2),
        verified=verified,
        interface="anonymous_action_stream",
    )


ATOMS = {
    A: atom(A, (0, 1, 0), "A_world_1", "A_world_2"),
    B: atom(B, (2, 1), "B_world_1", "B_world_2"),
    C: atom(C, (0,), "C_world_1", "C_world_2"),
    D: atom(D, (1,), "D_world_1", "D_world_2"),
    E: atom(E, (2,), "E_world_1", "E_world_2"),
}


# Main corpus: recurring phrase-of-phrase structure.
MAIN_CORPUS = GrammarCorpus(
    atoms=ATOMS,
    episodes=(
        (A, B, A, B, A, B, A, B, C),
        (A, B, A, B, A, B, A, B, D),
    ),
    complete_authority=True,
    corpus_id="main_phrase_of_phrase",
)

# Held-out transfer episode with a new tail atom.
HELDOUT = (A, B, A, B, A, B, A, B, E)

# Same atom counts for A/B as heldout but different ordering.
WRONG_ORDER = (A, A, A, A, B, B, B, B, E)


# Structurally different corpus: one repeated atom rather than an alternating
# pair. The same generic learner should induce a different grammar.
HET_CORPUS = GrammarCorpus(
    atoms=ATOMS,
    episodes=(
        (A, A, A, A, A, A, C),
        (A, A, A, A, A, A, D),
    ),
    complete_authority=True,
    corpus_id="heterogeneous_run_structure",
)


# High recurrence inside one episode only: must not compile.
SINGLE_EXAMPLE_CORPUS = GrammarCorpus(
    atoms=ATOMS,
    episodes=(
        (A, B, A, B, A, B, A, B, A, B, A, B, C),
    ),
    complete_authority=True,
    corpus_id="single_example_only",
)


# Pair recurs across two episodes exactly twice total. Rule definition costs
# two tokens, so gain=0 and it must not compile.
NO_GAIN_CORPUS = GrammarCorpus(
    atoms=ATOMS,
    episodes=(
        (A, B, C),
        (A, B, D),
    ),
    complete_authority=True,
    corpus_id="zero_gain_control",
)


BAD_ATOMS = dict(ATOMS)
BAD_ATOMS[BAD] = VerifiedPhraseAtom(
    atom_id=BAD,
    expansion=(0, 2),
    provenance=("only_one_origin",),
    verified=False,
    interface="anonymous_action_stream",
)

BAD_AUTH_CORPUS = GrammarCorpus(
    atoms=BAD_ATOMS,
    episodes=(
        (A, BAD, A),
        (A, BAD, B),
    ),
    complete_authority=True,
    corpus_id="bad_lower_authority",
)
