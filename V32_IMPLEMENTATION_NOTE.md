# V32 implementation note

This branch implements the frozen V32 question without changing the V30/V31 commitment router.

The new carrier is a generic one-literal AST rewrite enumerator over installed atomic probe programs. It is not given `NUMERIC_LITERAL_SHIFT`, `increment`, `decrement`, a target-order constructor, or protected SAIR answers. The runtime first reproduces a natural V30-style successor whose old V28 probe carrier is exhausted. Only then are raw rewrite candidates exposed and exhaustively audited against the commitment residual. The minimum resolving raw transformer is executed through the canonical runtime and typed/retained only after verification.

Transfer is tested on a later distinct natural SAIR episode: that episode must independently reach a nonterminal successor with the old probe carrier exhausted, after which only the retained raw transformer is carried forward. If it cannot generate a useful verified probe there, V32 fails.

This is bounded transformer invention over a supplied finite structural-edit substrate, not mutation-grammar invention.