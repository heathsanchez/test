#!/usr/bin/env python3
from __future__ import annotations
import asyncio
from urllib.parse import urlparse
import webarena_gitlab_search_to_reddit as base
import webarena_shopping_to_reddit_reviews as forum_base

async def choose_forum(page,description):
    r=await page.goto(base.REDDIT,wait_until="networkidle",timeout=120000)
    if r is None or r.status not in (200,302):
        raise RuntimeError("reddit home failed")
    links=page.locator("a[href]")
    rows=[]; seen=set()
    for i in range(await links.count()):
        href=await links.nth(i).get_attribute("href")
        if not href:
            continue
        parts=[p for p in urlparse(href).path.split("/") if p]
        if len(parts)<2 or parts[0]!="f":
            continue
        slug=parts[1]
        if slug in seen:
            continue
        seen.add(slug)
        label=forum_base.clean(await links.nth(i).inner_text())
        rows.append((forum_base.forum_score(description,label,slug),label,slug))
    if not rows:
        raise RuntimeError("no discussion forums discovered")
    rows.sort(key=lambda x:x[0],reverse=True)
    if rows[0][0]<=0:
        raise RuntimeError(f"no relevant forum: {rows[:10]}")
    return {"score":rows[0][0],"label":rows[0][1],"slug":rows[0][2],"candidates":rows[:10]}

base.choose_forum=choose_forum

if __name__=="__main__":
    asyncio.run(base.main())
