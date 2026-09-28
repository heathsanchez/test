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
    `Collatz.OrdinaryExitReduction,
    `Collatz.OrdinaryInverseOdd,
    `Collatz.FirstCrossingRigidity,
    `Collatz.HardFirstCrossing,
    `Collatz.ThreeAdicReverseBarrier,
    `Collatz.FirstCrossingBias,
    `Collatz.FirstCrossingGap,
    `Collatz.StrictDescentReduction,
    `Collatz.HardCrossingFuture,
    `Collatz.ReverseTargetBoundary,
    `Collatz.SourceCoherenceAudit,
    `Collatz.FinalExcursion,
    `Collatz.AssembledConstructorCloseout,
    `Collatz.ConstructorTournament,
    `Collatz.ThreeQuarterCoalescence,
    `Collatz.PrefixHighOddCloseout,
    `Collatz.QuarterSplice,
    `Collatz.PostDiagonalFiber,
    `Collatz.UniversalDiagonal,
    `Collatz.DoubleDepthCloseout,
    `Collatz.DoubleDepthCorridor,
    `Collatz.DeficitOneCheckpoint,
    `Collatz.PersistentCorridor,
    `Collatz.FirstSuperHighBoundary,
    `Collatz.WeightedCoalescence
  ]
