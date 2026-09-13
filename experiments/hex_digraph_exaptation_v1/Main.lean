import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
Held-out n=4 source domain: loopless directed graphs.
Adapter: each source vertex v becomes OUT(v), IN(v), ANCHOR(v), with three
ordered colours. The target indices are interleaved:
  OUT(v)=3v, IN(v)=3v+1, ANCHOR(v)=3v+2.
Thus Hex's verified Coloring.mod 12 3 supplies the role colouring.
Anchor edges tie the three role-copies of one source vertex;
a directed arc u -> v becomes OUT(u) -- IN(v).
-/

def roleColoring12 : Coloring 12 3 := Coloring.mod 12 3

-- A: 0 -> 1 -> 2 -> 3
def encA : Colored 12 3 where
  graph := Graph.ofEdges [
    (0,2), (1,2),
    (3,5), (4,5),
    (6,8), (7,8),
    (9,11), (10,11),
    (0,4), (3,7), (6,10)
  ]
  coloring := roleColoring12

-- B: nontrivial relabelling of A by old->new [2,0,3,1].
-- Source arcs: 0->3, 2->0, 3->1.
def encB : Colored 12 3 where
  graph := Graph.ofEdges [
    (0,2), (1,2),
    (3,5), (4,5),
    (6,8), (7,8),
    (9,11), (10,11),
    (0,10), (1,6), (4,9)
  ]
  coloring := roleColoring12

-- C: 0 -> 1 <- 2 -> 3. Same underlying undirected path as A,
-- but not isomorphic to A as a directed graph.
def encC : Colored 12 3 where
  graph := Graph.ofEdges [
    (0,2), (1,2),
    (3,5), (4,5),
    (6,8), (7,8),
    (9,11), (10,11),
    (0,4), (4,6), (6,10)
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
