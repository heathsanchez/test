package broken
 type Cache struct{}
 func New() *Cache {return &Cache{}}
 func (*Cache) Set(key,value string){}
 func (*Cache) Get(key string)(string,bool){return "",false}
 func (*Cache) Delete(key string){}
