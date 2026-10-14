#!/usr/bin/env python3
"""Remove precisely one prevalidation site; source-only causal ablation."""
from pathlib import Path
p=Path("tree.go")
s=p.read_text()
old="\t// Reject duplicate param keys before mutating the tree.\n\t_ = patParamKeys(pattern)\n\n"
assert s.count(old)==1,"PREVALIDATION_SITE_NOT_UNIQUE"
assert s.count("func (n *node) InsertRoute(")==1
p.write_text(s.replace(old,"",1))
print("MATHGRAPH_ABLATION removed=prevalidate-before-tree-mutation other_edits=none")
