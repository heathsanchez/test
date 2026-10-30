package generic

import "errors"

type Config[K comparable,V any] struct { Maximum int }
type Cache[K comparable,V any] struct{}

func Create[K comparable,V any](cfg *Config[K,V]) (*Cache[K,V],error) {
	if cfg==nil || cfg.Maximum==0 {return nil,errors.New("invalid zero-valued config")}
	return &Cache[K,V]{},nil
}
