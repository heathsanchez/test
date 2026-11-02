package genericcache

import "time"

type Cache[K comparable, V any] struct{ values map[K]V }
type Option[K comparable, V any] func(*Cache[K, V])
type Item[K comparable, V any] struct{ value V }

func (i *Item[K, V]) Value() V { return i.value }

func New[K comparable, V any](opts ...Option[K, V]) *Cache[K, V] {
	return &Cache[K, V]{values: map[K]V{}}
}
func (c *Cache[K, V]) Set(key K, value V, ttl time.Duration) *Item[K, V] {
	if ttl != time.Duration(-1) {
		panic("non-persistent TTL")
	}
	c.values[key] = value
	return &Item[K, V]{value: value}
}
func (c *Cache[K, V]) Get(key K, opts ...Option[K, V]) *Item[K, V] {
	value, ok := c.values[key]
	if !ok {
		return nil
	}
	return &Item[K, V]{value: value}
}
func (c *Cache[K, V]) Delete(key K) { delete(c.values, key) }
