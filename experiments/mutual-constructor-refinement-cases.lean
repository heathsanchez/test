/-! Refinement controls after constructor-boundary differential.

These isolate two questions:
1. Does ind-models fail merely when constructor-bearing members use semantically equal but syntactically different parameterized result levels?
2. Do mathgraph/sokonanoda reject one-way mutual blocks regardless of universe syntax?
-/

/-- Nullary constructors with identical resultant syntax: control for ind-models. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `ctorRefineSameNullary_A
      type := .sort (.param `u)
      ctors := [
        { name := `ctorRefineSameNullary_A.mk, type := .const `ctorRefineSameNullary_A [.param `u] }
      ]
    },
    {
      name := `ctorRefineSameNullary_B
      type := .sort (.param `u)
      ctors := [
        { name := `ctorRefineSameNullary_B.mk, type := .const `ctorRefineSameNullary_B [.param `u] }
      ]
    }
  ]

/-- Nullary constructors with max u 0 versus u: another semantic-equality control. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `ctorRefineMaxZeroNullary_A
      type := .sort (.max (.param `u) .zero)
      ctors := [
        { name := `ctorRefineMaxZeroNullary_A.mk, type := .const `ctorRefineMaxZeroNullary_A [.param `u] }
      ]
    },
    {
      name := `ctorRefineMaxZeroNullary_B
      type := .sort (.param `u)
      ctors := [
        { name := `ctorRefineMaxZeroNullary_B.mk, type := .const `ctorRefineMaxZeroNullary_B [.param `u] }
      ]
    }
  ]

/-- Same-syntax one-way block, B u -> A u. Tests whether SCC policy is independent of universe normalization. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `ctorRefineSameAFromB_A
      type := .sort (.param `u)
      ctors := [
        { name := `ctorRefineSameAFromB_A.fromB, type := arrow (.const `ctorRefineSameAFromB_B [.param `u]) (.const `ctorRefineSameAFromB_A [.param `u]) }
      ]
    },
    {
      name := `ctorRefineSameAFromB_B
      type := .sort (.param `u)
      ctors := [
        { name := `ctorRefineSameAFromB_B.mk, type := .const `ctorRefineSameAFromB_B [.param `u] }
      ]
    }
  ]

/-- Reverse same-syntax one-way block, A u -> B u. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `ctorRefineSameBFromA_A
      type := .sort (.param `u)
      ctors := [
        { name := `ctorRefineSameBFromA_A.mk, type := .const `ctorRefineSameBFromA_A [.param `u] }
      ]
    },
    {
      name := `ctorRefineSameBFromA_B
      type := .sort (.param `u)
      ctors := [
        { name := `ctorRefineSameBFromA_B.fromA, type := arrow (.const `ctorRefineSameBFromA_A [.param `u]) (.const `ctorRefineSameBFromA_B [.param `u]) }
      ]
    }
  ]

/-- Only the max-u-u member has a constructor; partner is empty. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `ctorRefineOnlyA_A
      type := .sort (.max (.param `u) (.param `u))
      ctors := [
        { name := `ctorRefineOnlyA_A.mk, type := .const `ctorRefineOnlyA_A [.param `u] }
      ]
    },
    {
      name := `ctorRefineOnlyA_B
      type := .sort (.param `u)
      ctors := []
    }
  ]

/-- Only the canonical-u member has a constructor; partner is empty. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `ctorRefineOnlyB_A
      type := .sort (.max (.param `u) (.param `u))
      ctors := []
    },
    {
      name := `ctorRefineOnlyB_B
      type := .sort (.param `u)
      ctors := [
        { name := `ctorRefineOnlyB_B.mk, type := .const `ctorRefineOnlyB_B [.param `u] }
      ]
    }
  ]
