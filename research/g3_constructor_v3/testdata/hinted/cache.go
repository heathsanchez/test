package hinted

import "fmt"

type Config[K comparable, V any] struct {
	NumCounters int
	MaxCost int
	BufferItems int
}
type Cache[K comparable, V any] struct { Ready bool }

func NewCache[K comparable, V any](cfg *Config[K, V]) (*Cache[K, V], error) {
	if cfg == nil || cfg.NumCounters < 10 { return nil, fmt.Errorf("NumCounters must be at least 10") }
	if cfg.MaxCost == 0 { return nil, fmt.Errorf("MaxCost cannot be zero") }
	if cfg.BufferItems == 0 { return nil, fmt.Errorf("BufferItems must be positive") }
	return &Cache[K,V]{Ready: true}, nil
}
