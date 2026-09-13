import Std

namespace MathGraph

universe u v w

structure Bijection (α : Type u) (β : Type v) where
  toFun : α → β
  invFun : β → α
  left_inv : ∀ x, invFun (toFun x) = x
  right_inv : ∀ y, toFun (invFun y) = y

instance {α : Type u} {β : Type v} : CoeFun (Bijection α β) (fun _ => α → β) :=
  ⟨Bijection.toFun⟩

namespace Bijection

variable {α : Type u} {β : Type v}

def symm (e : Bijection α β) : Bijection β α where
  toFun := e.invFun
  invFun := e.toFun
  left_inv := e.right_inv
  right_inv := e.left_inv

@[simp] theorem symm_apply_apply (e : Bijection α β) (x : α) :
    e.symm (e x) = x := e.left_inv x

@[simp] theorem apply_symm_apply (e : Bijection α β) (y : β) :
    e (e.symm y) = y := e.right_inv y

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

end Bijection

/-- A relation-position key: a relation symbol together with one of its argument positions. -/
abbrev RoleKey (σ : Type w) (arity : σ → Nat) :=
  Sigma fun r => Fin (arity r)

/-- An arbitrary relational structure over a possibly heterogeneous signature. -/
structure RelStruct (σ : Type w) (arity : σ → Nat) (α : Type u) where
  holds : (r : σ) → (Fin (arity r) → α) → Prop

/-- Isomorphism of relational structures: one carrier bijection transports every relation. -/
structure SourceIso {σ : Type w} {arity : σ → Nat}
    {α : Type u} {β : Type v}
    (A : RelStruct σ arity α) (B : RelStruct σ arity β) where
  carrier : Bijection α β
  rel : ∀ r t, A.holds r t ↔ B.holds r (fun i => carrier (t i))

/-- Identity-anchor + tuple-occurrence incidence vertices. -/
inductive IncNode {σ : Type w} {arity : σ → Nat} {α : Type u}
    (A : RelStruct σ arity α)
  | role : α → RoleKey σ arity → IncNode A
  | anchor : α → IncNode A
  | occ : (r : σ) → {t : Fin (arity r) → α // A.holds r t} → IncNode A

/-- Colors remember exact relation-position roles and exact relation symbols. -/
inductive IncColor (σ : Type w) (arity : σ → Nat)
  | role : RoleKey σ arity → IncColor σ arity
  | anchor : IncColor σ arity
  | occurrence : σ → IncColor σ arity

namespace IncNode

variable {σ : Type w} {arity : σ → Nat}
variable {α : Type u} {A : RelStruct σ arity α}

def color : IncNode A → IncColor σ arity
  | .role _ key => .role key
  | .anchor _ => .anchor
  | .occ r _ => .occurrence r

/-- Undirected incidence:
role copies tie to a common carrier anchor;
relation occurrences tie to the role copy at every argument position. -/
def Adj : IncNode A → IncNode A → Prop
  | .role a _, .anchor b => a = b
  | .anchor a, .role b _ => a = b
  | .occ r q, .role a key =>
      ∃ i : Fin (arity r), key = ⟨r, i⟩ ∧ q.1 i = a
  | .role a key, .occ r q =>
      ∃ i : Fin (arity r), key = ⟨r, i⟩ ∧ a = q.1 i
  | _, _ => False

end IncNode

/-- Color- and adjacency-preserving incidence isomorphism. -/
structure IncIso {σ : Type w} {arity : σ → Nat}
    {α : Type u} {β : Type v}
    (A : RelStruct σ arity α) (B : RelStruct σ arity β) where
  map : Bijection (IncNode A) (IncNode B)
  color : ∀ x, IncNode.color (map x) = IncNode.color x
  adj : ∀ x y, IncNode.Adj (map x) (map y) ↔ IncNode.Adj x y

namespace SourceIso

variable {σ : Type w} {arity : σ → Nat}
variable {α : Type u} {β : Type v}
variable {A : RelStruct σ arity α} {B : RelStruct σ arity β}

def mapNode (h : SourceIso A B) : IncNode A → IncNode B
  | .role a key => .role (h.carrier a) key
  | .anchor a => .anchor (h.carrier a)
  | .occ r q =>
      .occ r ⟨fun i => h.carrier (q.1 i), (h.rel r q.1).mp q.2⟩

def invNode (h : SourceIso A B) : IncNode B → IncNode A
  | .role b key => .role (h.carrier.symm b) key
  | .anchor b => .anchor (h.carrier.symm b)
  | .occ r q =>
      let t := fun i => h.carrier.symm (q.1 i)
      have hb : B.holds r (fun i => h.carrier (t i)) := by
        simpa [t] using q.2
      .occ r ⟨t, (h.rel r t).mpr hb⟩

theorem inv_mapNode (h : SourceIso A B) (x : IncNode A) :
    h.invNode (h.mapNode x) = x := by
  cases x with
  | role a key => simp [mapNode, invNode]
  | anchor a => simp [mapNode, invNode]
  | occ r q =>
      cases q with
      | mk t ht =>
          simp only [mapNode, invNode]
          congr
          funext i
          simp

theorem map_invNode (h : SourceIso A B) (x : IncNode B) :
    h.mapNode (h.invNode x) = x := by
  cases x with
  | role b key => simp [mapNode, invNode]
  | anchor b => simp [mapNode, invNode]
  | occ r q =>
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
  cases x <;> cases y <;> simp [mapNode, IncNode.Adj]

def toIncIso (h : SourceIso A B) : IncIso A B where
  map := h.nodeEquiv
  color := h.mapNode_color
  adj := h.mapNode_adj

end SourceIso

namespace IncIso

variable {σ : Type w} {arity : σ → Nat}
variable {α : Type u} {β : Type v}
variable {A : RelStruct σ arity α} {B : RelStruct σ arity β}

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
  | role b key =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | anchor b =>
      exact ⟨b, rfl⟩
  | occ r q =>
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

theorem map_role_eq (F : IncIso A B) (a : α) (key : RoleKey σ arity) :
    F.map (IncNode.role a key) = IncNode.role (F.anchorMap a) key := by
  have hc := F.color (IncNode.role a key)
  cases h : F.map (IncNode.role a key) with
  | role b key' =>
      rw [h] at hc
      have hk : key' = key := by
        injection hc
      subst key'
      have ha : IncNode.Adj (IncNode.role a key : IncNode A) (IncNode.anchor a) := by
        simp [IncNode.Adj]
      have hb : IncNode.Adj (F.map (IncNode.role a key)) (F.map (IncNode.anchor a)) :=
        (F.adj (IncNode.role a key) (IncNode.anchor a)).2 ha
      rw [h, F.map_anchor_eq] at hb
      have hba : b = F.anchorMap a := by
        simpa [IncNode.Adj] using hb
      subst b
      rfl
  | anchor b =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | occ r q =>
      rw [h] at hc
      simp [IncNode.color] at hc

theorem map_occ_exists (F : IncIso A B)
    (r : σ) (t : Fin (arity r) → α) (ht : A.holds r t) :
    ∃ q : {s : Fin (arity r) → β // B.holds r s},
      F.map (IncNode.occ r ⟨t, ht⟩) = IncNode.occ r q := by
  have hc := F.color (IncNode.occ r ⟨t, ht⟩)
  cases h : F.map (IncNode.occ r ⟨t, ht⟩) with
  | role b key =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | anchor b =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | occ r' q =>
      rw [h] at hc
      have hr : r' = r := by
        injection hc
      subst r'
      exact ⟨q, rfl⟩

theorem relation_forward (F : IncIso A B)
    (r : σ) (t : Fin (arity r) → α) :
    A.holds r t → B.holds r (fun i => F.anchorEquiv (t i)) := by
  intro ht
  rcases F.map_occ_exists r t ht with ⟨q, hmap⟩
  have hq_eq : q.1 = fun i => F.anchorEquiv (t i) := by
    funext i
    let key : RoleKey σ arity := ⟨r, i⟩
    have ha : IncNode.Adj (IncNode.occ r ⟨t, ht⟩ : IncNode A)
        (IncNode.role (t i) key) := by
      exact ⟨i, rfl, rfl⟩
    have hb : IncNode.Adj (F.map (IncNode.occ r ⟨t, ht⟩))
        (F.map (IncNode.role (t i) key)) :=
      (F.adj (IncNode.occ r ⟨t, ht⟩) (IncNode.role (t i) key)).2 ha
    rw [hmap, F.map_role_eq] at hb
    rcases hb with ⟨j, hj, hval⟩
    change (⟨r, i⟩ : RoleKey σ arity) = ⟨r, j⟩ at hj
    cases hj
    simpa [anchorEquiv] using hval
  rw [← hq_eq]
  exact q.2

noncomputable def toSourceIso (F : IncIso A B) : SourceIso A B where
  carrier := F.anchorEquiv
  rel := by
    intro r t
    constructor
    · exact F.relation_forward r t
    · intro hb
      have hback := F.symm.relation_forward r (fun i => F.anchorEquiv (t i)) hb
      have hfun :
          (fun i => F.symm.anchorEquiv (F.anchorEquiv (t i))) = t := by
        funext i
        change F.symm.anchorMap (F.anchorMap (t i)) = t i
        exact F.anchor_left (t i)
      rw [hfun] at hback
      exact hback

end IncIso

/--
For any relational signature (even an infinite symbol type) with arbitrary
finite arity per symbol, the identity-anchor + occurrence-incidence
construction preserves and reflects isomorphism.
-/
theorem sourceIso_iff_incIso
    {σ : Type w} {arity : σ → Nat}
    {α : Type u} {β : Type v}
    (A : RelStruct σ arity α) (B : RelStruct σ arity β) :
    Nonempty (SourceIso A B) ↔ Nonempty (IncIso A B) := by
  constructor
  · rintro ⟨h⟩
    exact ⟨h.toIncIso⟩
  · rintro ⟨h⟩
    exact ⟨h.toSourceIso⟩

end MathGraph
