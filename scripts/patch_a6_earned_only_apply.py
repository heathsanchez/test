from pathlib import Path
import argparse

ap=argparse.ArgumentParser()
ap.add_argument('--mode',choices=('earned','raw'),required=True)
args=ap.parse_args()

p=Path('a6/src/eval.rs')
s=p.read_text()

old="""            Value::Rigid { head, spine , ..} => {
                let head_copy = *head;
                if self.nat_extension {
                    if let RigidHead::Ctor(name, _) = head_copy {
                        if Some(name) == self.ctx.export_file.name_cache.nat_succ {
                            let new_spine = value::spine_snoc(self.arena, spine, Elim::app(a));
                            return self.try_fire_rigid(depth, head_copy, new_spine);
                        }
                    }
                }
                let a = self.canonicalize_for_spine(a);
                let new_spine = self.spine_snoc_hc(spine, Elim::app(a));
                self.mk_rigid_hc(head_copy, new_spine)
            }
"""
if args.mode=='earned':
    new="""            Value::Rigid { head, spine , ..} => {
                let head_copy = *head;
                if self.nat_extension {
                    if let RigidHead::Ctor(name, _) = head_copy {
                        if Some(name) == self.ctx.export_file.name_cache.nat_succ {
                            let new_spine = value::spine_snoc(self.arena, spine, Elim::app(a));
                            return self.try_fire_rigid(depth, head_copy, new_spine);
                        }
                    }
                }
                let ca = if a.is_canonical() {
                    Some(a)
                } else {
                    let raw = a as *const Value<'t> as usize;
                    self.tc_cache.canon_cache.get(&raw).copied()
                };
                if let Some(a) = ca {
                    let new_spine = self.spine_snoc_hc(spine, Elim::app(a));
                    self.mk_rigid_hc(head_copy, new_spine)
                } else {
                    let new_spine = value::spine_snoc(self.arena, spine, Elim::app(a));
                    value::mk_rigid(self.arena, head_copy, new_spine)
                }
            }
"""
else:
    new="""            Value::Rigid { head, spine , ..} => {
                let head_copy = *head;
                if self.nat_extension {
                    if let RigidHead::Ctor(name, _) = head_copy {
                        if Some(name) == self.ctx.export_file.name_cache.nat_succ {
                            let new_spine = value::spine_snoc(self.arena, spine, Elim::app(a));
                            return self.try_fire_rigid(depth, head_copy, new_spine);
                        }
                    }
                }
                let new_spine = value::spine_snoc(self.arena, spine, Elim::app(a));
                value::mk_rigid(self.arena, head_copy, new_spine)
            }
"""
assert old in s
s=s.replace(old,new,1)

old="""            Value::Unfold { head, spine, head_value, .. } => {
                let head = *head;
                let head_value = *head_value;
                let spine = *spine;
                if self.nat_extension && self.is_nat_red_name(head.name) {
                    let new_spine = self.spine_snoc_hc(spine, Elim::app(a));
                    if let Some(args) = self.spine_apps(depth, new_spine) {
                        if let Some(r) = self.do_nat_red_shallow(depth, head.name, &args) {
                            return r;
                        }
                    }
                    return self.mk_unfold_hc(head.name, head.levels, new_spine, head_value);
                }
                let a = self.canonicalize_for_spine(a);
                let new_spine = self.spine_snoc_hc(spine, Elim::app(a));
                self.mk_unfold_hc(head.name, head.levels, new_spine, head_value)
            }
"""
if args.mode=='earned':
    new="""            Value::Unfold { head, spine, head_value, .. } => {
                let head = *head;
                let head_value = *head_value;
                let spine = *spine;
                if self.nat_extension && self.is_nat_red_name(head.name) {
                    let new_spine = self.spine_snoc_hc(spine, Elim::app(a));
                    if let Some(args) = self.spine_apps(depth, new_spine) {
                        if let Some(r) = self.do_nat_red_shallow(depth, head.name, &args) {
                            return r;
                        }
                    }
                    return self.mk_unfold_hc(head.name, head.levels, new_spine, head_value);
                }
                let ca = if a.is_canonical() {
                    Some(a)
                } else {
                    let raw = a as *const Value<'t> as usize;
                    self.tc_cache.canon_cache.get(&raw).copied()
                };
                if let Some(a) = ca {
                    let new_spine = self.spine_snoc_hc(spine, Elim::app(a));
                    self.mk_unfold_hc(head.name, head.levels, new_spine, head_value)
                } else {
                    let new_spine = value::spine_snoc(self.arena, spine, Elim::app(a));
                    value::mk_unfold(self.arena, head.name, head.levels, new_spine, head_value)
                }
            }
"""
else:
    new="""            Value::Unfold { head, spine, head_value, .. } => {
                let head = *head;
                let head_value = *head_value;
                let spine = *spine;
                if self.nat_extension && self.is_nat_red_name(head.name) {
                    let new_spine = self.spine_snoc_hc(spine, Elim::app(a));
                    if let Some(args) = self.spine_apps(depth, new_spine) {
                        if let Some(r) = self.do_nat_red_shallow(depth, head.name, &args) {
                            return r;
                        }
                    }
                    return self.mk_unfold_hc(head.name, head.levels, new_spine, head_value);
                }
                let new_spine = value::spine_snoc(self.arena, spine, Elim::app(a));
                value::mk_unfold(self.arena, head.name, head.levels, new_spine, head_value)
            }
"""
assert old in s
s=s.replace(old,new,1)

p.write_text(s)
