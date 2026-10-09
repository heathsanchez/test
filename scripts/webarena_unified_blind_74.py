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


def new_capability(intent: str,start_url: str) -> str | None:
    if site_from_start(start_url)!="reddit":
        return None
    try:
        kind,_=parse_reddit_read_intent(intent)
        return kind
    except ValueError:
        return None


async def run(intent: str,start_url: str,out: Path):
    if new_capability(intent,start_url) is not None:
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
