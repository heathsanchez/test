#!/usr/bin/env python3
"""Deterministic candidate transform; source and diff are retained by qualification.

Reference: sokonanoda 708859e6 src/checker/conv.rs unify_iota/spine_probe.
A failed minor-premise comparison is not a refutation of recursor results.
No new reduction rule, constructor inference, or equality axiom is added.
"""
from pathlib import Path
import difflib
import hashlib
import json

root=Path('metatron-kernel/src')
old_type=(root/'typecheck.rs').read_text()
anchor='    pub(crate) fn machine(&self) -> Machine<\'_> {'
assert old_type.count(anchor)==1
new_type=old_type.replace(anchor,"""    pub(crate) fn has_certified_recursor_rule(&self, name: NameId) -> bool {
        self.environment.recursor_reduction(name).is_some()
    }

"""+anchor)
old_conv=(root/'convert.rs').read_text()
anchor2='''                match compare_values(
                    checker,
                    cheap_left,
                    cheap_right,
                    remaining,
                    depth,
                    context,
                    &mut work,
                    &mut proof_function_frees,
                ) {'''
assert old_conv.count(anchor2)==1
insert='''                // Recursors are not injective in their minor premises.
                // Probe argument congruence in a disposable worklist. Its
                // failure must not commit argument equality obligations to
                // the enclosing conversion: first try licensed iota on the
                // ORIGINAL applications, as the reference checker does.
                let recursor_head = |value: &Value| match value {
                    Value::Neutral(Neutral {
                        head: NeutralHead::Const { name, .. }, ..
                    }) => checker.has_certified_recursor_rule(*name),
                    _ => false,
                };
                if delta_policy == DeltaPolicy::GuardedSemanticFallback
                    && remaining >= 16
                    && (recursor_head(cheap_left) || recursor_head(cheap_right))
                {
                    let probe_budget = (remaining / 4).min(128);
                    let mut speculative_work = Vec::new();
                    let mut speculative_proofs = proof_function_frees.clone();
                    let probe_result = compare_values(
                        checker, cheap_left, cheap_right, probe_budget, depth,
                        context, &mut speculative_work, &mut speculative_proofs,
                    );
                    let each_budget = probe_budget / speculative_work.len().max(1);
                    let all_proven = probe_result.is_proven()
                        && speculative_work.iter().all(|(a, b, d, ctx)| {
                            convert_in_context_with_congruence(
                                checker, a, b, each_budget,
                                DeltaPolicy::PreferredOnly, *d, ctx,
                                congruence_depth + 1, congruence_attempts,
                            ).is_proven()
                        });
                    remaining = remaining.saturating_sub(probe_budget * 2);
                    if all_proven {
                        continue;
                    }
                    // Only a successful existing machine transition can
                    // expose constructors. Unresolved majors remain UNKNOWN.
                    let full_left = machine.expose_for_conversion(
                        left.clone(), Transparency::Full, remaining,
                    );
                    let full_right = machine.expose_for_conversion(
                        right.clone(), Transparency::Full, remaining,
                    );
                    let (Some(full_left), Some(full_right)) =
                        (full_left.proven_value(), full_right.proven_value())
                    else {
                        return Judgment::unknown("recursor-transaction-exposure");
                    };
                    match compare_values(
                        checker, full_left, full_right, remaining, depth,
                        context, &mut work, &mut proof_function_frees,
                    ) {
                        Judgment::Proven { .. } => continue,
                        Judgment::Refuted { obstruction } => {
                            return Judgment::Refuted { obstruction };
                        }
                        Judgment::Unknown { residual } => {
                            return Judgment::Unknown { residual };
                        }
                    }
                }
'''
new_conv=old_conv.replace(anchor2,insert+anchor2)
out=Path('evidence-transaction');out.mkdir(exist_ok=True)
manifest={}
patch=[]
for filename,before,after in [('typecheck.rs',old_type,new_type),('convert.rs',old_conv,new_conv)]:
    patch.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),
        fromfile='a/metatron-kernel/src/'+filename,tofile='b/metatron-kernel/src/'+filename))
    (root/filename).write_text(after)
    (out/filename).write_text(after)
    manifest[filename]={'before_sha256':hashlib.sha256(before.encode()).hexdigest(),
                        'after_sha256':hashlib.sha256(after.encode()).hexdigest()}
(out/'candidate.patch').write_text(''.join(patch))
(out/'candidate-source.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,sort_keys=True))
