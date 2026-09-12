import HexGraphIso

open Hex Hex.GraphIso

/-
Held-out n=4 source domain: loopless directed graphs.
Adapter: each source vertex v becomes OUT(v), IN(v), ANCHOR(v), with three
ordered colours. Anchor edges tie the three role-copies of one source vertex;
a directed arc u -> v becomes OUT(u) -- IN(v).
-/

def roleColoring12 : Coloring 12 3 where
  cells := #v[0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2]
  onto := by decide

-- A: 0 -> 1 -> 2 -> 3
def encA : Colored 12 3 where
  graph := Graph.ofEdges [
    (0,5), (0,8),
    (1,6), (1,9),
    (2,7), (2,10),
    (3,11),
    (4,8), (5,9), (6,10), (7,11)
  ]
  coloring := roleColoring12

-- B: nontrivial relabelling of A by old->new [2,0,3,1].
def encB : Colored 12 3 where
  graph := Graph.ofEdges [
    (0,7), (0,8),
    (1,9),
    (2,4), (2,10),
    (3,5), (3,11),
    (4,8), (5,9), (6,10), (7,11)
  ]
  coloring := roleColoring12

-- C: 0 -> 1 <- 2 -> 3. Same underlying undirected path as A,
-- but not isomorphic to A as a directed graph.
def encC : Colored 12 3 where
  graph := Graph.ofEdges [
    (0,5), (0,8),
    (1,9),
    (2,5), (2,7), (2,10),
    (3,11),
    (4,8), (5,9), (6,10), (7,11)
  ]
  coloring := roleColoring12

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso

-- Lossy adapter control: erase direction. Both A and C become the same P4.
def lossyA : Graph 4 := Graph.ofEdges [(0,1), (1,2), (2,3)]
def lossyC : Graph 4 := Graph.ofEdges [(0,1), (1,2), (2,3)]

set_option trace.graph_iso true in
example : Graph.Isomorphic lossyA lossyC := by
  graph_iso
