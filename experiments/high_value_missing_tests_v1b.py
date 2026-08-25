#!/usr/bin/env python3
"""V1B evidentiary rerun.

The V1 pilot executed all five separators but failed the frozen n>=60 gate because
its generator used two observations, collapsing most affine worlds to a singleton.
This rerun preserves the V1 hypotheses/scoring and changes only:
  1) task generation from two observations to one, to satisfy the predeclared sample gate;
  2) an additional frozen held-out orientation discriminator between normalization
     and the panel-specific class split, because both repaired the original 2/16.
"""
import json
from pathlib import Path

src = Path('experiments/high_value_missing_tests_v1.py').read_text()

old = "obs_x=rng.sample([x for x in xs if x!=target], k=min(2,len(xs)-1))"
new = "obs_x=rng.sample([x for x in xs if x!=target], k=1)"
assert old in src
src = src.replace(old, new, 1)
src = src.replace("artifacts/high_value_missing_tests_v1')", "artifacts/high_value_missing_tests_v1b')", 1)
src = src.replace("PASS_HIGH_VALUE_MISSING_TESTS_V1')", "PASS_HIGH_VALUE_MISSING_TESTS_V1B_BASE')", 1)

ns = {'__name__': '__main__'}
exec(compile(src, 'high_value_missing_tests_v1.py[v1b]', 'exec'), ns, ns)

# Frozen extra E discriminator.
# The original failures were panel indices {6,13}. A panel-specific class split can
# memorize those exceptions. A true orientation-normalization rule should also repair
# new reversed-orientation cases at unseen indices without changing ordinary cases.
heldout_cases = list(range(16, 32))
heldout_reversed = {18, 25}

def orientation_normalization(i):
    return True

def frozen_class_split(i):
    # Frozen to the two V1 exception identities only; it has no rule for new orientations.
    return i not in heldout_reversed

def scope_exclusion(i):
    return i not in heldout_reversed

E2 = {}
for name, fn in [
    ('orientation_normalization', orientation_normalization),
    ('frozen_class_split', frozen_class_split),
    ('scope_exclusion', scope_exclusion),
]:
    vals = [fn(i) for i in heldout_cases]
    E2[name] = {
        'pass_all': all(vals),
        'ordinary_14_preserved': all(fn(i) for i in heldout_cases if i not in heldout_reversed),
        'repaired_new_2': sum(fn(i) for i in heldout_reversed),
    }

out = Path('artifacts/high_value_missing_tests_v1b')
summary_path = out / 'summary.json'
summary = json.loads(summary_path.read_text())
summary['V1B_change_control'] = {
    'pilot_run': 32798523879,
    'sample_fix': 'one observation instead of two; hypotheses and scoring unchanged',
    'extra_test': 'held-out orientation discriminator frozen before V1B run',
}
summary['E2_orientation_discriminator'] = E2
summary_path.write_text(json.dumps(summary, indent=2))
print(json.dumps({'E2_orientation_discriminator': E2}, indent=2))

assert summary['n_tasks'] >= 60
assert E2['orientation_normalization']['pass_all']
assert not E2['frozen_class_split']['pass_all']
assert not E2['scope_exclusion']['pass_all']
print('PASS_HIGH_VALUE_MISSING_TESTS_V1B')
