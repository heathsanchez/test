structure CertifiedAdapter where
  domain : Nat
  complete : Prop
  sound : complete

structure Retained where
  depth : Nat
  warranted : Prop
  proof : warranted

inductive Revision : Retained → Retained → Prop
  | preserve (s : Retained) : Revision s s

theorem noUnlicensedRevision {a b : Retained} (h : Revision a b) :
    a = b := by cases h; rfl

theorem adapterPremise (a : CertifiedAdapter) : a.complete := a.sound
