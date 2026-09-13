import HexGraphIso.Iso

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


/--
A finite colored simple graph presented on an arbitrary vertex type V,
together with an explicit numbering by Fin n.
-/
structure FiniteColored (V : Type u) (n k : Nat) where
  number : Bijection V (Fin n)
  color : V → Fin k
  color_onto : Function.Surjective color
  adj : V → V → Bool
  adj_symm : ∀ u v, adj u v = adj v u
  adj_loopless : ∀ u, adj u u = false

namespace FiniteColored

open Hex Hex.GraphIso

variable {V : Type u} {W : Type v} {n k : Nat}

/-- Compile an explicitly numbered finite colored graph to Hex. -/
def toHex (A : FiniteColored V n k) : Colored n k where
  graph :=
    Graph.ofAdj
      (fun i j => A.adj (A.number.symm i) (A.number.symm j))
      (fun i j => by
        exact A.adj_symm (A.number.symm i) (A.number.symm j))
      (fun i => A.adj_loopless (A.number.symm i))
  coloring :=
    { cells := Hex.Vector.ofFn' fun i => A.color (A.number.symm i)
      onto := by
        intro c
        rcases A.color_onto c with ⟨v, hv⟩
        refine ⟨A.number v, ?_⟩
        rw [Hex.Vector.get_eq_getElem]
        simp [hv] }

@[simp] theorem toHex_adj (A : FiniteColored V n k) (i j : Fin n) :
    A.toHex.graph.adj i j = A.adj (A.number.symm i) (A.number.symm j) := by
  simp [toHex]

@[simp] theorem toHex_color (A : FiniteColored V n k) (i : Fin n) :
    A.toHex.coloring.cells[i] = A.color (A.number.symm i) := by
  simp [toHex]

end FiniteColored

/-- Isomorphism before compilation to Hex. -/
structure FiniteColoredIso
    {V : Type u} {W : Type v} {n k : Nat}
    (A : FiniteColored V n k) (B : FiniteColored W n k) where
  map : Bijection V W
  color : ∀ v, B.color (map v) = A.color v
  adj : ∀ u v, B.adj (map u) (map v) = A.adj u v

namespace FiniteColoredIso

open Hex Hex.GraphIso

variable {V : Type u} {W : Type v} {n k : Nat}
variable {A : FiniteColored V n k} {B : FiniteColored W n k}

def finMap (F : FiniteColoredIso A B) (i : Fin n) : Fin n :=
  B.number (F.map (A.number.symm i))

theorem finMap_inj (F : FiniteColoredIso A B) :
    ∀ i j, F.finMap i = F.finMap j → i = j := by
  intro i j h
  apply A.number.symm.injective
  apply F.map.injective
  apply B.number.injective
  exact h

theorem finMap_surj (F : FiniteColoredIso A B) :
    ∀ y : Fin n, ∃ i : Fin n, F.finMap i = y := by
  intro y
  refine ⟨A.number (F.map.symm (B.number.symm y)), ?_⟩
  simp [finMap]

def perm (F : FiniteColoredIso A B) : Hex.Perm n :=
  Hex.Perm.ofFn F.finMap F.finMap_inj F.finMap_surj

theorem toHex_isIso (F : FiniteColoredIso A B) :
    IsIso A.toHex B.toHex F.perm := by
  refine IsIso.mk ?_ ?_
  · intro i
    rw [FiniteColored.toHex_color, FiniteColored.toHex_color]
    simpa [perm, finMap] using F.color (A.number.symm i)
  · intro i j
    rw [FiniteColored.toHex_adj, FiniteColored.toHex_adj]
    simpa [perm, finMap] using F.adj (A.number.symm i) (A.number.symm j)

theorem toHex_isomorphic (F : FiniteColoredIso A B) :
    Isomorphic A.toHex B.toHex :=
  Isomorphic.intro F.perm F.toHex_isIso

end FiniteColoredIso

namespace FiniteColored

open Hex Hex.GraphIso

variable {V : Type u} {W : Type v} {n k : Nat}
variable {A : FiniteColored V n k} {B : FiniteColored W n k}

def mapFromPerm (p : Hex.Perm n) (v : V) : W :=
  B.number.symm (p.get (A.number v))

def invFromPerm (p : Hex.Perm n) (w : W) : V :=
  A.number.symm (p.inv.get (B.number w))

theorem inv_mapFromPerm (p : Hex.Perm n) (v : V) :
    invFromPerm (A := A) (B := B) p (mapFromPerm (A := A) (B := B) p v) = v := by
  simp [mapFromPerm, invFromPerm]

theorem map_invFromPerm (p : Hex.Perm n) (w : W) :
    mapFromPerm (A := A) (B := B) p (invFromPerm (A := A) (B := B) p w) = w := by
  simp [mapFromPerm, invFromPerm]

def nodeBijectionFromPerm (p : Hex.Perm n) : Bijection V W where
  toFun := mapFromPerm (A := A) (B := B) p
  invFun := invFromPerm (A := A) (B := B) p
  left_inv := inv_mapFromPerm (A := A) (B := B) p
  right_inv := map_invFromPerm (A := A) (B := B) p

end FiniteColored

/--
An explicit finite numbering is a semantics-preserving compiler boundary:
abstract finite-colored isomorphism is equivalent to Hex colored-graph
isomorphism.
-/
theorem finiteColoredIso_iff_hexIsomorphic
    {V : Type u} {W : Type v} {n k : Nat}
    (A : FiniteColored V n k) (B : FiniteColored W n k) :
    Nonempty (FiniteColoredIso A B) ↔
      Hex.GraphIso.Isomorphic A.toHex B.toHex := by
  constructor
  · rintro ⟨h⟩
    exact h.toHex_isomorphic
  · intro h
    rcases Hex.GraphIso.Isomorphic.elim h with ⟨p, hp⟩
    refine ⟨{
      map := FiniteColored.nodeBijectionFromPerm (A := A) (B := B) p
      color := ?_
      adj := ?_
    }⟩
    · intro v
      have hc := Hex.GraphIso.IsIso.cells_eq hp (A.number v)
      rw [FiniteColored.toHex_color, FiniteColored.toHex_color] at hc
      simpa [FiniteColored.nodeBijectionFromPerm, FiniteColored.mapFromPerm] using hc
    · intro u v
      have ha := Hex.GraphIso.IsIso.adj_eq hp (A.number u) (A.number v)
      rw [FiniteColored.toHex_adj, FiniteColored.toHex_adj] at ha
      simpa [FiniteColored.nodeBijectionFromPerm, FiniteColored.mapFromPerm] using ha


/-! # Exact incidence presentation and composed transport -/

theorem bool_eq_of_true_iff {a b : Bool} (h : (a = true ↔ b = true)) : a = b := by
  cases a <;> cases b <;> simp_all

/--
Two finite-colored presentations of V21 incidence structures use the same
semantic colors and exactly represent the abstract incidence relation.
-/
structure IncidencePairPresentation
    {σ : Type w} {arity : σ → Nat}
    {α : Type u} {β : Type v}
    (A : RelStruct σ arity α) (B : RelStruct σ arity β)
    (n k : Nat) where
  left : FiniteColored (IncNode A) n k
  right : FiniteColored (IncNode B) n k
  color_exact :
    ∀ x : IncNode A, ∀ y : IncNode B,
      right.color y = left.color x ↔ IncNode.color y = IncNode.color x
  left_adj_exact :
    ∀ x y : IncNode A, left.adj x y = true ↔ IncNode.Adj x y
  right_adj_exact :
    ∀ x y : IncNode B, right.adj x y = true ↔ IncNode.Adj x y

namespace IncidencePairPresentation

open Hex Hex.GraphIso

variable {σ : Type w} {arity : σ → Nat}
variable {α : Type u} {β : Type v}
variable {A : RelStruct σ arity α} {B : RelStruct σ arity β}
variable {n k : Nat}

def incIsoToFiniteColoredIso
    (P : IncidencePairPresentation A B n k)
    (F : IncIso A B) :
    FiniteColoredIso P.left P.right where
  map := F.map
  color := by
    intro x
    exact (P.color_exact x (F.map x)).2 (F.color x)
  adj := by
    intro x y
    apply bool_eq_of_true_iff
    rw [P.right_adj_exact, P.left_adj_exact]
    exact F.adj x y

def finiteColoredIsoToIncIso
    (P : IncidencePairPresentation A B n k)
    (F : FiniteColoredIso P.left P.right) :
    IncIso A B where
  map := F.map
  color := by
    intro x
    exact (P.color_exact x (F.map x)).1 (F.color x)
  adj := by
    intro x y
    have htrue :
        P.right.adj (F.map x) (F.map y) = true ↔
          P.left.adj x y = true := by
      rw [F.adj x y]
    rw [P.right_adj_exact, P.left_adj_exact] at htrue
    exact htrue

/--
The experimentally discovered identity-anchor + relation-occurrence
representation, once finitely and exactly presented, transports arbitrary
relational isomorphism all the way to Hex's concrete Colored isomorphism.

This composes V21's general incidence theorem with V22's verified finite
compiler boundary.
-/
theorem sourceIso_iff_hexIsomorphic
    (P : IncidencePairPresentation A B n k) :
    Nonempty (SourceIso A B) ↔
      Isomorphic P.left.toHex P.right.toHex := by
  constructor
  · rintro ⟨h⟩
    exact (P.incIsoToFiniteColoredIso h.toIncIso).toHex_isomorphic
  · intro h
    have hf :
        Nonempty (FiniteColoredIso P.left P.right) :=
      (finiteColoredIso_iff_hexIsomorphic P.left P.right).2 h
    rcases hf with ⟨f⟩
    exact ⟨(P.finiteColoredIsoToIncIso f).toSourceIso⟩

end IncidencePairPresentation


/-! # V24: construct exact incidence presentations from finite numberings -/

namespace IncNode

variable {σ : Type w} {arity : σ → Nat}
variable {α : Type u} {A : RelStruct σ arity α}

theorem adj_symm (x y : IncNode A) :
    Adj x y ↔ Adj y x := by
  cases x <;> cases y <;> simp [Adj, eq_comm]

theorem not_adj_self (x : IncNode A) :
    ¬ Adj x x := by
  cases x <;> simp [Adj]

noncomputable def adjBool (x y : IncNode A) : Bool := by
  classical
  exact decide (Adj x y)

@[simp] theorem adjBool_eq_true_iff (x y : IncNode A) :
    adjBool x y = true ↔ Adj x y := by
  classical
  simp [adjBool]

theorem adjBool_symm (x y : IncNode A) :
    adjBool x y = adjBool y x := by
  classical
  apply bool_eq_of_true_iff
  rw [adjBool_eq_true_iff, adjBool_eq_true_iff]
  exact adj_symm x y

@[simp] theorem adjBool_self (x : IncNode A) :
    adjBool x x = false := by
  classical
  have h : ¬ Adj x x := not_adj_self x
  simpa [adjBool, h]

end IncNode

/--
Only the irreducible finite bookkeeping remains supplied:
bijective vertex numberings and a common injective ordered color code.
The exact finite-colored incidence graphs are then constructed, not assumed.
-/
structure IncidenceNumberingPair
    {σ : Type w} {arity : σ → Nat}
    {α : Type u} {β : Type v}
    (A : RelStruct σ arity α) (B : RelStruct σ arity β)
    (n k : Nat) where
  leftNumber : Bijection (IncNode A) (Fin n)
  rightNumber : Bijection (IncNode B) (Fin n)
  colorCode : IncColor σ arity → Fin k
  colorCode_injective : Function.Injective colorCode
  left_color_onto :
    Function.Surjective (fun x : IncNode A => colorCode (IncNode.color x))
  right_color_onto :
    Function.Surjective (fun x : IncNode B => colorCode (IncNode.color x))

namespace IncidenceNumberingPair

open Hex Hex.GraphIso

variable {σ : Type w} {arity : σ → Nat}
variable {α : Type u} {β : Type v}
variable {A : RelStruct σ arity α} {B : RelStruct σ arity β}
variable {n k : Nat}

noncomputable def leftFinite
    (P : IncidenceNumberingPair A B n k) :
    FiniteColored (IncNode A) n k where
  number := P.leftNumber
  color := fun x => P.colorCode (IncNode.color x)
  color_onto := P.left_color_onto
  adj := IncNode.adjBool
  adj_symm := IncNode.adjBool_symm
  adj_loopless := IncNode.adjBool_self

noncomputable def rightFinite
    (P : IncidenceNumberingPair A B n k) :
    FiniteColored (IncNode B) n k where
  number := P.rightNumber
  color := fun x => P.colorCode (IncNode.color x)
  color_onto := P.right_color_onto
  adj := IncNode.adjBool
  adj_symm := IncNode.adjBool_symm
  adj_loopless := IncNode.adjBool_self

noncomputable def exactPresentation
    (P : IncidenceNumberingPair A B n k) :
    IncidencePairPresentation A B n k where
  left := P.leftFinite
  right := P.rightFinite
  color_exact := by
    intro x y
    constructor
    · intro h
      exact P.colorCode_injective h
    · intro h
      exact congrArg P.colorCode h
  left_adj_exact := by
    intro x y
    exact IncNode.adjBool_eq_true_iff x y
  right_adj_exact := by
    intro x y
    exact IncNode.adjBool_eq_true_iff x y

/--
For arbitrary relational signatures and finite arities, explicit finite
numberings plus one faithful ordered color code suffice to construct the
incidence graphs and transport source isomorphism to Hex.
-/
theorem sourceIso_iff_hexIsomorphic
    (P : IncidenceNumberingPair A B n k) :
    Nonempty (SourceIso A B) ↔
      Isomorphic P.leftFinite.toHex P.rightFinite.toHex := by
  exact P.exactPresentation.sourceIso_iff_hexIsomorphic

end IncidenceNumberingPair

end MathGraph
