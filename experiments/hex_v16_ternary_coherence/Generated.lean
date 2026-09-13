import HexGraphIso.Tactic

open Hex Hex.GraphIso

def roleColoring20 : Coloring 20 5 := Coloring.mod 20 5

def encA : Colored 20 5 where
  graph := Graph.ofEdges [(0,3), (0,4), (0,9), (1,3), (1,4), (1,14), (2,3), (2,4), (2,19), (5,8), (6,8), (6,9), (6,19), (7,8), (7,9), (7,14), (10,13), (10,14), (10,19), (11,13), (12,13), (15,18), (16,18), (17,18)]
  coloring := roleColoring20

def encB : Colored 20 5 where
  graph := Graph.ofEdges [(0,3), (1,3), (1,4), (1,14), (2,3), (2,9), (2,14), (4,10), (4,17), (5,8), (6,8), (7,8), (9,10), (9,16), (10,13), (11,13), (12,13), (14,15), (15,18), (15,19), (16,18), (16,19), (17,18), (17,19)]
  coloring := roleColoring20

def encC : Colored 20 5 where
  graph := Graph.ofEdges [(0,3), (0,4), (0,9), (1,3), (1,4), (1,14), (2,3), (2,9), (2,14), (4,7), (5,8), (6,8), (6,9), (6,19), (7,8), (7,19), (10,13), (10,14), (10,19), (11,13), (12,13), (15,18), (16,18), (17,18)]
  coloring := roleColoring20

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso
