package duration

import "time"

type Cache struct { Expiry time.Duration }

func New(expiry, cleanup time.Duration) *Cache {
	return &Cache{Expiry:expiry}
}
