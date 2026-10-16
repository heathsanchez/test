# P-256 V2 — original-1997-source point-generator audit (frozen before V2 implementation)

Date: 2026-10-17 (Pacific/Auckland). Parent: qualified V1 negative CI 38976971244, commit 750982b1dd60ddc88f45a91cd024face1cc24b0f.

Source pins (source authenticity limited to mirrored copy, original author/date statements are source-provided):
- FreeLIP v1.1 README, 21 July 1997, https://github.com/lrobot/freelip/blob/master/README blob 2b5551522548107e3021b39a6cdddce6fdebb34e.
- FreeLIP lip.h, https://github.com/lrobot/freelip/blob/master/lip.h blob 080cda8aec8c0939348452ea3beb9f1afad845ef. Lines 593-597 choose NBITS=30 default, NBITS=26 under SINGLE_MUL; ALPHA/ALPHA50 choose NBITS=62.
- FreeLIP lip.c, https://github.com/lrobot/freelip/blob/master/lip.c blob a86ce8ae5be49e0f35999a2c87f52e1718ebdb81. Function zrstarts / zrstart lines 3790-3825, zrandom lines 3836-3860, zrandomb lines 9274-9297, zrandoml lines 9300-9333.
- Anthropic (16 October 2026) https://www.anthropic.com/research/ecdsa-curve-origins; standardized target P-256 Gx from RFC6090.
- Existing V1 source/result in branch research/p256-origin-forensics-20261017, do NOT silently replace or extend its warrant.

Question: Does the standardized P-256 Gx occur under 1997 FreeLIP NBITS=30/62 limb geometry, or under direct lrand48 continuation / a FreeLIP state seeded from companion lrand48 outputs, in the bounded source-informed domains below?

Freeze H2 hypotheses:
F30: exact FreeLIP 107-bit multiplicative state, generate zrandom(RADIX=2^30) lower 30 bits with historical rejection bound; contiguous first 192 accepted limbs; lengths 9,10,11; msf/lsf packing; reduction mod P-256 p. Track the historical native shape n=10/msf/low30 separately from exploratory shapes. Seeds: 0..65535 and all Unix seconds ±86400 centered at P-256 seed timestamp 1997-08-16 01:52:34 UTC, plus default seed 7157891 (if outside these ranges). Compute exact checked-window counts and zeros/hits. Include source-native 30-bit reconstruction of a synthetic planted target as scanner positive.
F62: same FreeLIP 107-bit state, zrandom(RADIX=2^62) lower 62 bits with historical rejection; first 192 accepted limbs; lengths 5,6,7; msf/lsf, mod p. Seeds 0..65535 and default 7157891 (no timestamp-day expansion); report separately.
L31: C lrand48 48-bit recurrence with timestamp seed 1997-08-16 01:52:34; first 40,000 outputs. Native top31-bit outputs, candidate widths 8 or 9 or 10 words, msf/lsf, mod p; include full run from beginning (not just near seed #1842). No substring claims beyond this finite output class. Add synthetic target from a known stream window to prove comparator correctness.
CHAIN30: seed FreeLIP via each 31-bit top output of the first 40,000 lrand48 draws from the same timestamp; de-duplicate exact seed values, first 64 zrandom(2^30) accepted limbs, 10-limb native-msf point windows only; mod p. This is a constructed cross-library hypothesis, NOT known historical practice. Keep this disjoint or count overlap explicitly.

Evidence floor:
1. Recheck original published FreeLIP prime239v1 26-bit known positive (seed20420/start29), reproduce official P-256 Gx/Gy from OpenSSL or RFC.
2. Independently check scanner arithmetic against a Python reference on a few fixed seed/output windows; validate historical zrandom rejection, or report no rejections in scanned bound.
3. Report exact seed/work window counts, SHA256 of code, any matches with exact seed/geometry/offset, performance and failures. If no match -> BOUNDED_NEGATIVE/HISTORICAL_ORIGIN_UNKNOWN.
4. If a match -> CANDIDATE_NUMERICAL_EXPLANATION only. Demand independent native implementation, exact Gy parity, and P-224/P-384/P-521 prospective application before any general law; archive citation/document evidence necessary for historical attribution.
5. Do NOT claim no FreeLIP, ECDSA insecurity, or autonomous novelty. Strong equal-info agent comparator NOT_RUN unless actually executed. No upstream changes.

No hidden expansion after observing zero; any later family requires another protocol freeze and lineage.
