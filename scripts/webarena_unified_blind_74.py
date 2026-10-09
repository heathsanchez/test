#!/usr/bin/env python3
"""74-family task-ID-blind agent: compose verified Reddit retrievals with
GitLab retrievals, four-site read/navigation and network mutation primitives.
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from webarena_unified_blind_compounding import run as run_prior
from webarena_unified_blind_four_site import site_from_start
from webarena_reddit_blind_retrieval_expansion import (
    parse_intent as parse_reddit_read_intent,
    run as run_reddit_read,
)
from webarena_shopping_sort_blind import (
    parse_intent as parse_shopping_sort_intent,
    run as run_shopping_sort,
)


def new_capability(intent: str,start_url: str) -> str | None:
    site=site_from_start(start_url)
    if site=="shopping":
        try:
            parse_shopping_sort_intent(intent)
            return "shopping_sort"
        except ValueError:
            return None
    if site!="reddit":
        return None
    try:
        kind,_=parse_reddit_read_intent(intent)
        return kind
    except ValueError:
        return None


async def run(intent: str,start_url: str,out: Path):
    kind=new_capability(intent,start_url)
    if kind=="shopping_sort":
        return await run_shopping_sort(intent,start_url,out)
    if kind is not None:
        return await run_reddit_read(intent,start_url,out)
    return await run_prior(intent,start_url,out)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--intent",required=True)
    parser.add_argument("--start-url",required=True)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))


if __name__=="__main__":
    main()
