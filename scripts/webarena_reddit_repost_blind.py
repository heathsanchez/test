#!/usr/bin/env python3
"""Task-ID-blind Reddit image URL repost through observed site content."""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright

BASE = "http://localhost:9999"


def parse_intent(intent: str, start_url: str) -> dict:
    start = str(start_url).strip()
    mstart = re.fullmatch(r"__REDDIT__/f/([A-Za-z][A-Za-z0-9_-]{0,60})/?", start)
    if not mstart:
        raise ValueError("Repost requires a single observed source Reddit forum URL")
    text = re.sub(r"\s+", " ", str(intent)).strip()
    match = re.fullmatch(
        r'Re-post the image of (.+?) from this forum to '
        r'([A-Za-z][A-Za-z0-9_-]{0,60}) forum using the image URL '
        r'and title "([^"]{1,250})"\.?',
        text, flags=re.I,
    )
    if not match:
        raise ValueError("Unsupported image repost intent or destination forum")
    image_phrase, dest, post_title = match.groups()
    if not image_phrase.strip() or ".." in dest or dest in (".", ".."):
        raise ValueError("Malformed image or unsafe destination")
    return {
        "source_forum": mstart.group(1),
        "image_phrase": image_phrase.strip(),
        "destination_forum": dest,
        "post_title": post_title,
    }


async def run(intent: str, start_url: str, output_dir: Path):
    request = parse_intent(intent, start_url)
    from webarena_reddit_repost_image import find_source, submit_url
    from webarena_reddit_submit_v3 import AUTH, observed_postcondition
    # The upstream verified source-image helper reads the pics forum. Admit
    # only that observed scope until a more general source collector qualifies.
    if request["source_forum"].casefold() != "pics":
        raise ValueError("Source forum lacks a verified image-search capability")
    output_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            extra_http_headers=AUTH,
            record_har_path=str(output_dir / "network.har"),
            record_har_mode="full",
        )
        page = await context.new_page()
        try:
            source = await find_source(page, BASE, request["image_phrase"])
            # One submitted mutation. Never retry a possibly committed POST.
            posted = await submit_url(
                page, BASE, request["destination_forum"],
                request["post_title"], source["href"],
            )
            if not await observed_postcondition(page, {
                "forum": request["destination_forum"],
                "title": request["post_title"],
            }):
                raise RuntimeError("Observed repost page did not prove target forum and title")
        finally:
            await context.close()
            await browser.close()
    response = {"task_type": "MUTATE", "status": "SUCCESS",
                "retrieved_data": None, "error_details": None}
    evidence = {"instruction_parameters": request, "source_post": source,
                "submitted_destination": posted, "confirmed_postcondition": True}
    (output_dir / "agent_response.json").write_text(json.dumps(response, indent=2) + "\n")
    (output_dir / "capability_evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(evidence, ensure_ascii=False))
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", required=True)
    parser.add_argument("--start-url", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    asyncio.run(run(args.intent, args.start_url, Path(args.output_dir)))


if __name__ == "__main__":
    main()
