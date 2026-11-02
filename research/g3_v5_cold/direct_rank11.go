// POST-HOC equal-information, manually written direct reference.
// Source family was already exposed by the frozen rank-11 trial.
// Not a blind comparator and not a claim of acquisition-cost advantage.
package main

import (
  "fmt"
  pkg "github.com/Code-Hex/go-generics-cache"
)

func main() {
  c := pkg.New[string, string]()
  k := "mathgraph-v4-probe-key-3b8e"
  if _, found := c.Get(k); found { panic("initial miss contradicted") }
  c.Set(k, "first")
  if value, found := c.Get(k); !found || value != "first" { panic("first readback contradicted") }
  c.Set(k, "second")
  if value, found := c.Get(k); !found || value != "second" { panic("second readback contradicted") }
  c.Delete(k)
  if _, found := c.Get(k); found { panic("post-delete miss contradicted") }
  fmt.Println("DIRECT_TRACE_PASS;source_calls=7;semantic_comparator=TIE")
}
