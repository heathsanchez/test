"""Exact source-table affine consequences. No semantic auto-discovery."""
import re
from dataclasses import dataclass
from fractions import Fraction as F

class SourceParseFailure(ValueError):
    pass

@dataclass(frozen=True)
class Datum:
    value: F
    sigma: F

# Explicit uncertainty format in Table I: 770 649 350 002.60(1.90)
# This is not the alternative CODATA concise-last-digit notation.
PUBLISHED_EXPLICIT_UNCERTAINTY=re.compile(
    r"(?<![0-9])([+\u2212\-]?\d(?:[\d ]*\d)?\.\d+)\((\d+\.\d+)\)")

def parse_explicit_entries(line):
    found=PUBLISHED_EXPLICIT_UNCERTAINTY.findall(line)
    return [Datum(F(value.replace(" ","").replace("\u2212","-")),
                  F(uncertainty)) for value,uncertainty in found]

def table_rows(text):
    """Read numeric values directly from text extracted from a pinned PDF."""
    begin=text.find("TABLE I. Systematic corrections")
    if begin<0:
        raise SourceParseFailure("ORIGINAL_TABLE_HEADING_MISSING")
    result=[]
    for raw in text[begin:].splitlines():
        m=PUBLISHED_EXPLICIT_UNCERTAINTY.search(raw)
        if not m: continue
        values=parse_explicit_entries(raw)
        if len(values)!=3:
            raise SourceParseFailure("MALFORMED_THREE_COLUMN_TABLE_ROW")
        label=raw[:m.start()].strip()
        if not label:
            raise SourceParseFailure("MISSING_ROW_ROLE")
        result.append((label,values))
        if "Final measured value" in label:
            break
    if len(result)!=9:
        raise SourceParseFailure("MISSING_OR_DUPLICATE_TABLE_ROW")
    if not result[0][0].startswith("ac Stark shift corrected"):
        raise SourceParseFailure("INITIAL_ROW_IDENTITY_MISMATCH")
    if result[-1][0]!="Final measured value":
        raise SourceParseFailure("FINAL_ROW_IDENTITY_MISMATCH")
    roles=[row[0] for row in result]
    if len(set(roles))!=len(roles):
        raise SourceParseFailure("DUPLICATED_ROW_ROLE")
    return result

def linear_map(inputs,coefficients):
    if len(inputs)!=len(coefficients) or not inputs:
        raise SourceParseFailure("AFFINE_ARITY_MISMATCH")
    return sum((x.value*F(a) for x,a in zip(inputs,coefficients)),F(0))

def independent_variance(inputs,coefficients,declared=False):
    if not declared:
        raise SourceParseFailure("UNKNOWN_COVARIANCE_FOR_VARIANCE")
    if len(inputs)!=len(coefficients):
        raise SourceParseFailure("AFFINE_ARITY_MISMATCH")
    return sum((x.sigma*x.sigma*F(a)*F(a) for x,a in zip(inputs,coefficients)),F(0))

def reproduce_table(rows):
    if len(rows)!=9:
        raise SourceParseFailure("MISSING_OR_DUPLICATE_TABLE_ROW")
    observed=[]
    for col in range(3):
        initial_and_corrections=[entries[col] for role,entries in rows[:-1]]
        target=rows[-1][1][col]
        actual=linear_map(initial_and_corrections,[1]*len(initial_and_corrections))
        uncertainty_sq=independent_variance(initial_and_corrections,
                                             [1]*len(initial_and_corrections),
                                             declared=True)
        # Rounded two decimal sigma from independent quadrature matches
        # source at displayed precision; source-to-raw covariance is unknown.
        from decimal import Decimal as D,localcontext,ROUND_HALF_UP
        with localcontext() as ctx:
            ctx.prec=50
            u=D(uncertainty_sq.numerator)/D(uncertainty_sq.denominator)
            u=u.sqrt().quantize(D("0.01"),rounding=ROUND_HALF_UP)
            specified=D(target.sigma.numerator)/D(target.sigma.denominator)
        observed.append({"col":col+1,"value":actual,"reported":target.value,
                         "exact_value_match":actual==target.value,
                         "rss_rounded_sigma":str(u),
                         "reported_sigma":str(specified),
                         "rss_rounded_sigma_match":u==specified})
    return observed

def holdout_centroid(source_text):
    """Second presentation is human-mapped Eq 7, not source equation parsing."""
    compact=re.sub(r"\s+","",source_text)
    anchors=["730,690,111,486.30","730,690,516,650.91",
             "730,690,248,610.79","132,985.25"]
    if not all(a in compact for a in anchors):
        raise SourceParseFailure("NATURE_ORIGINAL_EQ7_ANCHOR_MISSING")
    # Pair of marginal combined-uncertainty estimates appear in Eq 4,5.
    terms=[Datum(F("730690111486.30"),F("0.69")),
           Datum(F("730690516650.91"),F("0.66")),
           Datum(F("-132985.25"),F("0.01"))]
    centroid=linear_map(terms,[F(1,3),F(2,3),F(1)])
    if centroid!=F("730690248610.79"):
        raise SourceParseFailure("NATURE_CENTROID_MISMATCH")
    # No paper-proven full covariance attached to this three-scalar summary.
    try:
        independent_variance(terms,[F(1,3),F(2,3),F(1)],declared=False)
        raise AssertionError("MADE_UP_COVARIANCE")
    except SourceParseFailure as ex:
        if str(ex)!="UNKNOWN_COVARIANCE_FOR_VARIANCE":raise
    return {"exact_centroid":str(centroid),
            "reported_centroid":"730690248610.79",
            "reported_centroid_sigma_kHz":"0.48",
            "reconstruct_reported_sigma":"UNKNOWN_CORRELATION_BETWEEN_TERMS",
            "manual_equation_map":"1/3*nu1+2/3*nu3+HFS",
            "original_source_anchors":True}
