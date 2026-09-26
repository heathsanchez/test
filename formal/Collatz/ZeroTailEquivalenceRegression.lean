import Collatz.SourceProductZeroTail

namespace CollatzFinal
namespace SourceProduct

/-- Regression target: the zero-tail kernel must be shown equivalent to the
    original positive Collatz termination statement, not silently treated as
    a smaller solved problem. -/
example :
    KernelEmpty ZeroTailLive Next ↔
      (∀ n, 0 < n → CollatzGood n) := by
  exact zero_tail_kernel_empty_iff_collatz

end SourceProduct
end CollatzFinal
