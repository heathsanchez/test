/-! Boundary witnesses for the parameterized mutual-universe divergence.

These cases hold the semantically equal resultant universes fixed while adding
constructor structure one step at a time.  The goal is to distinguish common
family/model generation from cross-member recursive-field translation and SCC
closure.
-/

/-- Constructors present, but no cross-member fields.  If this fails, the
fault is already in constructor-bearing common-family/model generation. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `ctorBoundaryNullary_A
      type := .sort (.max (.param `u) (.param `u))
      ctors := [
        { name := `ctorBoundaryNullary_A.mk, type := .const `ctorBoundaryNullary_A [.param `u] }
      ]
    },
    {
      name := `ctorBoundaryNullary_B
      type := .sort (.param `u)
      ctors := [
        { name := `ctorBoundaryNullary_B.mk, type := .const `ctorBoundaryNullary_B [.param `u] }
      ]
    }
  ]

/-- One directed cross-member field: B u -> A u. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `ctorBoundaryAFromB_A
      type := .sort (.max (.param `u) (.param `u))
      ctors := [
        { name := `ctorBoundaryAFromB_A.fromB, type := arrow (.const `ctorBoundaryAFromB_B [.param `u]) (.const `ctorBoundaryAFromB_A [.param `u]) }
      ]
    },
    {
      name := `ctorBoundaryAFromB_B
      type := .sort (.param `u)
      ctors := [
        { name := `ctorBoundaryAFromB_B.mk, type := .const `ctorBoundaryAFromB_B [.param `u] }
      ]
    }
  ]

/-- Reverse directed cross-member field: A u -> B u. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `ctorBoundaryBFromA_A
      type := .sort (.max (.param `u) (.param `u))
      ctors := [
        { name := `ctorBoundaryBFromA_A.mk, type := .const `ctorBoundaryBFromA_A [.param `u] }
      ]
    },
    {
      name := `ctorBoundaryBFromA_B
      type := .sort (.param `u)
      ctors := [
        { name := `ctorBoundaryBFromA_B.fromA, type := arrow (.const `ctorBoundaryBFromA_A [.param `u]) (.const `ctorBoundaryBFromA_B [.param `u]) }
      ]
    }
  ]

/-- Full two-way SCC, matching the recursive shape of the existing failing
parameterized witness while keeping everything else minimal. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `ctorBoundaryScc_A
      type := .sort (.max (.param `u) (.param `u))
      ctors := [
        { name := `ctorBoundaryScc_A.fromB, type := arrow (.const `ctorBoundaryScc_B [.param `u]) (.const `ctorBoundaryScc_A [.param `u]) }
      ]
    },
    {
      name := `ctorBoundaryScc_B
      type := .sort (.param `u)
      ctors := [
        { name := `ctorBoundaryScc_B.fromA, type := arrow (.const `ctorBoundaryScc_A [.param `u]) (.const `ctorBoundaryScc_B [.param `u]) }
      ]
    }
  ]
