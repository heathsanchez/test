# V7 post-result multiline grammar audit (NOT heldout source success)

The sealed run at commit 1558ae7cf404575e9ba3e4f27676271d131002fb selected **single-line** ItsDangerous want_bytes and passed real native tests (297/297 before and after, incorrect return None mutation rejected). Its generated status label contains MULTILINE but this does not mean the multiline branch executed. Retain true value expression_multiline=false.

To measure the actual multiline branch of the unchanged AST rewrite on **previously EXPOSED** MarkupSafe _native.py (pallets/markupsafe@4e111271b1494995708a9e878a10829b5e10c7ba), import the V7 rewrite directly and record either an admitted AST-valid replacement or UNKNOWN; no training/tuning after result. Do not substitute this as source-independent prospective transfer. The original source must remain unmodified; no upstream PR, and do not publish a misleading claim that multiline has been qualified unless it genuinely succeeds.
