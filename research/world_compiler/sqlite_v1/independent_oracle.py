"""Independently replay real SQLite outcomes; never score using learner's probe."""
import argparse
import json
import sqlite3
from pathlib import Path

from engine import DEV, future_schema, world, passive, candidate_probes, apply_capability


def exact_native_verdict(db, schema):
    """Separate SQL oracle: valid parent-child succeeds, orphan FK fails."""
    def qi(n):
        return '"' + n.replace('"', '""') + '"'
    pid = 'real_parent' if schema.key_type == 'TEXT' else 101
    bad = 'not_in_parent' if schema.key_type == 'TEXT' else 990099
    extra = 'native' if schema.extra_type == 'TEXT' else 5
    previous = [tuple(r) for r in db.execute(
        f'SELECT * FROM {qi(schema.child)} ORDER BY rowid').fetchall()]
    try:
        db.execute('SAVEPOINT independent_native_oracle')
        db.execute(f'INSERT INTO {qi(schema.parent)}({qi(schema.parent_key)}) VALUES(?)', (pid,))
        db.execute(f'INSERT INTO {qi(schema.child)}({qi(schema.child_fk)},{qi(schema.extra)}) VALUES(?,?)',
                   (pid, extra))
        rejected = False
        try:
            db.execute(f'INSERT INTO {qi(schema.child)}({qi(schema.child_fk)},{qi(schema.extra)}) VALUES(?,?)',
                       (bad, extra))
        except sqlite3.IntegrityError as exc:
            rejected = 'FOREIGN KEY' in str(exc).upper()
        return rejected
    finally:
        db.execute('ROLLBACK TO independent_native_oracle')
        db.execute('RELEASE independent_native_oracle')
        assert [tuple(r) for r in db.execute(
            f'SELECT * FROM {qi(schema.child)} ORDER BY rowid').fetchall()] == previous


def inspect(receipt_path):
    r = json.loads(Path(receipt_path).read_text())
    assert r['status'] == 'PASS_NATIVE_BOUNDED_OBSERVATION_AND_INTERVENTION'
    seed, manifest = r['seed'], r['compiled_capability']
    assert len(r['future_cases']) == 24
    assert r['intervention_selection']['actual_tested'] == r['intervention_selection']['candidate_count']
    assert r['intervention_selection']['candidate_count'] <= 250
    assert r['intervention_selection']['program'] == manifest['intervention']
    assert r['diagnosis']['passive_indistinguishable']
    assert r['stale_manifest_denied']
    assert r['ablation'] == {'unsafe_without_capability': False, 'safe_without_capability': True}
    actual = []
    for i in range(12):
        spec = future_schema(seed, i)
        for enabled in (False, True):
            db = world(spec, enabled)
            try:
                before = passive(db)
                assert bool(db.execute('PRAGMA foreign_keys').fetchone()[0]) == enabled
                assert exact_native_verdict(db, spec) == enabled
                assert len(candidate_probes(db)) == 1
                if not enabled:
                    db.execute(manifest['intervention'])
                assert exact_native_verdict(db, spec)
                assert passive(db) == before
                actual.append((i, enabled))
            finally:
                db.close()
    assert len(actual) == 24
    guarded = world(future_schema(seed, 0), False)
    try:
        result = apply_capability(guarded, manifest)
        assert result == {'status': 'VERIFIED_NATIVE_INTERVENTION', 'changes': 1}
        assert exact_native_verdict(guarded, future_schema(seed, 0))
    finally:
        guarded.close()
    corrupted = json.loads(json.dumps(manifest))
    corrupted['probe']['values'] = [0]
    refused = False
    unsafe = world(DEV, False)
    try:
        old = passive(unsafe)
        try:
            apply_capability(unsafe, corrupted)
        except PermissionError:
            refused = True
        assert passive(unsafe) == old
    finally:
        unsafe.close()
    assert refused
    # Evidence for the baseline is the actual source-native execution trace in receipt.
    assert r['baselines']['native_successes'] == 24
    assert r['baselines']['configuration_changes'] == 12
    assert r['baselines']['direct_observation_reads'] == 24
    return {
        'verdict': 'PASS_INDEPENDENT_NATIVE_ORACLE',
        'native_cases': len(actual),
        'selected_program': manifest['intervention'],
        'compared_to_baseline': 'TIE_IN_SUCCESS; STRONG_BASELINE_CHEAPER_ACQUISITION',
        'manifest_tamper_denied': refused,
        'sqlite_version': sqlite3.sqlite_version
    }


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('receipt')
    p.add_argument('--out', required=True)
    args = p.parse_args()
    answer = inspect(args.receipt)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(answer, indent=2, sort_keys=True) + '\n')
    print(json.dumps(answer, sort_keys=True))
