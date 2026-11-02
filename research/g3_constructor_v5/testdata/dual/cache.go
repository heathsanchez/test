package dualcache
import "errors"
type Cache[K comparable,V any] struct { values map[K]V }
func New[K comparable,V any](size int) (*Cache[K,V],error) {if size<1 {return nil,errors.New("size")};return &Cache[K,V]{values:map[K]V{}},nil}
func (c *Cache[K,V]) Add(k K,v V) bool {c.values[k]=v;return false}
func (c *Cache[K,V]) Get(k K) (V,bool) {v,ok:=c.values[k];return v,ok}
func (c *Cache[K,V]) Remove(k K) bool {_,ok:=c.values[k];delete(c.values,k);return ok}
