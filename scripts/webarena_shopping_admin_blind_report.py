#!/usr/bin/env python3
"""Task-ID-blind Shopping Admin Orders Report navigation capability.

This compiles user-supplied date language to the already qualified Magento
report URL and observes the actual resulting document response. It neither
reads benchmark instantiation fields nor fabricates a network result.
"""
from __future__ import annotations
import re
from datetime import date
from webarena_shopping_admin_orders_report_nav import parse_date_phrase, report_url


def parse_report_range(intent: str) -> tuple[date,date]:
    text=re.sub(r"\s+"," ",str(intent)).strip()
    explicit=re.fullmatch(
        r"Show the orders report from ([A-Za-z]+\s+\d{1,2},\s+\d{4}) "
        r"to ([A-Za-z]+\s+\d{1,2},\s+\d{4})\.",
        text,re.I,
    )
    if explicit:
        start,end=(parse_date_phrase(x) for x in explicit.groups())
    else:
        prior=re.fullmatch(
            r"Show the sales order report for(?: for)? last year "
            r"\(today is ([A-Za-z]+\s+\d{1,2},\s+\d{4})\)\.",
            text,re.I,
        )
        if prior is None:
            raise ValueError(f"unsupported report intent: {text!r}")
        current=parse_date_phrase(prior.group(1))
        y=current.year-1
        start,end=date(y,1,1),date(y,12,31)
    if end<start:
        raise ValueError("report end precedes report start")
    return start,end


async def navigate_report(page,intent: str,base: str="http://localhost:7780/admin"):
    start,end=parse_report_range(intent)
    target=report_url(base,start,end)
    response=await page.goto(target,wait_until="networkidle",timeout=120000)
    if response is None or response.status!=200:
        raise RuntimeError(f"report response invalid: {getattr(response,'status',None)}")
    title=await page.title()
    if "Orders Report" not in title:
        raise RuntimeError(f"unexpected document title: {title!r}")
    return {
        "capability":"admin_orders_report_navigation",
        "range_start":start.isoformat(),
        "range_end":end.isoformat(),
        "observed_url":page.url,
        "observed_status":response.status,
        "observed_title":title,
    }
