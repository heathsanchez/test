import Lake
open Lake DSL

package collatzFinal where
  moreLeanArgs := #["-DautoImplicit=false"]

@[default_target]
lean_lib CollatzFinal where
  srcDir := "formal"
  roots := #[
    `Collatz.FinalKernel,
    `Collatz.Certificate,
    `Collatz.Shortcut,
    `Collatz.Squeeze,
    `Collatz.SourceProduct,
    `Collatz.SourceProductAffine,
    `Collatz.CoefficientCrossing,
    `Collatz.CoefficientDynamics,
    `Collatz.SurvivalDeficit,
    `Collatz.FirstCrossingRigidity,
    `Collatz.FixedSourceProgress,
    `Collatz.CoalescenceDescent,
    `Collatz.FinalExcursionContraction
  ]
