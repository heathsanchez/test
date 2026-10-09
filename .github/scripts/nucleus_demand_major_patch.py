#!/usr/bin/env python3
"""Candidate follow-up to the transactional probe regression.

Uses the existing admitted iota tables. The continuation forces only an
actual major expression, never inferring an input constructor from outputs.
A bounded transition allowance and cycle rejection preserve UNKNOWN.
"""
from pathlib import Path
import difflib,hashlib,json
root=Path('metatron-kernel/src');out=Path('evidence-transaction')
before=(root/'machine.rs').read_text();after=before
anchor='''pub enum Transparency {
    Opaque,
    Reducible,
    Full,
}'''
assert after.count(anchor)==1
after=after.replace(anchor,'''pub enum Transparency {
    Opaque,
    Reducible,
    Full,
    // Full delta, but majors are handled by the explicit demand stack.
    Demand,
}''')
anchor='        Transparency::Full => true,'
assert after.count(anchor)==1
after=after.replace(anchor,'        Transparency::Full | Transparency::Demand => true,')
anchor='    fn constructor_application(&self, target: &Closure) -> Option<(NameId, Vec<Closure>)> {'
assert after.count(anchor)==1
method='''    /// Normalize the dependency chain needed for a certified iota step.
    /// Unlike bounded nested head probes, this retains each pending recursor
    /// while its major is evaluated, without expanding unrelated fields.
    pub(crate) fn expose_demand_for_conversion(
        &self, root: Closure, budget: usize,
    ) -> Judgment<Value> {
        let mut remaining = budget;
        let mut waiting: Vec<(Neutral, Closure)> = Vec::new();
        let mut active: HashSet<Closure> = HashSet::new();
        let mut memo: HashMap<Closure, Value> = HashMap::new();
        let expose = |term: Closure, pending: Vec<Closure>, remaining: &mut usize| {
            if *remaining == 0 {
                return Judgment::unknown("demand-transition-budget");
            }
            let result = self.expose_internal_with_pending(
                term, Transparency::Demand, (*remaining).min(256), true, true, pending,
            );
            match result {
                Judgment::Proven { value, .. } => {
                    let cost = value.transitions.len().saturating_add(1);
                    *remaining = remaining.saturating_sub(cost);
                    Judgment::proven(value.value, "demand-certified-machine-step")
                }
                Judgment::Refuted { obstruction } => Judgment::Refuted { obstruction },
                Judgment::Unknown { residual } => Judgment::Unknown { residual },
            }
        };
        let initial = expose(root, Vec::new(), &mut remaining);
        let Some(mut value) = initial.proven_value().cloned() else { return initial; };
        loop {
            if remaining == 0 {
                return Judgment::unknown("demand-transition-budget");
            }
            remaining -= 1;
            if let Value::Neutral(neutral) = &value
                && let NeutralHead::Const { name, levels } = &neutral.head
                && let Some(reduction) = self.recursor_reductions.get(name)
            {
                let major_index = reduction.num_params + 1
                    + reduction.rules.len() + reduction.num_indices;
                if levels.len() != reduction.level_params.len() || neutral.spine.len() <= major_index {
                    return Judgment::unknown("demand-unsaturated-recursor");
                }
                let major = neutral.spine[major_index].clone();
                waiting.push((neutral.clone(), major.clone()));
                if let Some(known) = memo.get(&major).cloned() {
                    value = known;
                } else {
                    if !active.insert(major.clone()) {
                        return Judgment::unknown("demand-major-cycle");
                    }
                    let result = expose(major, Vec::new(), &mut remaining);
                    let Some(next) = result.proven_value().cloned() else { return result; };
                    value = next;
                    continue;
                }
            }
            let Some((parent, major)) = waiting.pop() else {
                return Judgment::proven(value, "demand-major-normal-form");
            };
            active.remove(&major);
            memo.insert(major, value.clone());
            let NeutralHead::Const { name, levels } = &parent.head else {
                return Judgment::unknown("demand-parent-not-recursor");
            };
            let Some(reduction) = self.recursor_reductions.get(name) else {
                return Judgment::unknown("demand-missing-authority");
            };
            let (constructor, fields) = match &value {
                Value::Neutral(Neutral { head: NeutralHead::Const { name, .. }, spine }) => {
                    (*name, spine.clone())
                }
                Value::NatLit(number) => {
                    let Some(nat) = &self.nat_primitives else {
                        return Judgment::unknown("demand-numeral-without-authority");
                    };
                    if number.is_zero() {
                        (nat.zero, Vec::new())
                    } else {
                        let Some(pred) = number.pred() else {
                            return Judgment::unknown("demand-numeral-predecessor");
                        };
                        let Some(id) = self.expressions.iter_raw().find_map(|(id,e)| {
                            matches!(e, Expr::NatLit(n) if *n == pred).then_some(ExprId(id))
                        }) else {
                            return Judgment::unknown("demand-missing-predecessor-expression");
                        };
                        (nat.succ, vec![Closure::new(id, EnvFrame::empty())])
                    }
                }
                _ => return Judgment::unknown("demand-major-not-constructor"),
            };
            let Some(rule) = reduction.rules.iter().find(|r| {
                r.constructor == constructor && fields.len() == r.num_params + r.num_fields
            }) else {
                return Judgment::unknown("demand-major-not-registered-constructor");
            };
            let prefix = reduction.num_params + 1 + reduction.rules.len();
            let required = prefix + reduction.num_indices + 1;
            let mut args = parent.spine[..prefix].to_vec();
            args.extend_from_slice(&fields[rule.num_params..]);
            let pending = parent.spine[required..].iter().rev().cloned()
                .chain(args.into_iter().rev()).collect();
            let substitution = LevelSubstitution::new(reduction.level_params.iter().copied()
                .zip(levels.iter().cloned()).collect());
            let next = expose(Closure::with_levels(rule.rhs,EnvFrame::empty(),substitution),
                pending,&mut remaining);
            let Some(next) = next.proven_value().cloned() else { return next; };
            value = next;
        }
    }

'''
after=after.replace(anchor,method+anchor)
(root/'machine.rs').write_text(after)
conv=(root/'convert.rs').read_text()
old='''                    let full_left = machine.expose_for_conversion(
                        left.clone(), Transparency::Full, remaining,
                    );
                    let full_right = machine.expose_for_conversion(
                        right.clone(), Transparency::Full, remaining,
                    );'''
new='''                    let force = |term: Closure| {
                        let candidate = machine.expose_demand_for_conversion(term.clone(), remaining);
                        if candidate.is_proven() {
                            candidate
                        } else {
                            // Unresolved normalization must not erase an
                            // independently available K or rigid rejection.
                            machine.expose_for_conversion(term, Transparency::Full, remaining)
                        }
                    };
                    let full_left = force(left.clone());
                    let full_right = force(right.clone());'''
assert conv.count(old)==1
newconv=conv.replace(old,new)
(root/'convert.rs').write_text(newconv)
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/machine.rs',tofile='b/machine.rs'))
patch+=''.join(difflib.unified_diff(conv.splitlines(True),newconv.splitlines(True),fromfile='a/convert.rs',tofile='b/convert.rs'))
(out/'demand-followup.patch').write_text(patch)
for name in ['machine.rs','convert.rs','typecheck.rs']:
    (out/name).write_bytes((root/name).read_bytes())
(out/'tested-source-hashes.json').write_text(json.dumps({name:hashlib.sha256((root/name).read_bytes()).hexdigest()
    for name in ['machine.rs','convert.rs','typecheck.rs']},indent=2))
