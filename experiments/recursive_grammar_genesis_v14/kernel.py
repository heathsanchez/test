#!/usr/bin/env python3
"""Frozen V14 generic binary grammar induction kernel.

The learner receives only verified phrase atoms and ordered episodes. It
discovers anonymous binary grammar rules from recurring adjacent pairs,
retaining only independently supported, exact-replay, positive-gain rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from basis import GrammarCorpus, VerifiedPhraseAtom, anonymous_rule_id


Token = str
Episode = Tuple[Token, ...]


@dataclass(frozen=True)
class GrammarRule:
    rule_id: str
    rhs: Tuple[Token, Token]
    support_episodes: Tuple[int, ...]
    replacement_count: int
    gain: int
    provenance: Tuple[str, ...]

    def data(self) -> Any:
        return {
            "rule_id": self.rule_id,
            "rhs": list(self.rhs),
            "support_episodes": list(self.support_episodes),
            "replacement_count": self.replacement_count,
            "gain": self.gain,
            "provenance": list(self.provenance),
        }


@dataclass(frozen=True)
class GrammarState:
    encoded_episodes: Tuple[Episode, ...]
    rules: Tuple[GrammarRule, ...]
    source_expansions: Tuple[Tuple[int, ...], ...]
    initial_token_count: int
    current_token_count: int
    grammar_definition_cost: int
    total_description_cost: int

    def rule_map(self) -> Dict[str, GrammarRule]:
        return {r.rule_id: r for r in self.rules}

    def data(self) -> Any:
        return {
            "encoded_episodes": [list(ep) for ep in self.encoded_episodes],
            "rules": [r.data() for r in self.rules],
            "initial_token_count": self.initial_token_count,
            "current_token_count": self.current_token_count,
            "grammar_definition_cost": self.grammar_definition_cost,
            "total_description_cost": self.total_description_cost,
        }


class Kernel:
    RULE_DEFINITION_COST = 2

    @staticmethod
    def _require_authority(corpus: GrammarCorpus) -> Optional[Dict[str, Any]]:
        if not corpus.complete_authority:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "corpus_authority_incomplete",
            }
        bad = [
            atom.atom_id
            for atom in corpus.atoms.values()
            if not atom.authoritative()
        ]
        if bad:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "lower_phrase_atom_not_authoritative",
                "bad_atoms": bad,
            }
        return None

    @staticmethod
    def _replace_pair(
        episode: Sequence[Token],
        pair: Tuple[Token, Token],
        replacement: Token,
    ) -> Tuple[Episode, int]:
        out: List[Token] = []
        i = 0
        count = 0
        while i < len(episode):
            if (
                i + 1 < len(episode)
                and episode[i] == pair[0]
                and episode[i + 1] == pair[1]
            ):
                out.append(replacement)
                count += 1
                i += 2
            else:
                out.append(episode[i])
                i += 1
        return tuple(out), count

    @classmethod
    def _pair_stats(
        cls,
        episodes: Sequence[Sequence[Token]],
        *,
        allow_hierarchy: bool,
        rule_ids: Iterable[str],
    ) -> Dict[Tuple[Token, Token], Dict[str, Any]]:
        rule_ids = set(rule_ids)
        all_pairs = set()
        for ep in episodes:
            for i in range(len(ep) - 1):
                pair = (ep[i], ep[i + 1])
                if not allow_hierarchy and (
                    pair[0] in rule_ids or pair[1] in rule_ids
                ):
                    continue
                all_pairs.add(pair)

        stats: Dict[Tuple[Token, Token], Dict[str, Any]] = {}
        for pair in sorted(all_pairs):
            support = []
            replacements = 0
            for epi, ep in enumerate(episodes):
                _enc, count = cls._replace_pair(ep, pair, "__TMP__")
                if count:
                    support.append(epi)
                    replacements += count
            gain = replacements - cls.RULE_DEFINITION_COST
            stats[pair] = {
                "support_episodes": tuple(support),
                "replacement_count": replacements,
                "gain": gain,
            }
        return stats

    @staticmethod
    def _expand_token(
        token: Token,
        atoms: Mapping[str, VerifiedPhraseAtom],
        rules: Mapping[str, GrammarRule],
        _stack: Tuple[str, ...] = tuple(),
    ) -> Tuple[int, ...]:
        if token in atoms:
            return tuple(atoms[token].expansion)
        if token not in rules:
            raise KeyError(f"unknown grammar token {token}")
        if token in _stack:
            raise ValueError("cyclic grammar dependency")
        rule = rules[token]
        out = []
        for child in rule.rhs:
            out.extend(
                Kernel._expand_token(
                    child,
                    atoms,
                    rules,
                    _stack + (token,),
                )
            )
        return tuple(out)

    @classmethod
    def _expand_episode(
        cls,
        episode: Sequence[Token],
        atoms: Mapping[str, VerifiedPhraseAtom],
        rules: Mapping[str, GrammarRule],
    ) -> Tuple[int, ...]:
        out = []
        for token in episode:
            out.extend(cls._expand_token(token, atoms, rules))
        return tuple(out)

    @classmethod
    def _verify_exact_replay(
        cls,
        corpus: GrammarCorpus,
        episodes: Sequence[Sequence[Token]],
        rules: Sequence[GrammarRule],
        source_expansions: Sequence[Sequence[int]],
    ) -> bool:
        rule_map = {r.rule_id: r for r in rules}
        if len(episodes) != len(source_expansions):
            return False
        try:
            for ep, expected in zip(episodes, source_expansions):
                got = cls._expand_episode(ep, corpus.atoms, rule_map)
                if tuple(got) != tuple(expected):
                    return False
        except (KeyError, ValueError):
            return False
        return True

    @staticmethod
    def _description_cost(
        episodes: Sequence[Sequence[Token]],
        rules: Sequence[GrammarRule],
    ) -> Tuple[int, int, int]:
        current_tokens = sum(len(ep) for ep in episodes)
        grammar_cost = sum(len(rule.rhs) for rule in rules)
        return (
            current_tokens,
            grammar_cost,
            current_tokens + grammar_cost,
        )

    def induce(
        self,
        corpus: GrammarCorpus,
        *,
        allow_hierarchy: bool = True,
        max_rules: Optional[int] = None,
    ) -> Dict[str, Any]:
        auth = self._require_authority(corpus)
        if auth:
            return auth

        source_expansions = corpus.source_expansions()
        episodes = tuple(tuple(ep) for ep in corpus.episodes)
        rules: List[GrammarRule] = []
        initial_token_count = sum(len(ep) for ep in episodes)
        generations: List[Dict[str, Any]] = []

        if max_rules is None:
            max_rules = max(1, initial_token_count)

        for generation in range(int(max_rules) + 1):
            stats = self._pair_stats(
                episodes,
                allow_hierarchy=allow_hierarchy,
                rule_ids=[r.rule_id for r in rules],
            )

            eligible = []
            for pair, row in stats.items():
                if len(row["support_episodes"]) < 2:
                    continue
                if row["gain"] <= 0:
                    continue
                eligible.append((pair, row))

            record: Dict[str, Any] = {
                "generation": generation,
                "encoded_episodes": [list(ep) for ep in episodes],
                "candidate_count": len(stats),
                "eligible_candidates": [
                    {
                        "pair": list(pair),
                        "support_episodes": list(row["support_episodes"]),
                        "replacement_count": row["replacement_count"],
                        "gain": row["gain"],
                    }
                    for pair, row in sorted(
                        eligible,
                        key=lambda x: (-x[1]["gain"], x[0]),
                    )
                ],
            }

            if not eligible:
                generations.append(record)
                current_tokens, grammar_cost, total_cost = self._description_cost(
                    episodes, rules
                )
                state = GrammarState(
                    encoded_episodes=episodes,
                    rules=tuple(rules),
                    source_expansions=tuple(tuple(x) for x in source_expansions),
                    initial_token_count=initial_token_count,
                    current_token_count=current_tokens,
                    grammar_definition_cost=grammar_cost,
                    total_description_cost=total_cost,
                )
                if not self._verify_exact_replay(
                    corpus,
                    state.encoded_episodes,
                    state.rules,
                    state.source_expansions,
                ):
                    return {
                        "status": "REPLAY_FAILED",
                        "generations": generations,
                    }
                return {
                    "status": "VERIFIED",
                    "state": state.data(),
                    "generations": generations,
                    "rule_count": len(rules),
                    "compression_gain": initial_token_count - total_cost,
                }

            best_gain = max(row["gain"] for _pair, row in eligible)
            best = [
                (pair, row)
                for pair, row in eligible
                if row["gain"] == best_gain
            ]

            if len(best) > 1:
                record["frontier"] = [
                    {
                        "pair": list(pair),
                        "gain": row["gain"],
                        "support_episodes": list(row["support_episodes"]),
                    }
                    for pair, row in best
                ]
                generations.append(record)
                return {
                    "status": "VERIFIED_FRONTIER",
                    "reason": "equal_max_gain_incomparable_rules",
                    "frontier": record["frontier"],
                    "generations": generations,
                }

            pair, row = best[0]
            rule_id = anonymous_rule_id(pair)
            rule = GrammarRule(
                rule_id=rule_id,
                rhs=pair,
                support_episodes=tuple(row["support_episodes"]),
                replacement_count=int(row["replacement_count"]),
                gain=int(row["gain"]),
                provenance=tuple(
                    f"{corpus.corpus_id}:episode:{i}"
                    for i in row["support_episodes"]
                ),
            )

            # Tentative replacement, then exact replay before admission.
            next_episodes = []
            actual_replacements = 0
            for ep in episodes:
                enc, count = self._replace_pair(ep, pair, rule_id)
                next_episodes.append(enc)
                actual_replacements += count

            tentative_rules = tuple(rules + [rule])
            if actual_replacements != rule.replacement_count:
                return {
                    "status": "INTERNAL_COUNT_MISMATCH",
                    "generations": generations,
                }

            if not self._verify_exact_replay(
                corpus,
                tuple(next_episodes),
                tentative_rules,
                source_expansions,
            ):
                return {
                    "status": "REPLAY_FAILED",
                    "candidate_rule": rule.data(),
                    "generations": generations,
                }

            before = self._description_cost(episodes, rules)[2]
            after = self._description_cost(next_episodes, tentative_rules)[2]
            if not (after < before):
                return {
                    "status": "CERTIFIED_NO_POSITIVE_GAIN",
                    "candidate_rule": rule.data(),
                    "before_cost": before,
                    "after_cost": after,
                    "generations": generations,
                }

            record["promoted_rule"] = rule.data()
            record["before_cost"] = before
            record["after_cost"] = after
            generations.append(record)

            rules.append(rule)
            episodes = tuple(next_episodes)

        return {
            "status": "UNKNOWN_SEARCH",
            "reason": "max_rules_exhausted",
            "generations": generations,
        }

    @classmethod
    def state_from_data(cls, state_data: Mapping[str, Any]) -> GrammarState:
        rules = tuple(
            GrammarRule(
                rule_id=row["rule_id"],
                rhs=tuple(row["rhs"]),
                support_episodes=tuple(row["support_episodes"]),
                replacement_count=int(row["replacement_count"]),
                gain=int(row["gain"]),
                provenance=tuple(row["provenance"]),
            )
            for row in state_data["rules"]
        )
        return GrammarState(
            encoded_episodes=tuple(
                tuple(ep) for ep in state_data["encoded_episodes"]
            ),
            rules=rules,
            source_expansions=tuple(),
            initial_token_count=int(state_data["initial_token_count"]),
            current_token_count=int(state_data["current_token_count"]),
            grammar_definition_cost=int(state_data["grammar_definition_cost"]),
            total_description_cost=int(state_data["total_description_cost"]),
        )

    @classmethod
    def validate_rule_dependencies(
        cls,
        atoms: Mapping[str, VerifiedPhraseAtom],
        rules: Sequence[GrammarRule],
    ) -> Dict[str, Any]:
        available = set(atoms.keys())
        for rule in rules:
            missing = [x for x in rule.rhs if x not in available]
            if missing:
                return {
                    "status": "INVALID_GRAMMAR_DEPENDENCY",
                    "rule_id": rule.rule_id,
                    "missing": missing,
                }
            available.add(rule.rule_id)
        return {"status": "VERIFIED"}

    @classmethod
    def encode_with_rules(
        cls,
        sequence: Sequence[Token],
        rules: Sequence[GrammarRule],
    ) -> Episode:
        out = tuple(sequence)
        for rule in rules:
            out, _count = cls._replace_pair(out, rule.rhs, rule.rule_id)
        return out

    @classmethod
    def replay_sequence(
        cls,
        sequence: Sequence[Token],
        atoms: Mapping[str, VerifiedPhraseAtom],
        rules: Sequence[GrammarRule],
    ) -> Dict[str, Any]:
        dep = cls.validate_rule_dependencies(atoms, rules)
        if dep["status"] != "VERIFIED":
            return dep

        encoded = cls.encode_with_rules(sequence, rules)
        expected = []
        for token in sequence:
            if token not in atoms:
                return {
                    "status": "UNKNOWN_AUTHORITY",
                    "reason": f"heldout token {token} is not a verified phrase atom",
                }
            expected.extend(atoms[token].expansion)

        rule_map = {r.rule_id: r for r in rules}
        try:
            expanded = cls._expand_episode(encoded, atoms, rule_map)
        except (KeyError, ValueError) as exc:
            return {
                "status": "REPLAY_FAILED",
                "reason": str(exc),
            }

        return {
            "status": "VERIFIED" if tuple(expanded) == tuple(expected) else "REPLAY_FAILED",
            "encoded": list(encoded),
            "encoded_length": len(encoded),
            "direct_length": len(sequence),
            "expanded_primitive_length": len(expanded),
            "rules_used": [
                r.rule_id
                for r in rules
                if r.rule_id in encoded
                or any(r.rule_id in rr.rhs for rr in rules)
            ],
        }

    @classmethod
    def construct_under_budget(
        cls,
        sequence: Sequence[Token],
        atoms: Mapping[str, VerifiedPhraseAtom],
        rules: Sequence[GrammarRule],
        budget: int,
    ) -> Dict[str, Any]:
        replay = cls.replay_sequence(sequence, atoms, rules)
        if replay.get("status") != "VERIFIED":
            return replay
        ok = replay["encoded_length"] <= int(budget)
        return {
            **replay,
            "budget": int(budget),
            "within_budget": ok,
            "status": "VERIFIED" if ok else "UNKNOWN_BUDGET",
        }

    @classmethod
    def remove_rule(
        cls,
        rules: Sequence[GrammarRule],
        rule_id: str,
    ) -> Tuple[GrammarRule, ...]:
        return tuple(r for r in rules if r.rule_id != rule_id)
