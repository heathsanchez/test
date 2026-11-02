package buildercache

type Builder struct{}
type Cache struct{ values map[string]string }

func New(size int) *Builder                    { return &Builder{} }
func (*Builder) Build() *Cache                 { return &Cache{values: map[string]string{}} }
func (c *Cache) Set(key, value string) error   { c.values[key] = value; return nil }
func (c *Cache) Get(key string) (string, bool) { v, ok := c.values[key]; return v, ok }
func (c *Cache) Remove(key string) bool {
	_, had := c.values[key]
	delete(c.values, key)
	return had
}
