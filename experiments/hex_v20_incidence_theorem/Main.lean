import HexGraphIso.Iso

namespace MathGraph

universe u v w

/-- A small explicit bijection type, avoiding any external equivalence library. -/
structure Bijection (α : Type u) (β : Type v) where
  toFun : α → β
  invFun : β → α
  left_inv : ∀ x, invFun (toFun x) = x
  right_inv : ∀ y, toFun (invFun y) = y

instance {α : Type u} {β : Type v} : CoeFun (Bijection α β) (fun _ => α → β) :=
  ⟨Bijection.toFun⟩

namespace Bijection

variable {α : Type u} {β : Type v} {γ : Type w}

def symm (e : Bijection α β) : Bijection β α where
  toFun := e.invFun
  invFun := e.toFun
  left_inv := e.right_inv
  right_inv := e.left_inv

@[simp] theorem symm_apply_apply (e : Bijection α β) (x : α) :
    e.symm (e x) = x :=
  e.left_inv x

@[simp] theorem apply_symm_apply (e : Bijection α β) (y : β) :
    e (e.symm y) = y :=
  e.right_inv y

theorem injective (e : Bijection α β) : Function.Injective e := by
  intro x y h
  calc
    x = e.invFun (e x) := (e.left_inv x).symm
    _ = e.invFun (e y) := congrArg e.invFun h
    _ = y := e.left_inv y

@[simp] theorem apply_eq_apply_iff (e : Bijection α β) {x y : α} :
    e x = e y ↔ x = y := by
  constructor
  · intro h
    exact e.injective h
  · intro h
    exact congrArg e h

theorem surjective (e : Bijection α β) : Function.Surjective e := by
  intro y
  exact ⟨e.symm y, e.apply_symm_apply y⟩

end Bijection

/-- A single k-ary relation on a carrier α. -/
structure KRel (α : Type u) (k : Nat) where
  holds : (Fin k → α) → Prop

/-- Isomorphism of k-ary relational structures. -/
structure SourceIso {α : Type u} {β : Type v} {k : Nat}
    (A : KRel α k) (B : KRel β k) where
  carrier : Bijection α β
  rel : ∀ t, A.holds t ↔ B.holds (fun i => carrier (t i))

/-- Vertices of the abstract identity+occurrence incidence construction. -/
inductive IncNode {α : Type u} {k : Nat} (A : KRel α k)
  | role : α → Fin k → IncNode A
  | anchor : α → IncNode A
  | occ : {t : Fin k → α // A.holds t} → IncNode A

/-- Ordered colors in the incidence construction. -/
inductive IncColor (k : Nat)
  | role : Fin k → IncColor k
  | anchor : IncColor k
  | occurrence : IncColor k

namespace IncNode

variable {α : Type u} {k : Nat} {A : KRel α k}

def color : IncNode A → IncColor k
  | .role _ i => .role i
  | .anchor _ => .anchor
  | .occ _ => .occurrence

/-- The undirected incidence relation. -/
def Adj : IncNode A → IncNode A → Prop
  | .role a _, .anchor b => a = b
  | .anchor a, .role b _ => a = b
  | .occ q, .role a i => q.1 i = a
  | .role a i, .occ q => a = q.1 i
  | _, _ => False

end IncNode

/-- Color- and adjacency-preserving isomorphism of abstract incidence graphs. -/
structure IncIso {α : Type u} {β : Type v} {k : Nat}
    (A : KRel α k) (B : KRel β k) where
  map : Bijection (IncNode A) (IncNode B)
  color : ∀ x, IncNode.color (map x) = IncNode.color x
  adj : ∀ x y, IncNode.Adj (map x) (map y) ↔ IncNode.Adj x y

namespace SourceIso

variable {α : Type u} {β : Type v} {k : Nat}
variable {A : KRel α k} {B : KRel β k}

def mapNode (h : SourceIso A B) : IncNode A → IncNode B
  | .role a i => .role (h.carrier a) i
  | .anchor a => .anchor (h.carrier a)
  | .occ q =>
      .occ ⟨fun i => h.carrier (q.1 i), (h.rel q.1).mp q.2⟩

def invNode (h : SourceIso A B) : IncNode B → IncNode A
  | .role b i => .role (h.carrier.symm b) i
  | .anchor b => .anchor (h.carrier.symm b)
  | .occ q =>
      let t := fun i => h.carrier.symm (q.1 i)
      have hb : B.holds (fun i => h.carrier (t i)) := by
        simpa [t] using q.2
      .occ ⟨t, (h.rel t).mpr hb⟩

theorem inv_mapNode (h : SourceIso A B) (x : IncNode A) :
    h.invNode (h.mapNode x) = x := by
  cases x with
  | role a i => simp [mapNode, invNode]
  | anchor a => simp [mapNode, invNode]
  | occ q =>
      cases q with
      | mk t ht =>
          simp only [mapNode, invNode]
          congr
          funext i
          simp

theorem map_invNode (h : SourceIso A B) (x : IncNode B) :
    h.mapNode (h.invNode x) = x := by
  cases x with
  | role b i => simp [mapNode, invNode]
  | anchor b => simp [mapNode, invNode]
  | occ q =>
      cases q with
      | mk s hs =>
          simp only [mapNode, invNode]
          congr
          funext i
          simp

def nodeEquiv (h : SourceIso A B) : Bijection (IncNode A) (IncNode B) where
  toFun := h.mapNode
  invFun := h.invNode
  left_inv := h.inv_mapNode
  right_inv := h.map_invNode

theorem mapNode_color (h : SourceIso A B) (x : IncNode A) :
    IncNode.color (h.mapNode x) = IncNode.color x := by
  cases x <;> rfl

theorem mapNode_adj (h : SourceIso A B) (x y : IncNode A) :
    IncNode.Adj (h.mapNode x) (h.mapNode y) ↔ IncNode.Adj x y := by
  cases x <;> cases y <;> simp [mapNode, IncNode.Adj, Bijection.injective]

def toIncIso (h : SourceIso A B) : IncIso A B where
  map := h.nodeEquiv
  color := h.mapNode_color
  adj := h.mapNode_adj

end SourceIso

namespace IncIso

variable {α : Type u} {β : Type v} {k : Nat}
variable {A : KRel α k} {B : KRel β k}

def symm (F : IncIso A B) : IncIso B A where
  map := F.map.symm
  color := by
    intro y
    have h := F.color (F.map.symm y)
    simpa using h.symm
  adj := by
    intro x y
    have h := F.adj (F.map.symm x) (F.map.symm y)
    simpa using h.symm

theorem map_anchor_exists (F : IncIso A B) (a : α) :
    ∃ b : β, F.map (IncNode.anchor a) = IncNode.anchor b := by
  have hc := F.color (IncNode.anchor a)
  cases h : F.map (IncNode.anchor a) with
  | role b i =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | anchor b =>
      exact ⟨b, rfl⟩
  | occ q =>
      rw [h] at hc
      simp [IncNode.color] at hc

noncomputable def anchorMap (F : IncIso A B) (a : α) : β :=
  Classical.choose (F.map_anchor_exists a)

theorem map_anchor_eq (F : IncIso A B) (a : α) :
    F.map (IncNode.anchor a) = IncNode.anchor (F.anchorMap a) :=
  Classical.choose_spec (F.map_anchor_exists a)

theorem anchor_left (F : IncIso A B) (a : α) :
    F.symm.anchorMap (F.anchorMap a) = a := by
  have h1 := F.map_anchor_eq a
  have h2 := F.symm.map_anchor_eq (F.anchorMap a)
  change F.map.symm (IncNode.anchor (F.anchorMap a)) =
      IncNode.anchor (F.symm.anchorMap (F.anchorMap a)) at h2
  rw [← h1] at h2
  simp at h2
  exact h2.symm

theorem anchor_right (F : IncIso A B) (b : β) :
    F.anchorMap (F.symm.anchorMap b) = b := by
  have h1 := F.symm.map_anchor_eq b
  have h2 := F.map_anchor_eq (F.symm.anchorMap b)
  change F.map.symm (IncNode.anchor b) =
      IncNode.anchor (F.symm.anchorMap b) at h1
  rw [← h1] at h2
  simp at h2
  exact h2.symm

noncomputable def anchorEquiv (F : IncIso A B) : Bijection α β where
  toFun := F.anchorMap
  invFun := F.symm.anchorMap
  left_inv := F.anchor_left
  right_inv := F.anchor_right

theorem map_role_eq (F : IncIso A B) (a : α) (i : Fin k) :
    F.map (IncNode.role a i) = IncNode.role (F.anchorMap a) i := by
  have hc := F.color (IncNode.role a i)
  cases h : F.map (IncNode.role a i) with
  | role b j =>
      rw [h] at hc
      have hij : j = i := by
        injection hc
      subst j
      have ha : IncNode.Adj (IncNode.role a i : IncNode A) (IncNode.anchor a) := by
        simp [IncNode.Adj]
      have hb : IncNode.Adj (F.map (IncNode.role a i)) (F.map (IncNode.anchor a)) :=
        (F.adj (IncNode.role a i) (IncNode.anchor a)).2 ha
      rw [h, F.map_anchor_eq] at hb
      have hba : b = F.anchorMap a := by
        simpa [IncNode.Adj] using hb
      subst b
      rfl
  | anchor b =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | occ q =>
      rw [h] at hc
      simp [IncNode.color] at hc

theorem map_occ_exists (F : IncIso A B) (t : Fin k → α) (ht : A.holds t) :
    ∃ q : {s : Fin k → β // B.holds s},
      F.map (IncNode.occ ⟨t, ht⟩) = IncNode.occ q := by
  have hc := F.color (IncNode.occ ⟨t, ht⟩)
  cases h : F.map (IncNode.occ ⟨t, ht⟩) with
  | role b i =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | anchor b =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | occ q =>
      exact ⟨q, rfl⟩

theorem relation_forward (F : IncIso A B) (t : Fin k → α) :
    A.holds t → B.holds (fun i => F.anchorEquiv (t i)) := by
  intro ht
  rcases F.map_occ_exists t ht with ⟨q, hmap⟩
  have hq_eq : q.1 = fun i => F.anchorEquiv (t i) := by
    funext i
    have ha : IncNode.Adj (IncNode.occ ⟨t, ht⟩ : IncNode A)
        (IncNode.role (t i) i) := by
      simp [IncNode.Adj]
    have hb : IncNode.Adj (F.map (IncNode.occ ⟨t, ht⟩))
        (F.map (IncNode.role (t i) i)) :=
      (F.adj (IncNode.occ ⟨t, ht⟩) (IncNode.role (t i) i)).2 ha
    rw [hmap, F.map_role_eq] at hb
    simpa [IncNode.Adj, anchorEquiv] using hb
  rw [← hq_eq]
  exact q.2

noncomputable def toSourceIso (F : IncIso A B) : SourceIso A B where
  carrier := F.anchorEquiv
  rel := by
    intro t
    constructor
    · exact F.relation_forward t
    · intro hb
      have hback := F.symm.relation_forward (fun i => F.anchorEquiv (t i)) hb
      have hfun :
          (fun i => F.symm.anchorEquiv (F.anchorEquiv (t i))) = t := by
        funext i
        change F.symm.anchorMap (F.anchorMap (t i)) = t i
        exact F.anchor_left (t i)
      rw [hfun] at hback
      exact hback

end IncIso

/--
The identity-anchor + tuple-occurrence incidence construction preserves and
reflects isomorphism for arbitrary carrier types and arbitrary finite arity.
-/
theorem sourceIso_iff_incIso
    {α : Type u} {β : Type v} {k : Nat}
    (A : KRel α k) (B : KRel β k) :
    Nonempty (SourceIso A B) ↔ Nonempty (IncIso A B) := by
  constructor
  · rintro ⟨h⟩
    exact ⟨h.toIncIso⟩
  · rintro ⟨h⟩
    exact ⟨h.toSourceIso⟩

end MathGraph
