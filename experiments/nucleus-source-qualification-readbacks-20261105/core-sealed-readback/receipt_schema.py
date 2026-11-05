"""Compare every recorded control field except diagnostic text, as a multiset."""
from collections import Counter
import json
def controls_equal(left,right):
 def signature(rows):
  return Counter(json.dumps({k:v for k,v in r.items()if k!='stderr'},sort_keys=True,separators=(',',':'))for r in rows)
 return signature(left)==signature(right)
