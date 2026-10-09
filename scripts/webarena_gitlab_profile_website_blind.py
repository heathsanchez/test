#!/usr/bin/env python3
"""Task-ID-blind GitLab profile website mutation with independent readback."""
from __future__ import annotations
import argparse,asyncio,json,re
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE, sign_in


def parse_profile_website_intent(intent):
    text=" ".join(str(intent).split())
    match=re.fullmatch(
        r"set the homepage URL on my GitLab profile to ([^ ]+)",
        text,re.I,
    )
    if match is None:
        raise ValueError("unsupported GitLab profile mutation intent")
    target=match.group(1).rstrip(".")
    if not re.fullmatch(r"(?:https?://)?[A-Za-z0-9.-]+(?:/[A-Za-z0-9._~%/+?=&-]*)?",target):
        raise ValueError("invalid profile website URL")
    return target


def valid_form_website(value):
    text=str(value).strip()
    if re.match(r"^https?://",text,re.I):
        return text
    return "https://"+text


def website_key(value):
    text=str(value or "").strip().rstrip("/")
    for prefix in ("https://","http://"):
        if text.casefold().startswith(prefix):
            text=text[len(prefix):]
            break
    return text.casefold()


async def profile_page(page):
    observations=[]
    for path in ("/-/profile","/profile"):
        url=BASE+path
        response=await page.goto(url,wait_until="networkidle",timeout=120000)
        if response is None or response.status!=200:
            observations.append({"url":url,"status":None if response is None else response.status})
            continue
        selectors=(
            'input[name="user[website_url]"]',
            'input#user_website_url',
            'input[name="user[website]"]',
            'input#user_website',
        )
        for selector in selectors:
            target=page.locator(selector).first
            if await target.count():
                return {"field":target,"selector":selector,"url":page.url,
                        "observations":observations}
        observations.append({"url":url,"status":200,"found_field":False})
    raise RuntimeError("GitLab profile website field unavailable "+json.dumps(observations))


async def set_website(page,intent):
    requested=parse_profile_website_intent(intent)
    await sign_in(page)
    profile=await profile_page(page)
    field=profile["field"]
    prior=await field.input_value()
    form_value=valid_form_website(requested)
    await field.fill(form_value)
    form=field.locator("xpath=ancestor::form[1]")
    if await form.count()==0:
        raise RuntimeError("profile website field is not in a form")
    # Exactly one write. Wait for an actual profile POST response before
    # opening the form again; requestSubmit returns before navigation settles.
    async with page.expect_response(
        lambda response:
            response.request.method=="POST" and
            "/-/profile" in response.url,
        timeout=40000,
    ) as receipt:
        await form.evaluate("(f)=>f.requestSubmit()")
    submitted_response=await receipt.value
    if submitted_response.status not in (200,302):
        raise RuntimeError(f"GitLab profile submission HTTP {submitted_response.status}")
    try:
        await page.wait_for_load_state("networkidle",timeout=120000)
    except Exception:
        pass
    # Safe GET-only polling handles delayed commits and/or cached first reads.
    # The mutation itself is never replayed.
    readback=None
    observed=""
    for attempt in range(7):
        readback=await profile_page(page)
        observed=await readback["field"].input_value()
        if website_key(observed)==website_key(requested):
            break
        await page.wait_for_timeout(min(250*(attempt+1),1500))
    if website_key(observed)!=website_key(requested):
        errors=[]
        for selector in (".flash-container",".flash-alert",".alert",".invalid-feedback",".field_with_errors"):
            for idx in range(min(await page.locator(selector).count(),10)):
                msg=" ".join((await page.locator(selector).nth(idx).inner_text()).split())
                if msg and msg not in errors:
                    errors.append(msg[:240])
        raise RuntimeError(
            "GitLab profile website readback differs: "
            +json.dumps({"requested":requested,"submitted":form_value,
                         "observed":observed,"visible_validation_errors":errors[:10]})
        )
    return {
        "capability":"gitlab_profile_website_mutation",
        "requested":requested,"submitted":form_value,"previous":prior,"observed":observed,
        "form_url":profile["url"],"readback_url":readback["url"],
        "submitted_response_status":submitted_response.status,
        "field_selector":profile["selector"],
    }


async def run(intent,start_url,output_dir):
    if start_url!="__GITLAB__" and start_url!=BASE:
        raise ValueError("profile mutation requires GitLab starting site")
    output_dir.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as playwright:
        browser=await playwright.chromium.launch(headless=True)
        context=await browser.new_context(record_har_path=str(output_dir/"network.har"),
            record_har_mode="full")
        page=await context.new_page()
        try:
            evidence=await set_website(page,intent)
        finally:
            await context.close()
            await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS",
              "retrieved_data":None,"error_details":None}
    (output_dir/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (output_dir/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--intent",required=True)
    parser.add_argument("--start-url",required=True)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))


if __name__=="__main__":
    main()
