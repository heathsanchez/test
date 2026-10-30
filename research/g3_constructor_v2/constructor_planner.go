// V2 experimental constructor planner. This stub deliberately implements no
// synthesis yet; the first CI run must demonstrate a real failing test.
package main

import "go/ast"

type Plan struct {
	Schema string `json:"schema"`
	Status string `json:"status"`
	Constructor string `json:"constructor"`
	Call string `json:"call"`
	RootType string `json:"root_type"`
	HasErrorResult bool `json:"has_error_result"`
	SpeculativeGeneric bool `json:"speculative_generic"`
}

func planFromFiles(_ []*ast.File) Plan {
	return Plan{Schema:"mathgraph.g3.typed-constructor.v2", Status:"UNKNOWN_CONSTRUCTOR_INHABITANT"}
}

func main(){}
