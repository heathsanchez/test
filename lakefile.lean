import Lake
open Lake DSL

package collatzFinal where
  moreLeanArgs := #["-DautoImplicit=false"]

@[default_target]
lean_lib CollatzFinal where
  srcDir := "formal"
  roots := #[`Collatz.FinalKernel, `Collatz.Certificate, `Collatz.Shortcut]
