"""Typed source-prose relation compiler for one known pinned Nature PDF.

Human-authored lexical/semantic grammar. No expected Nature frequency, HFS
number, or weights are supplied by source-dependent code. This is not a
universal physical semantics or autonomous method invention.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import re
from affine_core import Datum,linear_map,SourceParseFailure

NUM=r"([0-9][0-9,]*\.[0-9]+)"
class RelationUnknown(SourceParseFailure):
    pass

@dataclass(frozen=True)
class TextWitness:
    kind: str
    span: str
    start: int
    end: int

def source_ratio(text:str):
    """Use line-strength physical role, never unrelated laser power ratio."""
    matches=[]
    for m in re.finditer(r"The line strengths\b",text):
        window=text[m.start():m.start()+750]
        # The ratio must be syntactically attached to line strengths of two
        # atomic transitions, not merely a number in the same document.
        row=re.search(r"2S[–−\-]6P1/2.*?2S[–−\-]6P3/2.*?"
                      r"transitions\s+have\s+a\s+(\d+)\s*:\s*(\d+)\s+ratio",
                      window,re.S)
        if row:
            a,b=int(row.group(1)),int(row.group(2))
            matches.append((a,b,TextWitness("fine-structure-line-strength-ratio",
                                           window[:row.end()],
                                           m.start(),m.start()+row.end())))
    if len(matches)!=1:
        raise RelationUnknown("UNKNOWN_LINE_STRENGTH_SOURCE_RATIO")
    a,b,w=matches[0]
    if not (a>0 and b>0 and a+b>0):
        raise RelationUnknown("INVALID_SOURCE_WEIGHT_RATIO")
    return F(a,a+b),F(b,a+b),w

def source_transition_pair(text:str):
    """Take main Eq4/5 measured labels and reported combined uncertainties."""
    start=text.find("By averaging all available data")
    if start<0:
        raise RelationUnknown("MEASUREMENT_SECTION_UNAVAILABLE")
    # Keep the original 2-column PDF extraction text, no target output
    # values or ratio used to select a fitting pair.
    section=text[start:start+9000]
    out={}
    for m in re.finditer(r"ν\s*([13]/2)\s*=\s*"+NUM+r"\s*\((\d+)\)\s*stat",
                         section,re.S):
        label,value=m.group(1),m.group(2)
        if label in out:
            raise RelationUnknown("AMBIGUOUS_REPEATED_MEASUREMENT_LABEL")
        # Locate the repeated final reported combined standard uncertainty,
        # rather than the preceding separated stat and sys uncertainties.
        suffix=section[m.end():m.end()+5000]
        final=re.search(r"=\s*"+re.escape(value)+r"\s*\((\d+)\)\s*kHz",suffix,re.S)
        if final is None:
            raise RelationUnknown("MEASUREMENT_COMBINED_UNCERTAINTY_UNKNOWN_"+label)
        value_f=F(value.replace(",",""))
        sigma=F(final.group(1))/F(10**len(value.split(".")[-1]))
        out[label]=(Datum(value_f,sigma),
                    TextWitness("labeled-transition-frequency-"+label,
                                section[m.start():m.end()]+
                                " ... "+suffix[final.start():final.end()],
                                start+m.start(),start+m.end()+final.end()))
    if set(out)!={"1/2","3/2"}:
        raise RelationUnknown("SOURCE_MEASUREMENT_LABELS_NOT_BIJECTIVE")
    if out["1/2"][0].value==out["3/2"][0].value:
        raise RelationUnknown("DEGENERATE_TRANSITION_OBSERVATIONS")
    return out

def source_hfs(text:str):
    role="with the hyperfine-structure (HFS) correction"
    at=text.find(role)
    if at<0:raise RelationUnknown("SOURCE_HFS_SEMANTIC_ROLE_MISSING")
    section=text[at:at+330]
    # Reject offset without explicit sign. The source provides a negative
    # hyperfine correction; no fabricated arithmetic sign.
    match=re.search(r"=\s*([+\u2212-])\s*"+NUM+r"\s*\((\d+)\)\s*kHz",
                    section,re.S)
    if not match:
        raise RelationUnknown("UNKNOWN_SIGNED_HFS_OFFSET")
    sign,num,digits=match.groups()
    digits_before= len(num.split(".")[-1])
    value=F(num.replace(",",""))
    if sign in ("\u2212","-"):
        value=-value
    sigma=F(digits)/F(10**digits_before)
    return Datum(value,sigma),TextWitness("signed-hyperfine-correction",
                   section[:match.end()],at,at+match.end())

def source_ratio_compiled_centroid(text:str):
    a,b,ratio_witness=source_ratio(text)
    measurements=source_transition_pair(text)
    offset,offset_witness=source_hfs(text)
    x=[measurements["1/2"][0], measurements["3/2"][0], offset]
    # Exact rule reused unchanged from V3: arithmetic is NOT reimplemented.
    out=linear_map(x,[a,b,F(1)])
    return {"value":out,
            "source_coefficients":[a,b,F(1)],
            "source_measurements":measurements,
            "source_offset":offset,
            "ratio_witness":ratio_witness,
            "offset_witness":offset_witness,
            "physical_uncertainty":"UNKNOWN_FULL_COVARIANCE_NOT_INFERRED"}

def published_centroid_for_validation_only(text:str):
    at=text.find("Finally, we combine the two transition frequencies")
    if at<0:raise RelationUnknown("ORIGINAL_PUBLISHED_TARGET_SECTION_MISSING")
    # Source Eq8 appears within this short context; do not inspect the target
    # until source-relation-compilation has completely finished.
    section=text[at:at+1600]
    results=re.findall(NUM+r"\s*\((\d+)\)\s*kHz",section)
    big=[]
    for s,sigma in results:
        val=F(s.replace(",",""))
        if val>F(10**11):
            big.append((val,sigma))
    if len(big)!=1:
        raise RelationUnknown("AMBIGUOUS_PUBLISHED_CENTROID_TARGET")
    return big[0]
