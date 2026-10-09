#!/usr/bin/env python3
"""One authenticated GitLab star UI action, with fail-closed DOM readback."""
from __future__ import annotations

from urllib.parse import quote
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

BASE = 'http://localhost:8023'


async def star_project_once(page, project):
    path = str(project.get('path_with_namespace', ''))
    parts = path.split('/')
    if len(parts) < 2 or any(part in ('', '.', '..') for part in parts):
        raise ValueError('observed GitLab project path is not safe')
    target = BASE + '/' + quote(path, safe='/')
    response = await page.goto(target, wait_until='networkidle', timeout=120000)
    if response is None or response.status != 200:
        raise RuntimeError('GitLab project page could not be observed')
    control = page.locator('button.star-btn.toggle-star').first
    if await control.count() != 1 or not await control.is_visible():
        raise RuntimeError('GitLab project star control unavailable')
    before = (await control.inner_text()).strip()
    if before == 'Unstar':
        return {'observed_page': target, 'before': before, 'after': before,
                'mutation_count': 0}
    if before != 'Star':
        raise RuntimeError(f'uncertain GitLab star control state: {before!r}')
    timed_out = False
    try:
        await control.click(timeout=30000)
    except PlaywrightTimeoutError:
        timed_out = True
    # Never repeat a potentially committed mutation. Observe the updated
    # rendered button and retain independent starred-list readback upstream.
    after = (await control.inner_text()).strip()
    for _ in range(40):
        if after == 'Unstar':
            break
        await page.wait_for_timeout(250)
        after = (await control.inner_text()).strip()
    if timed_out and after != 'Unstar':
        raise PlaywrightTimeoutError('GitLab star click timed out without confirmed state')
    if after != 'Unstar':
        raise RuntimeError(f'GitLab star state not observed after action: {after!r}')
    return {'observed_page': target, 'before': before, 'after': after,
            'mutation_count': 1}
