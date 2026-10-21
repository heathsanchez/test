# V9 post-exposure comparator audit, not part of sealed evaluation

The first frozen CI run #39541413275 identified source owner signature "bisect. insort_left ( a , x ... )", while the conventional signature-aware comparator incorrectly searched for literal "insort_left(" and returned UNKNOWN. The candidate used a whitespace-tolerant regex and succeeded. This is an implementation asymmetry, not evidence of superiority.

This follow-on check normalizes whitespace around dots and parentheses for the conventional comparator and compares its exact owner selection to the original candidate, holding original source SHA and first-run immutable artifacts fixed. It must be scored as POSTEXPOSURE_FAIR_BASELINE, never as original prospective baseline score. Same signature-owner logic as equally informed expert; expected TIE if the method is simple markup lookup.
Source meaning of "left of equals" remains separately UNKNOWN because owner text says "insert in sorted order" and refers to bisect_left rather than independently spelling out equality case in this selected dd.
