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
    # Split camel-case forum names such as BuyItForLife before case folding.
    readable=re.sub(r"(?<=[a-z])(?=[A-Z])"," ",clean(s))
    for w in re.findall(r"[a-z0-9]+",readable.casefold()):
        if w in STOP: continue
        if w=="gaming": w="game"
        elif w.endswith("ing") and len(w)>6: w=w[:-3]
        elif w.endswith("ies") and len(w)>5: w=w[:-3]+"y"
        elif w.endswith("s") and len(w)>4: w=w[:-1]
        out.append(w)
    return out

NUMBER_WORDS={"zero":"0","one":"1","two":"2","three":"3","four":"4","five":"5","six":"6","seven":"7","eight":"8","nine":"9"}

def forum_key(value):
    tokens=re.findall(r"[a-z0-9]+",clean(value).casefold())
    return "".join(NUMBER_WORDS.get(token,token) for token in tokens)

def compact(value):
    return re.sub(r"[^a-z0-9]+", "", clean(value).casefold())

def candidate_forum_slugs(query):
    """Generate literal variants, keeping each candidate source-derived."""
    query=clean(query)
    digits_to_words={digit:word for word,digit in NUMBER_WORDS.items()}
    spelled=re.sub(
        r"\b([0-9])\b",
        lambda match: digits_to_words.get(match.group(1),match.group(1)),
        query.casefold(),
    )
    variants=(query,compact(query),re.sub(r"[^a-z0-9]+","-",query.casefold()).strip("-"),compact(spelled))
    return list(dict.fromkeys(variant for variant in variants if variant))

def sim(a,b):
    return SequenceMatcher(None,a,b).ratio()

SEMANTIC_EQUIVALENTS={
    "product":("goods","item","purchase","buy"),
    "products":("goods","items","purchase","buy"),
    "last":("lasting","durable","life"),
    "lasting":("durable","life"),
    "ever":("permanent","lifetime","life"),
    "forever":("permanent","lifetime","life"),
}

def score(description,label,slug,context=""):
    wanted=toks(description)
    observed=toks(" ".join([label,slug,context]))
    if not wanted or not observed: return 0.0
    total=0.0
    exact=0
    for w in wanted:
        equivalences=(w,)+SEMANTIC_EQUIVALENTS.get(w,())
        best=max((sim(term,o) for term in equivalences for o in observed),default=0.0)
        if best>=0.99: exact+=1
        if best>=0.68: total+=best
    return exact*10.0+total

async def resolve_forum(page,base,description,max_pages=12):
    # First resolve explicitly named forums through the site's own search.
    # Do not guess a forum slug from the user's wording.
    query=clean(description)
    if query and len(query.split()) <= 7:
        from urllib.parse import quote
        normalized=forum_key
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
    # Explicit names may be stored as compact slugs; test candidate paths
    # and verify the page's canonical forum link before accepting one.
    if query and len(query.split()) <= 7:
        from urllib.parse import quote
        variants=candidate_forum_slugs(query)
        for variant in dict.fromkeys(v for v in variants if v):
            response=await page.goto(f"{base.rstrip('/')}/f/{quote(variant)}",wait_until="networkidle",timeout=120000)
            if response is None or response.status!=200:
                continue
            canonical=urlparse(page.url).path.strip("/").split("/")
            if len(canonical)<2 or canonical[0]!="f":
                continue
            slug=canonical[1]
            if compact(slug) != compact(variant):
                continue
            row={"score":100.0,"label":slug,"slug":slug,"context":"verified direct forum URL"}
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
    wanted = forum_key(description)
    exact = [row for row in rows if wanted and (forum_key(row["slug"]) == wanted or forum_key(row["label"]) == wanted)]
    if len(exact) == 1:
        return {**exact[0], "candidates": [exact[0]]}
    rows.sort(key=lambda x:(-x["score"],x["slug"]))
    if rows[0]["score"]<=0:
        raise RuntimeError(f"no semantically relevant forum: {rows[:10]}")
    return {**rows[0],"candidates":rows[:12]}
