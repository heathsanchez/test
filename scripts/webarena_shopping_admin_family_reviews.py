#!/usr/bin/env python3
from __future__ import annotations
import asyncio, re
import webarena_shopping_admin_review_ratings as app

async def family_reviews(page,product):
    terms=app.product_terms(product)
    if not terms:
        raise RuntimeError("empty family query")
    await app.apply_product_filter(page,terms[0])
    out=[]; seen=set()
    for _ in range(80):
        table,headers=await app.live_table(page)
        lower=[h.lower() for h in headers]
        ix={k:lower.index(k) for k in ["id","title","nickname","product"]}
        rows=table.locator("tbody tr")
        for ri in range(await rows.count()):
            row=rows.nth(ri); cells=row.locator("td")
            if await cells.count()<=max(ix.values()):
                continue
            rid=app.clean(await cells.nth(ix["id"]).inner_text())
            if not rid or rid in seen:
                continue
            seen.add(rid)
            pname=app.clean(await cells.nth(ix["product"]).inner_text())
            if not all(app.term_match(term,pname) for term in terms):
                continue
            links=row.locator('a[href*="/review/product/edit/"]')
            href=await links.first.get_attribute("href") if await links.count() else None
            out.append({
                "review_id":rid,
                "product":pname,
                "title":app.clean(await cells.nth(ix["title"]).inner_text()),
                "nickname":app.clean(await cells.nth(ix["nickname"]).inner_text()),
                "href":href,
            })
        if not await app.next_page(page):
            break
    return out

app.matching_reviews=family_reviews

if __name__=="__main__":
    asyncio.run(app.main())
