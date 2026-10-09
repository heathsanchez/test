#!/usr/bin/env python3
"""Observe Magento AJAX review pages, preserving independent repeated titles.

Only same-origin paging links seen in the browser authorize subsequent
read-only GETs. An unchanged product URL does not imply review completion.
"""
from __future__ import annotations

from urllib.parse import urljoin,urlparse


def trusted_review_page(base,href):
    target=urljoin(base.rstrip('/')+'/',str(href))
    actual=urlparse(target)
    allowed=urlparse(base)
    if (actual.scheme,actual.hostname,actual.port)!=(allowed.scheme,allowed.hostname,allowed.port):
        raise RuntimeError('review pager points outside the observed Shopping origin')
    if not actual.path.startswith('/review/product/listAjax/'):
        raise RuntimeError('review pager points outside the observed review listing')
    return target


async def collect_all_reviews(page,base,read_rows,max_pages=20):
    """Return (observed rows, page URLs), without deduplicating customer reviews."""
    found=[]
    visited=[page.url]
    seen={page.url}
    for _ in range(max_pages):
        observed=await read_rows(page)
        if not isinstance(observed,list):
            raise RuntimeError('review reader did not produce an observed list')
        found.extend(observed)
        links=page.locator('.pages-item-next a')
        next_url=None
        for index in range(min(await links.count(),20)):
            raw=await links.nth(index).get_attribute('href')
            if not raw:
                continue
            target=trusted_review_page(base,raw)
            if next_url is None:
                next_url=target
            elif next_url!=target:
                raise RuntimeError('conflicting review pager destinations')
        if next_url is None:
            return found,visited
        if next_url in seen:
            raise RuntimeError('review pager cycle; completeness not established')
        seen.add(next_url)
        visited.append(next_url)
        reply=await page.goto(next_url,wait_until='networkidle',timeout=120000)
        if reply is None or reply.status!=200:
            raise RuntimeError(f'review page fetch returned {getattr(reply,"status",None)}')
    raise RuntimeError('review page count exceeds qualification bound')
