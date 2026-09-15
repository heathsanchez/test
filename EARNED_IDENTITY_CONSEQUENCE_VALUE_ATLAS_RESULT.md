# Earned-Identity Consequence Value Atlas — Result

Run: `34921910079`  
Job: `104231707434`  
Commit: `8f07e2f168636dec8883d06363b20c327d0ebd06`  
Artifact: `10378467434`  
Artifact digest: `sha256:64ee8364d45407437136edfabd2ed1f4c0a14dd0f5cbf65ea732f354edca098d`

This atlas tested only reuse opportunities whose semantic identity had already
been earned by the checker. It did not trigger canonicalization or compute a
new equivalence relation.

## Quote

Across 32,735 raw quote-cache misses:

- misses with already-earned canonical identity: **22,329**
- repeated canonical identities behind distinct raw misses: **500**
- recursive quote calls inside those repeats: **216**
- maximum recursive calls for one repeat: **5**
- total measured repeated work: **54,601 ns**
- maximum repeat: **1,283 ns**

## Verified global key

Across 13,004 raw global-key misses:

- misses with already-earned canonical identity: **12,580**
- repeated canonical identities: **72**
- recursive global-key calls inside repeats: **6**
- maximum recursive calls for one repeat: **4**
- total measured repeated work: **7,105 ns**
- maximum repeat: **191 ns**

## Structural eta

Across 611 struct-eta cache misses:

- misses with already-earned canonical identity: **611**
- repeated canonical identities: **0**

## Conclusion

Even with essentially zero incremental identity cost, these cache-level
consequences are too small to matter.

Therefore the current frontier is not cross-state consequence reuse at the
cache layer.

The next search moves up to the actual instruction-level hot residual in A6 and
asks which whole computation should be avoided before it begins.
