#!/usr/bin/env python3
"""Blind GitLab star-ranking action, based on API-observed project ranking.

User inputs are the instruction and starting site only. The evaluator and
all task metadata remain outside this agent. Mutations are issued once each;
we verify completion via independent read-only starred-project listings.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import sign_in

BASE='http://localhost:8023'
NUMBER_WORDS={'one':1,'two':2,'three':3,'four':4,'five':5,
              'six':6,'seven':7,'eight':8,'nine':9,'ten':10}


def parse_intent(intent:str)->int:
    text=re.sub(r'\s+',' ',str(intent)).strip()
    match=re.fullmatch(
        r'Star the top (three|four|five|[1-9][0-9]?) most star(?:ed|red) repos in Gitlab\.?',
        text,re.IGNORECASE,
    )
    if match is None:
        raise ValueError(f'unsupported GitLab star-ranking instruction: {text!r}')
    count=NUMBER_WORDS.get(match.group(1).casefold())
    if count is None:
        count=int(match.group(1))
    if not 1<=count<=10:
        raise ValueError('star selection count outside bounded scope')
    return count


def validate_start(start_url:str)->None:
    if start_url not in ('__GITLAB__',BASE,BASE+'/'):
        raise ValueError('GitLab star action requires a GitLab initial site')


def choose_projects(rows:list[dict],count:int)->list[dict]:
    if not isinstance(rows,list) or len(rows)<count:
        raise ValueError('fewer observed ranked GitLab projects than requested')
    ranked=[];seen=set();prior=None
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('id'),int):
            raise ValueError('GitLab project listing missing a numeric project ID')
        if not row.get('path_with_namespace'):
            raise ValueError('GitLab project missing observed path')
        stars=row.get('star_count')
        if not isinstance(stars,int) or stars<0:
            raise ValueError('GitLab project star-count evidence unavailable')
        if prior is not None and stars>prior:
            raise ValueError('provider response contradicts descending star-count order')
        prior=stars
        if row['id'] in seen:
            raise ValueError('duplicate project in observed ranking')
        seen.add(row['id'])
        ranked.append(row)
    return ranked[:count]


async def api_request(page,method:str,path:str):
    if method not in ('GET','POST') or not path.startswith('/api/v4/projects'):
        raise ValueError('request must stay inside the authenticated GitLab project API')
    result=await page.evaluate('''async ({url,method}) => {
      const r=await fetch(url,{method,credentials:'same-origin',
        headers:{'Accept':'application/json'}});
      return {status:r.status,text:await r.text()};
    }''',{'url':BASE+path,'method':method})
    if method=='POST':
        return {'status':result['status'], 'body':result.get('text','')[:400]}
    if result['status']!=200:
        raise RuntimeError(f'GitLab project GET failed {result["status"]}: {result.get("text","")[:400]}')
    return json.loads(result['text'])


async def observed_ranked_projects(page,per_page:int=100,max_pages:int=250):
    """Rank complete observed project pages without unsupported star ordering.

    This fixture's GitLab version returns HTTP 400 for order_by=star_count.
    Plain paginated project GETs are the trusted source of star counts;
    exhausting the listing is required before selecting any top-N projects.
    """
    projects=[]
    pages=0
    for page_number in range(1,max_pages+1):
        batch=await api_request(page,'GET',
            f'/api/v4/projects?per_page={per_page}&page={page_number}')
        if not isinstance(batch,list):
            raise RuntimeError('GitLab project-list response is not a list')
        pages+=1
        for project in batch:
            if not isinstance(project,dict) or not isinstance(project.get('id'),int):
                raise RuntimeError('GitLab project list contains an invalid ID')
            if not isinstance(project.get('star_count'),int) or project['star_count']<0:
                raise RuntimeError('GitLab project list contains invalid star evidence')
            if not project.get('path_with_namespace'):
                raise RuntimeError('GitLab project list lacks a project name')
        projects.extend(batch)
        if len(batch)<per_page:
            break
    else:
        raise RuntimeError('GitLab project listing exceeds bounded pagination; ranking UNKNOWN')
    if not projects:
        raise RuntimeError('GitLab project listing empty')
    # Deterministic tie-break affects only equal-star projects. Preserve
    # observed project identifiers so the readback verifies exactly these.
    return sorted(projects,key=lambda project:(-project['star_count'],project['id'])),pages


async def perform(page,count:int)->dict:
    ranked,pages=await observed_ranked_projects(page)
    chosen=choose_projects(ranked,count)
    receipt=[]
    for project in chosen:
        response=await api_request(page,'POST',f'/api/v4/projects/{project["id"]}/star')
        if response['status'] not in (200,201,304):
            raise RuntimeError(f'GitLab star write for project {project["id"]} returned HTTP {response["status"]}')
        receipt.append({'project':project['path_with_namespace'],
                        'id':project['id'],'status':response['status']})
    # Readback is safe to repeat; never repeat a write after an ambiguous POST.
    starred=set()
    for index in range(1,31):
        batch=await api_request(page,'GET',
            f'/api/v4/projects?starred=true&per_page=100&page={index}')
        if not isinstance(batch,list):
            raise RuntimeError('starred-project readback returned non-list')
        for project in batch:
            if isinstance(project,dict) and isinstance(project.get('id'),int):
                starred.add(project['id'])
        if len(batch)<100:
            break
    else:
        raise RuntimeError('starred-project readback exceeds bounded pagination')
    selected_ids=[project['id'] for project in chosen]
    if not all(identifier in starred for identifier in selected_ids):
        raise RuntimeError('GitLab starred-project readback did not confirm all writes')
    return {'capability':'gitlab_star_top_projects',
            'selected_count':count,
            'observed_project_count':len(ranked),
            'observed_pages':pages,
            'ranked_projects':[{'id':p['id'],'path':p['path_with_namespace'],
                                'observed_stars':p['star_count']} for p in chosen],
            'writes':receipt,'verified_project_ids':selected_ids}


async def run(intent:str,start_url:str,out:Path):
    validate_start(start_url)
    count=parse_intent(intent)
    out.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as playwright:
        browser=await playwright.chromium.launch(headless=True)
        context=await browser.new_context(
            record_har_path=str(out/'network.har'),record_har_mode='full')
        page=await context.new_page()
        try:
            await sign_in(page)
            evidence=await perform(page,count)
        finally:
            await context.close()
            await browser.close()
    response={'task_type':'MUTATE','status':'SUCCESS',
              'retrieved_data':None,'error_details':None}
    (out/'agent_response.json').write_text(json.dumps(response,indent=2)+'\n')
    (out/'capability_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,ensure_ascii=False),flush=True)
    return response


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--intent',required=True)
    parser.add_argument('--start-url',required=True)
    parser.add_argument('--output-dir',required=True)
    args=parser.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))


if __name__=='__main__':main()
