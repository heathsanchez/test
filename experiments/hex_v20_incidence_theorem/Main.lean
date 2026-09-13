import HexGraphIso.Iso

namespace MathGraph

universe u v

/-- A single k-ary relation on a carrier α. -/
structure KRel (α : Type u) (k : Nat) where
  holds : (Fin k → α) → Prop

/-- Isomorphism of k-ary relational structures. -/
structure SourceIso {α : Type u} {β : Type v} {k : Nat}
    (A : KRel α k) (B : KRel β k) where
  carrier : α ≃ β
  rel : ∀ t, A.holds t ↔ B.holds (fun i => carrier (t i))

/-- Vertices of the abstract identity+occurrence incidence construction. -/
inductive IncNode {α : Type u} {k : Nat} (A : KRel α k)
  | role : α → Fin k → IncNode A
  | anchor : α → IncNode A
  | occ : (t : Fin k → α) → A.holds t → IncNode A

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
  | .occ _ _ => .occurrence

/-- The undirected incidence relation. -/
def Adj : IncNode A → IncNode A → Prop
  | .role a i, .anchor b => a = b
  | .anchor a, .role b _ => a = b
  | .occ t _, .role a i => t i = a
  | .role a i, .occ t _ => a = t i
  | _, _ => False

end IncNode

/-- Color- and adjacency-preserving isomorphism of abstract incidence graphs. -/
structure IncIso {α : Type u} {β : Type v} {k : Nat}
    (A : KRel α k) (B : KRel β k) where
  map : IncNode A ≃ IncNode B
  color : ∀ x, IncNode.color (map x) = IncNode.color x
  adj : ∀ x y, IncNode.Adj (map x) (map y) ↔ IncNode.Adj x y

namespace SourceIso

variable {α : Type u} {β : Type v} {k : Nat}
variable {A : KRel α k} {B : KRel β k}

def mapNode (h : SourceIso A B) : IncNode A → IncNode B
  | .role a i => .role (h.carrier a) i
  | .anchor a => .anchor (h.carrier a)
  | .occ t ht => .occ (fun i => h.carrier (t i)) ((h.rel t).mp ht)

def invNode (h : SourceIso A B) : IncNode B → IncNode A
  | .role b i => .role (h.carrier.symm b) i
  | .anchor b => .anchor (h.carrier.symm b)
  | .occ s hs =>
      let t := fun i => h.carrier.symm (s i)
      have hs' : B.holds (fun i => h.carrier (t i)) := by
        simpa [t] using hs
      .occ t ((h.rel t).mpr hs')

theorem inv_mapNode (h : SourceIso A B) (x : IncNode A) :
    h.invNode (h.mapNode x) = x := by
  cases x with
  | role a i => simp [mapNode, invNode]
  | anchor a => simp [mapNode, invNode]
  | occ t ht =>
      simp only [mapNode, invNode]
      congr
      funext i
      simp

theorem map_invNode (h : SourceIso A B) (x : IncNode B) :
    h.mapNode (h.invNode x) = x := by
  cases x with
  | role b i => simp [mapNode, invNode]
  | anchor b => simp [mapNode, invNode]
  | occ s hs =>
      simp only [mapNode, invNode]
      congr
      funext i
      simp

def nodeEquiv (h : SourceIso A B) : IncNode A ≃ IncNode B where
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
    ∃ b : β, F.map (.anchor a) = .anchor b := by
  have hc := F.color (.anchor a)
  cases h : F.map (.anchor a) with
  | role b i =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | anchor b =>
      exact ⟨b, h⟩
  | occ s hs =>
      rw [h] at hc
      simp [IncNode.color] at hc

noncomputable def anchorMap (F : IncIso A B) (a : α) : β :=
  Classical.choose (F.map_anchor_exists a)

theorem map_anchor_eq (F : IncIso A B) (a : α) :
    F.map (.anchor a) = .anchor (F.anchorMap a) :=
  Classical.choose_spec (F.map_anchor_exists a)

theorem anchor_left (F : IncIso A B) (a : α) :
    F.symm.anchorMap (F.anchorMap a) = a := by
  have h1 := F.map_anchor_eq a
  have h2 := F.symm.map_anchor_eq (F.anchorMap a)
  rw [← h1] at h2
  simp [symm] at h2
  exact IncNode.anchor.inj h2.symm

theorem anchor_right (F : IncIso A B) (b : β) :
    F.anchorMap (F.symm.anchorMap b) = b := by
  have h1 := F.symm.map_anchor_eq b
  have h2 := F.map_anchor_eq (F.symm.anchorMap b)
  rw [← h1] at h2
  simp [symm] at h2
  exact IncNode.anchor.inj h2.symm

noncomputable def anchorEquiv (F : IncIso A B) : α ≃ β where
  toFun := F.anchorMap
  invFun := F.symm.anchorMap
  left_inv := F.anchor_left
  right_inv := F.anchor_right

theorem map_role_eq (F : IncIso A B) (a : α) (i : Fin k) :
    F.map (.role a i) = .role (F.anchorMap a) i := by
  have hc := F.color (.role a i)
  cases h : F.map (.role a i) with
  | role b j =>
      rw [h] at hc
      have hij : j = i := by
        simpa [IncNode.color] using IncColor.role.inj hc
      subst j
      have ha : IncNode.Adj (.role a i : IncNode A) (.anchor a) := by
        simp [IncNode.Adj]
      have hb : IncNode.Adj (F.map (.role a i)) (F.map (.anchor a)) :=
        (F.adj (.role a i) (.anchor a)).2 ha
      rw [h, F.map_anchor_eq] at hb
      have hba : b = F.anchorMap a := by
        simpa [IncNode.Adj] using hb
      subst b
      rfl
  | anchor b =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | occ s hs =>
      rw [h] at hc
      simp [IncNode.color] at hc

theorem map_occ_exists (F : IncIso A B) (t : Fin k → α) (ht : A.holds t) :
    ∃ s (hs : B.holds s), F.map (.occ t ht) = .occ s hs := by
  have hc := F.color (.occ t ht)
  cases h : F.map (.occ t ht) with
  | role b i =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | anchor b =>
      rw [h] at hc
      simp [IncNode.color] at hc
  | occ s hs =>
      exact ⟨s, hs, h⟩

theorem relation_forward (F : IncIso A B) (t : Fin k → α) :
    A.holds t → B.holds (fun i => F.anchorEquiv (t i)) := by
  intro ht
  rcases F.map_occ_exists t ht with ⟨s, hs, hmap⟩
  have hs_eq : s = fun i => F.anchorEquiv (t i) := by
    funext i
    have ha : IncNode.Adj (.occ t ht : IncNode A) (.role (t i) i) := by
      simp [IncNode.Adj]
    have hb : IncNode.Adj (F.map (.occ t ht)) (F.map (.role (t i) i)) :=
      (F.adj (.occ t ht) (.role (t i) i)).2 ha
    rw [hmap, F.map_role_eq] at hb
    simpa [IncNode.Adj, anchorEquiv] using hb
  rw [hs_eq] at hs
  exact hs

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
