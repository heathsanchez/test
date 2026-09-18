"""Retrospective consequence-propagation fixture, not autonomous theorem discovery."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import collatz_macro_authority as authority
import collatz_macro_qualification as qualification

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/macro-qualification-v1'


def contract():
    return dict(execution='stepwise_forward_replay', metric='counted_T_steps',
                budget='preparation_plus_all_replay', claim='strict_baseline_advantage')


class Graph:
    """A dependency edge from one explicitly reviewed rule to matching jobs.

    Admission is an allowlist for a manually reviewed conditional argument,
    NOT a proof checker. Callers construct contracts for this fixed runner.
    """
    def __init__(self, contracts):
        self.contracts = contracts
        self.states = ['pending'] * len(contracts)
        self.events = []
        self.matches = 0

    def admit(self, authority_id):
        authority.require(authority_id == 'reviewed-dominance-v1', 'unadmitted rule')
        for i, c in enumerate(self.contracts):
            self.matches += 1
            if c == contract() and self.states[i] == 'pending':
                self.states[i] = 'blocked'
                self.events.append(dict(job=i, dependency=authority_id, action='block'))

    def revoke(self):
        for i, state in enumerate(self.states):
            if state == 'blocked':
                self.states[i] = 'pending'
                self.events.append(dict(job=i, action='reopen'))


def check_result(result):
    """Check each finite certificate and its claimed direct-iteration allowance."""
    for row in result['rows']:
        cert = row['certificate']
        if cert:
            authority.require(cert['t'] <= row['preparation_steps'] + row['replay_steps'],
                              'certificate outside matched budget')
            authority.verify_descent(cert['n'], cert['t'], cert['y'])


def worker(arm, output):
    begin = time.perf_counter()
    steps = 0
    original = authority.step
    def counted(x):
        nonlocal steps
        steps += 1
        return original(x)
    authority.step = counted
    bank = authority.restore((EVIDENCE / 'bank.json').read_text())
    cohort = json.loads((EVIDENCE / 'cohort.json').read_text())
    authority.require(authority.digest(cohort['sources']) == cohort['digest'], 'cohort changed')
    # Recheck endpoint preparation rather than relying only on stored labels.
    for row in cohort['sources']:
        for k, r, m, x in row['starts']:
            y = row['n']
            for _ in range(k): y = authority.step(y)
            authority.require(y == x == 2**r*m-1, 'invalid endpoint')
    graph = Graph([contract() for _ in range(8)])
    if arm == 'guarded': graph.admit('reviewed-dominance-v1')
    completed = []
    stored = []
    for i in range(8):
        if graph.states[i] != 'pending': continue
        caps = bank['capabilities']
        # Eight distinct deterministic policy orders of the same verified bank.
        shift = i * 59
        variant = authority.seal(caps[shift:] + caps[:shift])
        result = qualification.evaluate(variant, cohort)
        check_result(result)
        graph.states[i] = 'completed'
        completed.append(dict(job=i, closed=result['closed'],
                              result_digest=authority.digest(result)))
        if arm != 'isolated': stored.append('reviewed-dominance-v1')
        # Rule is manually supplied; first completion is a controlled release
        # event. It does not infer a universal theorem from finite observations.
        if arm == 'flash' and i == 0: graph.admit(stored[-1])
    obj = dict(arm=arm, completed=completed, states=graph.states,
               graph_events=graph.events, rule_matches=graph.matches,
               counted_T_calls_including_verification=steps,
               worker_seconds=time.perf_counter()-begin,
               scope='retrospective fixed workload; manually reviewed propagation rule',
               rule_document_sha256=hashlib.sha256(
                   (ROOT/'docs/collatz-macro-qualification-v1.md').read_bytes()).hexdigest())
    output.write_text(authority.canonical(obj))


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    results = []
    arms = ['isolated', 'shared', 'flash', 'ablation', 'guarded']
    for repeat in range(3):
        for arm in arms[repeat:] + arms[:repeat]:
            path = output / f'{arm}-{repeat}.json'
            begin = time.perf_counter()
            subprocess.run([sys.executable, __file__, '--worker', arm,
                            '--output', str(path)], check=True)
            row = json.loads(path.read_text())
            row['process_seconds'] = time.perf_counter()-begin
            row['repeat'] = repeat
            results.append(row)
    groups = {arm:[r for r in results if r['arm']==arm] for arm in arms}
    reference = groups['isolated'][0]['completed']
    for arm in ('isolated', 'shared', 'ablation'):
        authority.require(all(r['completed']==reference for r in groups[arm]),
                          'nonpropagating control mismatch')
    authority.require(all(len(r['completed'])==1 and r['states'].count('blocked')==7
                          for r in groups['flash']), 'flash failed to propagate')
    authority.require(all(not r['completed'] and r['states'].count('blocked')==8
                          for r in groups['guarded']), 'guarded baseline failed')
    import statistics
    summary = dict(verdict='PASS_BOUNDED_PROPAGATION_NO_ADVANTAGE_OVER_UPFRONT_GUARD',
        arms={arm:dict(completed=len(rows[0]['completed']),
            blocked=rows[0]['states'].count('blocked'),
            T_calls=rows[0]['counted_T_calls_including_verification'],
            median_process_seconds=statistics.median(r['process_seconds'] for r in rows))
            for arm,rows in groups.items()},
        limitations=['retrospective, deliberately redundant policy workload',
          'shared control stores evidence but does not query before dispatch',
          'ablation removes propagation; identical to passive shared control',
          'manually reviewed rule; no automated universal proof authority',
          'sequential event scheduler; no concurrent cancellation measured',
          'no Collatz termination or general Flash superiority established'])
    (output/'summary.json').write_text(authority.canonical(summary))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--worker', choices=['isolated','shared','flash','ablation','guarded'])
    args = p.parse_args()
    if args.worker: worker(args.worker,args.output)
    else: run(args.output)
