/-! Differential tests for heterogeneous mutual inductive universe blocks. -/

def mutualDummyRecInfo (indName : Lean.Name) (allNames : List Lean.Name) : Lean.ConstantInfo :=
  .recInfo {
    name := indName ++ `rec
    levelParams := []
    type := .sort 0
    all := allNames
    numParams := 0
    numIndices := 0
    numMotives := 0
    numMinors := 0
    rules := []
    k := false
    isUnsafe := false
  }

def rawMutualPair (A B : Lean.Name) (uA uB : Lean.Level) : Array Lean.ConstantInfo :=
  let all := [A, B]
  #[
    .inductInfo {
      name := A, levelParams := [], type := .sort uA
      numParams := 0, numIndices := 0, all := all
      ctors := [A ++ `fromB]
      numNested := 0, isRec := true, isUnsafe := false, isReflexive := false
    },
    .ctorInfo {
      name := A ++ `fromB, levelParams := []
      type := arrow (.const B []) (.const A [])
      numParams := 0, induct := A, cidx := 0, numFields := 1, isUnsafe := false
    },
    mutualDummyRecInfo A all,
    .inductInfo {
      name := B, levelParams := [], type := .sort uB
      numParams := 0, numIndices := 0, all := all
      ctors := [B ++ `fromA]
      numNested := 0, isRec := true, isUnsafe := false, isReflexive := false
    },
    .ctorInfo {
      name := B ++ `fromA, levelParams := []
      type := arrow (.const A []) (.const B [])
      numParams := 0, induct := B, cidx := 0, numFields := 1, isUnsafe := false
    },
    mutualDummyRecInfo B all
  ]

def rawEmptyMutualPair (A B : Lean.Name) (uA uB : Lean.Level) : Array Lean.ConstantInfo :=
  let all := [A, B]
  #[
    .inductInfo {
      name := A, levelParams := [], type := .sort uA
      numParams := 0, numIndices := 0, all := all
      ctors := []
      numNested := 0, isRec := false, isUnsafe := false, isReflexive := false
    },
    mutualDummyRecInfo A all,
    .inductInfo {
      name := B, levelParams := [], type := .sort uB
      numParams := 0, numIndices := 0, all := all
      ctors := []
      numNested := 0, isRec := false, isUnsafe := false, isReflexive := false
    },
    mutualDummyRecInfo B all
  ]

def rawMutualMetadataPair
    (A B : Lean.Name)
    (allA allB recAllA recAllB : List Lean.Name) : Array Lean.ConstantInfo :=
  #[
    .inductInfo {
      name := A, levelParams := [], type := .sort 1
      numParams := 0, numIndices := 0, all := allA
      ctors := [A ++ `fromB]
      numNested := 0, isRec := true, isUnsafe := false, isReflexive := false
    },
    .ctorInfo {
      name := A ++ `fromB, levelParams := []
      type := arrow (.const B []) (.const A [])
      numParams := 0, induct := A, cidx := 0, numFields := 1, isUnsafe := false
    },
    mutualDummyRecInfo A recAllA,
    .inductInfo {
      name := B, levelParams := [], type := .sort 1
      numParams := 0, numIndices := 0, all := allB
      ctors := [B ++ `fromA]
      numNested := 0, isRec := true, isUnsafe := false, isReflexive := false
    },
    .ctorInfo {
      name := B ++ `fromA, levelParams := []
      type := arrow (.const A []) (.const B [])
      numParams := 0, induct := B, cidx := 0, numFields := 1, isUnsafe := false
    },
    mutualDummyRecInfo B recAllB
  ]

/-- Alex Meiburg example: Prop mediates Type 0 and Type 2. Current Lean contract rejects. -/
bad_raw_consts
  let A := `heteroABC_A
  let B := `heteroABC_B
  let C := `heteroABC_C
  let all := [A, B, C]
  #[
    .inductInfo {
      name := A, levelParams := [], type := .sort 0
      numParams := 0, numIndices := 0, all := all
      ctors := [A ++ `fromB, A ++ `fromC]
      numNested := 0, isRec := true, isUnsafe := false, isReflexive := false
    },
    .ctorInfo {
      name := A ++ `fromB, levelParams := []
      type := arrow (.const B []) (.const A [])
      numParams := 0, induct := A, cidx := 0, numFields := 1, isUnsafe := false
    },
    .ctorInfo {
      name := A ++ `fromC, levelParams := []
      type := arrow (.const C []) (.const A [])
      numParams := 0, induct := A, cidx := 1, numFields := 1, isUnsafe := false
    },
    mutualDummyRecInfo A all,
    .inductInfo {
      name := B, levelParams := [], type := .sort 1
      numParams := 0, numIndices := 0, all := all
      ctors := [B ++ `fromA]
      numNested := 0, isRec := true, isUnsafe := false, isReflexive := false
    },
    .ctorInfo {
      name := B ++ `fromA, levelParams := []
      type := arrow (.const A []) (.const B [])
      numParams := 0, induct := B, cidx := 0, numFields := 1, isUnsafe := false
    },
    mutualDummyRecInfo B all,
    .inductInfo {
      name := C, levelParams := [], type := .sort 3
      numParams := 0, numIndices := 0, all := all
      ctors := [C ++ `fromA]
      numNested := 0, isRec := true, isUnsafe := false, isReflexive := false
    },
    .ctorInfo {
      name := C ++ `fromA, levelParams := []
      type := arrow (.const A []) (.const C [])
      numParams := 0, induct := C, cidx := 0, numFields := 1, isUnsafe := false
    },
    mutualDummyRecInfo C all
  ]

/-- Alex Meiburg weaker example: G : Prop mutually recursive with H : Type 1. Current Lean contract rejects. -/
bad_raw_consts
  let G := `heteroGH_G
  let H := `heteroGH_H
  let all := [G, H]
  #[
    .inductInfo {
      name := G, levelParams := [], type := .sort 0
      numParams := 0, numIndices := 0, all := all
      ctors := [G ++ `base, G ++ `fromH]
      numNested := 0, isRec := true, isUnsafe := false, isReflexive := false
    },
    .ctorInfo {
      name := G ++ `base, levelParams := []
      type := .const G []
      numParams := 0, induct := G, cidx := 0, numFields := 0, isUnsafe := false
    },
    .ctorInfo {
      name := G ++ `fromH, levelParams := []
      type := arrow (.const H []) (.const G [])
      numParams := 0, induct := G, cidx := 1, numFields := 1, isUnsafe := false
    },
    mutualDummyRecInfo G all,
    .inductInfo {
      name := H, levelParams := [], type := .sort 2
      numParams := 0, numIndices := 0, all := all
      ctors := [H ++ `mk]
      numNested := 0, isRec := true, isUnsafe := false, isReflexive := false
    },
    .ctorInfo {
      name := H ++ `mk, levelParams := []
      type := arrow (.const G []) (.const H [])
      numParams := 0, induct := H, cidx := 0, numFields := 1, isUnsafe := false
    },
    mutualDummyRecInfo H all
  ]

/-- Nearest recursive boundary: Prop versus Type 0. -/
bad_raw_consts rawMutualPair `heteroPropType0_P `heteroPropType0_T .zero (.succ .zero)

/-- Recursive Type 0 versus Type 1 without Prop mediation. -/
bad_raw_consts rawMutualPair `heteroType0Type1_A `heteroType0Type1_B (.succ .zero) (.succ (.succ .zero))

/-- Same Prop/Type mismatch, but with the higher-universe member first. -/
bad_raw_consts rawMutualPair `heteroReversed_H `heteroReversed_P (.succ (.succ .zero)) .zero

/-- The universe restriction is block-level even when the block is linearizable/non-recursive. -/
bad_raw_consts rawEmptyMutualPair `heteroEmptyProp_A `heteroEmptyProp_B .zero (.succ .zero)

/-- A second non-recursive heterogeneous block, entirely in Type. -/
bad_raw_consts rawEmptyMutualPair `heteroEmptyType_A `heteroEmptyType_B (.succ .zero) (.succ (.succ (.succ .zero)))

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

/-- Equality must be semantic, not syntactic: max (Type 0) Prop = Type 0. -/
good_decl
  .inductDecl (lparams := []) (nparams := 0) (isUnsafe := false) [
    {
      name := `levelEqMaxControl_A
      type := .sort (.max (.succ .zero) .zero)
      ctors := [
        { name := `levelEqMaxControl_A.fromB, type := arrow (.const `levelEqMaxControl_B []) (.const `levelEqMaxControl_A []) }
      ]
    },
    {
      name := `levelEqMaxControl_B
      type := .sort (.succ .zero)
      ctors := [
        { name := `levelEqMaxControl_B.fromA, type := arrow (.const `levelEqMaxControl_A []) (.const `levelEqMaxControl_B []) }
      ]
    }
  ]

/-- A second semantic-equality control through imax normalization. -/
good_decl
  .inductDecl (lparams := []) (nparams := 0) (isUnsafe := false) [
    {
      name := `levelEqImaxControl_A
      type := .sort (.imax .zero (.succ .zero))
      ctors := [
        { name := `levelEqImaxControl_A.fromB, type := arrow (.const `levelEqImaxControl_B []) (.const `levelEqImaxControl_A []) }
      ]
    },
    {
      name := `levelEqImaxControl_B
      type := .sort (.succ .zero)
      ctors := [
        { name := `levelEqImaxControl_B.fromA, type := arrow (.const `levelEqImaxControl_A []) (.const `levelEqImaxControl_B []) }
      ]
    }
  ]

/-- Parameterized semantic equality: max u u = u inside a mutual block. -/
good_decl
  .inductDecl (lparams := [`u]) (nparams := 0) (isUnsafe := false) [
    {
      name := `levelEqParamIdem_A
      type := .sort (.max (.param `u) (.param `u))
      ctors := [
        { name := `levelEqParamIdem_A.fromB, type := arrow (.const `levelEqParamIdem_B [.param `u]) (.const `levelEqParamIdem_A [.param `u]) }
      ]
    },
    {
      name := `levelEqParamIdem_B
      type := .sort (.param `u)
      ctors := [
        { name := `levelEqParamIdem_B.fromA, type := arrow (.const `levelEqParamIdem_A [.param `u]) (.const `levelEqParamIdem_B [.param `u]) }
      ]
    }
  ]

/-- Parameterized semantic equality through absorption: max u (max u v) = max u v. -/
good_decl
  .inductDecl (lparams := [`u, `v]) (nparams := 0) (isUnsafe := false) [
    {
      name := `levelEqParamAbsorb_A
      type := .sort (.max (.param `u) (.max (.param `u) (.param `v)))
      ctors := [
        { name := `levelEqParamAbsorb_A.fromB, type := arrow (.const `levelEqParamAbsorb_B [.param `u, .param `v]) (.const `levelEqParamAbsorb_A [.param `u, .param `v]) }
      ]
    },
    {
      name := `levelEqParamAbsorb_B
      type := .sort (.max (.param `u) (.param `v))
      ctors := [
        { name := `levelEqParamAbsorb_B.fromA, type := arrow (.const `levelEqParamAbsorb_A [.param `u, .param `v]) (.const `levelEqParamAbsorb_B [.param `u, .param `v]) }
      ]
    }
  ]

/-- Block metadata disagreement: members list the same block in different orders. -/
bad_raw_consts
  rawMutualMetadataPair `mutualMetaOrder_A `mutualMetaOrder_B
    [`mutualMetaOrder_A, `mutualMetaOrder_B]
    [`mutualMetaOrder_B, `mutualMetaOrder_A]
    [`mutualMetaOrder_A, `mutualMetaOrder_B]
    [`mutualMetaOrder_A, `mutualMetaOrder_B]

/-- Block metadata disagreement: one inductive omits its partner from `all`. -/
bad_raw_consts
  rawMutualMetadataPair `mutualMetaMissing_A `mutualMetaMissing_B
    [`mutualMetaMissing_A, `mutualMetaMissing_B]
    [`mutualMetaMissing_B]
    [`mutualMetaMissing_A, `mutualMetaMissing_B]
    [`mutualMetaMissing_A, `mutualMetaMissing_B]

/-- Recursor metadata disagrees with otherwise-consistent inductive block membership. -/
bad_raw_consts
  rawMutualMetadataPair `mutualMetaRecMissing_A `mutualMetaRecMissing_B
    [`mutualMetaRecMissing_A, `mutualMetaRecMissing_B]
    [`mutualMetaRecMissing_A, `mutualMetaRecMissing_B]
    [`mutualMetaRecMissing_A]
    [`mutualMetaRecMissing_A, `mutualMetaRecMissing_B]

/-- Duplicate member name in block metadata. -/
bad_raw_consts
  rawMutualMetadataPair `mutualMetaDuplicate_A `mutualMetaDuplicate_B
    [`mutualMetaDuplicate_A, `mutualMetaDuplicate_A, `mutualMetaDuplicate_B]
    [`mutualMetaDuplicate_A, `mutualMetaDuplicate_A, `mutualMetaDuplicate_B]
    [`mutualMetaDuplicate_A, `mutualMetaDuplicate_A, `mutualMetaDuplicate_B]
    [`mutualMetaDuplicate_A, `mutualMetaDuplicate_A, `mutualMetaDuplicate_B]
