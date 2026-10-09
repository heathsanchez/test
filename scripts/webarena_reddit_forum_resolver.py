#!/usr/bin/env python3
from __future__ import annotations
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

STOP={"the","a","an","related","discussion","forum","forums","implementation"}

def clean(s):
    return re.sub(r"\s+"," ",str(s)).strip()

def toks(s):
    out=[]
    for w in re.findall(r"[a-z0-9]+",clean(s).casefold()):
        if w in STOP: continue
        if w=="gaming": w="game"
        elif w.endswith("ing") and len(w)>6: w=w[:-3]
        elif w.endswith("ies") and len(w)>5: w=w[:-3]+"y"
        elif w.endswith("s") and len(w)>4: w=w[:-1]
        out.append(w)
    return out

def sim(a,b):
    return SequenceMatcher(None,a,b).ratio()

def score(description,label,slug,context=""):
    wanted=toks(description)
    observed=toks(" ".join([label,slug,context]))
    if not wanted or not observed: return 0.0
    total=0.0
    exact=0
    for w in wanted:
        best=max((sim(w,o) for o in observed),default=0.0)
        if best>=0.99: exact+=1
        if best>=0.68: total+=best
    return exact*10.0+total

async def resolve_forum(page,base,description,max_pages=12):
    # First resolve explicitly named forums through the site's own search.
    # Do not guess a forum slug from the user's wording.
    query=clean(description)
    if query and len(query.split()) <= 7:
        from urllib.parse import quote
        normalized=lambda value: re.sub(r"[^a-z0-9]+","",clean(value).casefold())
        wanted=normalized(query)
        for url in (
            f"{base.rstrip('/')}/forums/search?q={quote(query)}",
            f"{base.rstrip('/')}/search?q={quote(query)}",
        ):
            response=await page.goto(url,wait_until="networkidle",timeout=120000)
            if response is None or response.status!=200:
                continue
            links=page.locator('a[href^="/f/"]')
            matches={}
            for i in range(min(await links.count(),300)):
                link=links.nth(i)
                href=await link.get_attribute("href") or ""
                parts=[p for p in urlparse(href).path.split("/") if p]
                if len(parts)<2 or parts[0]!="f":
                    continue
                slug=parts[1]
                label=clean(await link.inner_text())
                if normalized(slug)==wanted or normalized(label)==wanted:
                    matches[slug]={"score":100.0,"label":label,"slug":slug,"context":"forum search"}
            if len(matches)==1:
                row=next(iter(matches.values()))
                return {**row,"candidates":[row]}
    rows=[]; seen=set(); empty=0
    for n in range(1,max_pages+1):
        r=await page.goto(f"{base.rstrip('/')}/forums/by_name/{n}",wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200:
            empty+=1
            if empty>=2: break
            continue
        links=page.locator('a[href^="/f/"]')
        count=await links.count()
        if count==0:
            empty+=1
            if empty>=2: break
            continue
        empty=0
        for i in range(count):
            link=links.nth(i)
            href=await link.get_attribute("href")
            if not href: continue
            parts=[p for p in urlparse(href).path.split("/") if p]
            if len(parts)<2 or parts[0]!="f": continue
            slug=parts[1]
            if slug in seen: continue
            seen.add(slug)
            label=clean(await link.inner_text())
            context=""
            try:
                context=clean(await link.locator("xpath=..").inner_text())
            except Exception:
                pass
            rows.append({"score":score(description,label,slug,context),"label":label,"slug":slug,"context":context})
    if not rows:
        raise RuntimeError("forum index returned no forums")
    # Resolve explicit names by normalized exact match before semantic scoring.
    # This handles display aliases such as "explain like im 5" without
    # changing the policy for semantically chosen forums.
    wanted = re.sub(r"[^a-z0-9]+", "", clean(description).casefold())
    exact = [row for row in rows if wanted and (re.sub(r"[^a-z0-9]+", "", row["slug"].casefold()) == wanted or re.sub(r"[^a-z0-9]+", "", row["label"].casefold()) == wanted)]
    if len(exact) == 1:
        return {**exact[0], "candidates": [exact[0]]}
    rows.sort(key=lambda x:(-x["score"],x["slug"]))
    if rows[0]["score"]<=0:
        raise RuntimeError(f"no semantically relevant forum: {rows[:10]}")
    return {**rows[0],"candidates":rows[:12]}
