"""DOM-observed Star action: no direct unauthorized API POST and no double write."""
import sys
import unittest
from pathlib import Path
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from webarena_gitlab_star_dom_action import star_project_once


class Button:
    def __init__(self,page):self.page=page
    async def count(self):return 1
    async def is_visible(self):return True
    async def inner_text(self):return 'Unstar' if self.page.starred else 'Star'
    async def click(self,**kwargs):
        self.page.clicks+=1
        if self.page.committed:self.page.starred=True
        if self.page.timeout:raise PlaywrightTimeoutError('scheduled click navigation timeout')


class Page:
    def __init__(self,committed=True,started=False,timeout=False):
        self.starred=started;self.clicks=0;self.committed=committed
        self.timeout=timeout;self.url=''
    async def goto(self,url,**kwargs):
        self.url=url
        class Response:status=200
        return Response()
    def locator(self,selector):
        assert selector=='button.star-btn.toggle-star'
        class Locator:
            def __init__(self,page):self.first=Button(page)
        return Locator(self)
    async def wait_for_timeout(self,ms):pass


class StarOnce(unittest.IsolatedAsyncioTestCase):
    async def test_one_ui_click_and_confirmed_state(self):
        page=Page()
        result=await star_project_once(page,{'path_with_namespace':'example/project','id':1})
        self.assertEqual(page.clicks,1)
        self.assertEqual(result['before'],'Star')
        self.assertEqual(result['after'],'Unstar')

    async def test_preexisting_star_not_repeated(self):
        page=Page(started=True)
        result=await star_project_once(page,{'path_with_namespace':'example/project','id':1})
        self.assertEqual(page.clicks,0)
        self.assertEqual(result['mutation_count'],0)

    async def test_navigation_timeout_requires_readback(self):
        page=Page(timeout=True)
        result=await star_project_once(page,{'path_with_namespace':'example/project','id':1})
        self.assertEqual(page.clicks,1)
        self.assertEqual(result['after'],'Unstar')

    async def test_no_confirmed_state_fails_without_retry(self):
        page=Page(committed=False,timeout=True)
        with self.assertRaises(PlaywrightTimeoutError):
            await star_project_once(page,{'path_with_namespace':'example/project','id':1})
        self.assertEqual(page.clicks,1)

    async def test_dot_segments_rejected_before_navigation(self):
        for path in ('../private','example/../private','/example/','example//private'):
            page=Page()
            with self.assertRaises(ValueError):
                await star_project_once(page,{'path_with_namespace':path,'id':1})
            self.assertEqual(page.clicks,0)

if __name__ == '__main__':unittest.main()
