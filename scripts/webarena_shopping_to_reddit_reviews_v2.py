#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import webarena_shopping_to_reddit_reviews as base
from webarena_reddit_forum_resolver import resolve_forum

async def choose_forum(page,description):
    return await resolve_forum(page,base.REDDIT,description)

base.choose_forum=choose_forum

if __name__=="__main__":
    asyncio.run(base.main())
