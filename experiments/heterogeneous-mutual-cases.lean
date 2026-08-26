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
