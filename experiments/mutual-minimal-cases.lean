/-! Minimal witnesses for the parameterized mutual-universe divergence. -/

/-- Minimal orientation: no constructors, max u u versus u. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `minParamIdem_A
      type := .sort (.max (.param `u) (.param `u))
      ctors := []
    },
    {
      name := `minParamIdem_B
      type := .sort (.param `u)
      ctors := []
    }
  ]

/-- Reverse the member order to detect first-member asymmetry. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `minParamIdemRev_A
      type := .sort (.param `u)
      ctors := []
    },
    {
      name := `minParamIdemRev_B
      type := .sort (.max (.param `u) (.param `u))
      ctors := []
    }
  ]

/-- Simpler parameterized normalization: max u 0 = u. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `minParamMaxZero_A
      type := .sort (.max (.param `u) .zero)
      ctors := []
    },
    {
      name := `minParamMaxZero_B
      type := .sort (.param `u)
      ctors := []
    }
  ]

/-- Syntactic control: both members use the same unsimplified expression. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `minParamSameSyntax_A
      type := .sort (.max (.param `u) (.param `u))
      ctors := []
    },
    {
      name := `minParamSameSyntax_B
      type := .sort (.max (.param `u) (.param `u))
      ctors := []
    }
  ]
