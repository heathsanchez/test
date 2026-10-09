#!/usr/bin/env python3
"""Single blind entrypoint preserving promoted four-site and GitLab capability reuse.

The only runtime task inputs are natural-language instruction and start URL.
Additional Shopping mutations are admitted by their declared intent grammar
and independently verified by observed post-state / official external gate.
"""
from __future__ import annotations

import argparse
import asyncio
import re
from pathlib import Path

from webarena_unified_gitlab_readonly_expansion import run as run_existing
from webarena_unified_blind_four_site import site_from_start
from webarena_shopping_wishlist_blind import (
    authorize_intent as authorize_wishlist,
    run as run_wishlist,
)


def select_new_primitive(intent: str,start_url: str) -> str | None:
    site=site_from_start(start_url)
    if site!="shopping":
        return None
    text=re.sub(r"\s+"," ",str(intent)).strip()
    if text.casefold()=="add the product on the current page to my wishlist":
        authorize_wishlist(intent)
        return "shopping_wishlist_add"
    return None


async def run(intent: str,start_url: str,output_dir: Path):
    candidate=select_new_primitive(intent,start_url)
    if candidate=="shopping_wishlist_add":
        return await run_wishlist(intent,start_url,output_dir)
    return await run_existing(intent,start_url,output_dir)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--intent",required=True)
    parser.add_argument("--start-url",required=True)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))


if __name__=="__main__":
    main()
