/-! Differential tests for heterogeneous mutual inductive universe blocks. -/

/-- Alex Meiburg example: Prop mediates Type 0 and Type 2. Current Lean contract rejects. -/
bad_decl
  .inductDecl (lparams := []) (nparams := 0) (isUnsafe := false) [
    {
      name := `heteroABC_A
      type := .sort 0
      ctors := [
        { name := `heteroABC_A.fromB, type := arrow (.const `heteroABC_B []) (.const `heteroABC_A []) },
        { name := `heteroABC_A.fromC, type := arrow (.const `heteroABC_C []) (.const `heteroABC_A []) }
      ]
    },
    {
      name := `heteroABC_B
      type := .sort 1
      ctors := [
        { name := `heteroABC_B.fromA, type := arrow (.const `heteroABC_A []) (.const `heteroABC_B []) }
      ]
    },
    {
      name := `heteroABC_C
      type := .sort 3
      ctors := [
        { name := `heteroABC_C.fromA, type := arrow (.const `heteroABC_A []) (.const `heteroABC_C []) }
      ]
    }
  ]

/-- Alex Meiburg weaker example: G : Prop mutually recursive with H : Type 1. Current Lean contract rejects. -/
bad_decl
  .inductDecl (lparams := []) (nparams := 0) (isUnsafe := false) [
    {
      name := `heteroGH_G
      type := .sort 0
      ctors := [
        { name := `heteroGH_G.base, type := .const `heteroGH_G [] },
        { name := `heteroGH_G.fromH, type := arrow (.const `heteroGH_H []) (.const `heteroGH_G []) }
      ]
    },
    {
      name := `heteroGH_H
      type := .sort 2
      ctors := [
        { name := `heteroGH_H.mk, type := arrow (.const `heteroGH_G []) (.const `heteroGH_H []) }
      ]
    }
  ]

/-- Harness control: an otherwise similar homogeneous mutual block must remain accepted. -/
good_decl
  .inductDecl (lparams := []) (nparams := 0) (isUnsafe := false) [
    {
      name := `homogeneousMutualControl_A
      type := .sort 1
      ctors := [
        { name := `homogeneousMutualControl_A.fromB, type := arrow (.const `homogeneousMutualControl_B []) (.const `homogeneousMutualControl_A []) }
      ]
    },
    {
      name := `homogeneousMutualControl_B
      type := .sort 1
      ctors := [
        { name := `homogeneousMutualControl_B.fromA, type := arrow (.const `homogeneousMutualControl_A []) (.const `homogeneousMutualControl_B []) }
      ]
    }
  ]
