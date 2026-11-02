package legacycache
import "time"
type Cache struct { entries map[string]string }
func New(defaultTTL,cleanup time.Duration) *Cache { return &Cache{entries:map[string]string{}} }
func (c *Cache) Set(k string,v interface{},ttl time.Duration) { c.entries[k] = v.(string) }
func (c *Cache) Get(k string) (interface{},bool) { v,ok:=c.entries[k]; if !ok {return nil,false}; return v,true }
func (c *Cache) Delete(k string) { delete(c.entries,k) }
