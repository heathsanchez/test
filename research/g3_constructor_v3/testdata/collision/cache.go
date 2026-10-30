package collision

import "fmt"

type Config[K comparable, V any] struct {
	Cost int
	MaxCost int
}
type Cache[K comparable, V any] struct{}

func NewCache[K comparable, V any](cfg *Config[K,V]) (*Cache[K,V], error) {
	if cfg.MaxCost == 0 {return nil,fmt.Errorf("MaxCost missing")}
	if cfg.Cost != 0 {return nil,fmt.Errorf("Cost must remain zero")}
	return &Cache[K,V]{},nil
}
