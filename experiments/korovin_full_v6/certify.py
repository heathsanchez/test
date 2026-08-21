from __future__ import annotations
from collections import deque


def fmt(word):
    return 'ε' if not word else ''.join(word)


def decode(text):
    return () if text == 'ε' else tuple(text)


def bfs_representatives(world, execute):
    tokens = tuple(world.generators)
    start_state = execute(world, ())
    reps = {start_state: ()}
    q = deque([()])
    while q:
        word = q.popleft()
        for token in tokens:
            nxt = word + (token,)
            state = execute(world, nxt)
            if state not in reps:
                reps[state] = nxt
                q.append(nxt)
    return reps


def rewrite_neighbors(word, rules, max_word_len):
    for rule_index, (lhs, rhs) in enumerate(rules):
        for direction, (src, dst) in enumerate(((lhs, rhs), (rhs, lhs))):
            width = len(src)
            if width == 0:
                positions = range(len(word) + 1)
            else:
                positions = [
                    i for i in range(len(word) - width + 1)
                    if word[i:i + width] == src
                ]
            for position in positions:
                nxt = word[:position] + dst + word[position + width:]
                if len(nxt) <= max_word_len:
                    yield nxt, {
                        'rule': rule_index,
                        'direction': direction,
                        'position': position,
                        'before': fmt(word),
                        'after': fmt(nxt),
                    }


def derive(start, target, rules, max_word_len=7):
    if start == target:
        return []
    q = deque([start])
    previous = {start: None}
    how = {}
    while q:
        word = q.popleft()
        for nxt, step in rewrite_neighbors(word, rules, max_word_len):
            if nxt in previous:
                continue
            previous[nxt] = word
            how[nxt] = step
            if nxt == target:
                path = []
                cur = nxt
                while previous[cur] is not None:
                    path.append(how[cur])
                    cur = previous[cur]
                return list(reversed(path))
            q.append(nxt)
    return None


def verify_derivation(start, target, path, rules):
    if path is None:
        return False
    word = start
    for step in path:
        if decode(step['before']) != word:
            return False
        lhs, rhs = rules[step['rule']]
        src, dst = (lhs, rhs) if step['direction'] == 0 else (rhs, lhs)
        position = step['position']
        if word[position:position + len(src)] != src:
            return False
        word = word[:position] + dst + word[position + len(src):]
        if decode(step['after']) != word:
            return False
    return word == target


def global_certificate(world, execute, rules, max_derivation_word_len=7):
    tokens = tuple(world.generators)
    reps = bfs_representatives(world, execute)
    edges = []
    all_edges = True

    for state, rep in sorted(reps.items(), key=lambda kv: (len(kv[1]), kv[1])):
        for token in tokens:
            lhs = rep + (token,)
            target_state = execute(world, lhs)
            rhs = reps[target_state]
            path = derive(lhs, rhs, rules, max_derivation_word_len)
            valid = verify_derivation(lhs, rhs, path, rules)
            semantic_ok = execute(world, lhs) == execute(world, rhs)
            edges.append({
                'representative': fmt(rep),
                'token': token,
                'lhs': fmt(lhs),
                'rhs': fmt(rhs),
                'steps': len(path) if path is not None else None,
                'valid': valid,
                'semantic_ok': semantic_ok,
                'derivation': path,
            })
            all_edges = all_edges and valid and semantic_ok

    rules_sound = all(execute(world, lhs) == execute(world, rhs) for lhs, rhs in rules)
    start_rep_empty = reps[execute(world, ())] == ()

    return {
        'state_count': len(reps),
        'rule_count': len(rules),
        'rules_sound': rules_sound,
        'start_rep_empty': start_rep_empty,
        'edge_count': len(edges),
        'all_edges_certified': all_edges,
        'global_completeness_theorem': rules_sound and start_rep_empty and all_edges,
        'edges': edges,
    }


def prune_globally_redundant_rules(world, execute, rules, max_derivation_word_len=7):
    retained = list(rules)
    deletions = []
    changed = True
    while changed:
        changed = False
        for index in range(len(retained)):
            candidate = retained[:index] + retained[index + 1:]
            cert = global_certificate(
                world, execute, candidate,
                max_derivation_word_len=max_derivation_word_len,
            )
            if cert['global_completeness_theorem']:
                removed = retained[index]
                deletions.append({'lhs': fmt(removed[0]), 'rhs': fmt(removed[1])})
                retained = candidate
                changed = True
                break
    return retained, deletions
