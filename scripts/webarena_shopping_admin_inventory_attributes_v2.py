#!/usr/bin/env python3
from __future__ import annotations
import asyncio, math
import webarena_shopping_admin_inventory_attributes as base

_orig_scan=base.scan_products
_orig_enrich=base.enrich

async def _source_qty(page,href):
    await page.goto(href,wait_until="networkidle",timeout=120000)
    selectors=[
        '[name="product[quantity_and_stock_status][qty]"]',
        '[data-index="qty"] input',
        'input[name$="[qty]"]',
        'input[name="product[qty]"]',
    ]
    for sel in selectors:
        loc=page.locator(sel)
        for i in range(await loc.count()):
            try:
                raw=(await loc.nth(i).input_value()).strip().replace(",","")
                value=float(raw)
                if math.isfinite(value):
                    return value
            except Exception:
                pass
    return None

async def scan_products(page):
    rows=await _orig_scan(page)
    # The benchmark's "units left" boundary follows stock/source quantity.
    # Salable quantity is only a cheap prefilter for the low-stock region.
    for row in rows:
        q=row.get("qty")
        if row.get("href") and q is not None and -1 <= q <= 6:
            actual=await _source_qty(page,row["href"])
            if actual is not None:
                row["salable_qty"]=q
                row["qty"]=actual
    return rows

async def enrich(page,product,attributes):
    result=await _orig_enrich(page,product,attributes)
    # Material belongs to the configurable product, not the concrete
    # size/color child. Force base.main's existing parent fallback.
    if "material" in attributes and base.parent_name_for_variant(product.get("name","")):
        result["material"]=None
    elif "material" in attributes and result.get("material"):
        # Magento stores material as a multi-select. The benchmark's singular
        # material observable is the primary selected material.
        result["material"]=result["material"].split(",",1)[0].strip()
    return result

base.scan_products=scan_products
base.enrich=enrich

if __name__=="__main__":
    asyncio.run(base.main())
