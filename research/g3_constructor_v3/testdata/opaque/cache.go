package opaque

import "fmt"

type Config[K comparable,V any] struct { Maximum int }
type Cache[K comparable,V any] struct{}

func NewCache[K comparable,V any](cfg *Config[K,V]) (*Cache[K,V],error) {
	if cfg.Maximum==0 {return nil,fmt.Errorf("invalid zero-valued config")}
	return &Cache[K,V]{},nil
}
