#!/usr/bin/env python3
"""Blind GitLab retrieval adapters over existing verified API/UI capabilities.

These adapters compile only natural-language intent and initial URL.
The benchmark task identity and expected result stay in the external harness.
"""
from __future__ import annotations
import argparse,asyncio,json,re
from pathlib import Path
from urllib.parse import quote,urlparse
from playwright.async_api import async_playwright

from webarena_unified_blind_four_site import run as run_existing
from webarena_gitlab_commit_counts import BASE,sign_in
from webarena_gitlab_ssh_clone import (
    api_json as projects_json,semantic_query,choose_project,
)
from webarena_gitlab_project_members import (
    resolve_project,members,
)
from webarena_gitlab_contributor_summary import (
    contributors,resolve_user,project_path_from_url,
)
from webarena_gitlab_top3_contributors import (
    api_json as top3_json,choose_project as choose_top3,
)


def clean(value):
    return re.sub(r"\s+"," ",str(value)).strip()


def parse_gitlab_retrieval(intent):
    text=clean(intent)
    m=re.fullmatch(
        r"Get the URL to clone (.+?) with SSH\. Return the URL only, "
        r"without any additional details\.",
        text,re.I,
    )
    if m:
        return "ssh_clone",{"description":m.group(1)}
    m=re.fullmatch(
        r"Get the usernames of other users who have access to my repo (.+)",
        text,re.I,
    )
    if m:
        return "project_members",{"description":m.group(1)}
    m=re.fullmatch(
        r"Get the number of commits of the contributor who has the most "
        r"commits to branch ([^ ]+) in the current repository",
        text,re.I,
    )
    if m:
        return "top_contributor_count",{"branch":m.group(1)}
    m=re.match(
        r"Get the full name, username, user location and email of the "
        r"contributor who has the most commits to branch ([^ ]+) "
        r"in the current repository(?:\.|$)",
        text,re.I,
    )
    if m:
        return "top_contributor_profile",{"branch":m.group(1)}
    m=re.fullmatch(
        r"Get the email addresses of the top 3 contributors "
        r"\(by commit count\) to (.+?) repo",
        text,re.I,
    )
    if m:
        return "top_three_emails",{"description":m.group(1)}
    return None


def search_term(description):
    # Find a source-derived topic token, not an evaluator-provided project ID.
    text=clean(description)
    m=re.search(r"\b(?:building|using|with)\s+([A-Za-z0-9+-]+)",text,re.I)
    if m:
        return m.group(1)
    words=[w for w in re.findall(r"[a-z0-9]+",text.casefold())
           if w not in {"the","best","most","project","repo","related","guide","on","for"}]
    if not words:
        raise ValueError("no searchable project topic in user request")
    return max(words,key=len)


async def execute(page,capability,args,start_url):
    if capability=="ssh_clone":
        wanted=args["description"]
        q=semantic_query(wanted)
        projects=await projects_json(page,BASE+"/api/v4/projects?simple=true&per_page=100&search="+quote(q,safe=""))
        if not projects:raise RuntimeError("no candidate GitLab projects from observed search")
        chosen=choose_project(wanted,projects)
        ssh=chosen.get("ssh_url_to_repo")
        if not ssh:raise RuntimeError("observed GitLab project has no SSH clone URL")
        return [ssh],{"route":capability,"requested":wanted,"search":q,
                      "project":chosen.get("path_with_namespace"),"observed_ssh":ssh}

    if capability=="project_members":
        wanted=args["description"]
        project=await resolve_project(page,BASE,wanted)
        names,excerpt,url=await members(page,BASE,project["path"])
        return names,{"route":capability,"wanted":wanted,"project":project,
                      "members_url":url,"observed_count":len(names)}

    if capability in ("top_contributor_count","top_contributor_profile"):
        path=start_url.replace("__GITLAB__",BASE,1)
        repo=project_path_from_url(path)
        if len([part for part in repo.split("/") if part])<2:
            raise RuntimeError("contributor query requires repository start URL")
        rows=await contributors(page,repo,args["branch"])
        top=rows[0]
        if capability=="top_contributor_count":
            data=[int(top["commits"])]
            evidence={"route":capability,"repo":repo,"branch":args["branch"],
                      "observed_contributors":len(rows),"top_commit_count":data[0]}
        else:
            profile=await resolve_user(page,top)
            data=[{
                "full_name":clean(profile.get("name","")) or clean(top.get("name","")),
                "username":clean(profile.get("username","")),
                "user_location":clean(profile.get("location","")),
                "email":clean(top.get("email","")),
            }]
            evidence={"route":capability,"repo":repo,"branch":args["branch"],
                      "observed_contributors":len(rows),
                      "resolved_username":data[0]["username"]}
        return data,evidence

    if capability=="top_three_emails":
        wanted=args["description"]
        q=search_term(wanted)
        projects=await top3_json(
            page,BASE+"/api/v4/projects?simple=true&per_page=100&search="+quote(q,safe="")
        )
        if not projects:raise RuntimeError("no GitLab project candidates")
        chosen=choose_top3(wanted,projects)
        contributors_seen=await top3_json(
            page,f"{BASE}/api/v4/projects/{chosen['id']}/repository/contributors?order_by=commits&sort=desc&per_page=100"
        )
        ranked=[c for c in contributors_seen if c.get("email")]
        if len(ranked)<3:raise RuntimeError("fewer than three contributors with emails")
        values=[str(row["email"]).strip() for row in ranked[:3]]
        return values,{"route":capability,"requested":wanted,"search":q,
                       "project":chosen.get("path_with_namespace"),
                       "observed_contributor_count":len(contributors_seen)}

    raise ValueError(f"unsupported GitLab retrieval capability: {capability}")


async def run(intent,start_url,out):
    parsed=parse_gitlab_retrieval(intent)
    if parsed is None:
        return await run_existing(intent,start_url,out)
    if not start_url.startswith("__GITLAB__"):
        raise ValueError("GitLab retrieval requires GitLab initial site")
    capability,args=parsed
    out.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page()
        try:
            await sign_in(page)
            data,evidence=await execute(page,capability,args,start_url)
        finally:
            await browser.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS",
              "retrieved_data":data,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps({"capability":capability,"response":response},ensure_ascii=False))
    return response


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--intent",required=True)
    parser.add_argument("--start-url",required=True)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))


if __name__=="__main__":
    main()
