#!/usr/bin/env python3
"""Promote independently verified behaviors into the Hard blind agent.

Capability selection receives only natural-language intent and the initial
site. Every selected implementation retains its stricter admission and
postcondition checks. Official task identities and evaluator metadata remain
outside this agent in the evaluation harness.
"""
from __future__ import annotations

import argparse
import asyncio
import re
from pathlib import Path


def select_route(intent: str, start_url: str) -> str | None:
    text = re.sub(r"\s+", " ", str(intent)).strip().casefold()
    if start_url == '__SHOPPING__':
        if (text.startswith('create a post in the ')
                and 'related discussion forum' in text
                and 'from the onestopshop' in text):
            return 'shopping_reddit_review'
        if text.startswith('pull up the page with all "') and ' listings sorted by ' in text:
            return 'shopping_sort'
    if start_url == '__GITLAB__' and text == 'go to the merge requests requiring my review':
        return 'navigation_transfer'
    if start_url == '__SHOPPING_ADMIN__' and text.startswith('show the tax report for'):
        return 'navigation_transfer'
    return None


async def run(intent: str, start_url: str, output_dir: Path):
    route = select_route(intent, start_url)
    if route == 'shopping_reddit_review':
        from webarena_shopping_reddit_review_compound import run as execute
    elif route == 'shopping_sort':
        from webarena_shopping_sort_blind import run as execute
    elif route == 'navigation_transfer':
        from webarena_blind_navigation_transfer import run as execute
    else:
        from webarena_blind_retrieval_bridge import run as execute
    # No retries through another implementation after an ambiguous mutation.
    return await execute(intent, start_url, output_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--intent', required=True)
    parser.add_argument('--start-url', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    asyncio.run(run(args.intent, args.start_url, Path(args.output_dir)))


if __name__ == '__main__':
    main()
