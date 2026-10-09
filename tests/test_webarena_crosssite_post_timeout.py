"""A delayed post-submit navigation cannot trigger a second cross-site write."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from webarena_gitlab_to_reddit_promote import submit_url_post

TITLE="Chrome extension that replaces occurrences of 'the cloud' with 'my butt'"

class Response:
    status=200

class Locator:
    def __init__(self,page,kind):self.page=page;self.kind=kind
    @property
    def first(self):return self
    async def count(self):return 1
    def filter(self,**kwargs):return self
    def locator(self,css):
        if "title" in css:return Locator(self.page,"title")
        if "url" in css:return Locator(self.page,"url")
        if "forum" in css:return Locator(self.page,"forum")
        raise AssertionError(css)
    def get_by_role(self,role,name):return Locator(self.page,"button")
    async def fill(self,value):self.page.values[self.kind]=value
    async def input_value(self):return "10016"
    async def inner_text(self,timeout=0):return self.page.visible
    async def click(self):
        self.page.click_count+=1
        if self.page.committed:
            self.page.url="http://localhost:9999/f/LifeProTips/2/chrome-extension-that-replaces-occurrences"
        raise PlaywrightTimeoutError("waiting for scheduled navigations to finish")

class Page:
    def __init__(self,committed):
        self.committed=committed;self.click_count=0;self.values={}
        self.url="http://localhost:9999/submit/LifeProTips"
        self.visible=TITLE if committed else "Submission failed"
    async def goto(self,url,**kwargs):self.url=url;return Response()
    def locator(self,css):return Locator(self,"body" if css=="body" else "form")
    async def wait_for_load_state(self,*args,**kwargs):pass

class CrossSiteTimeout(unittest.IsolatedAsyncioTestCase):
    async def test_committed_navigation_timeout_accepted_without_retry(self):
        page=Page(committed=True)
        response=await submit_url_post(page,"LifeProTips",TITLE,"http://localhost:8023/byteblaze/cloud-to-butt")
        self.assertEqual(page.click_count,1)
        self.assertIn("/f/LifeProTips/2/",response["final_url"])

    async def test_unconfirmed_post_fails_closed_without_retry(self):
        page=Page(committed=False)
        with self.assertRaises(PlaywrightTimeoutError):
            await submit_url_post(page,"LifeProTips",TITLE,"http://localhost:8023/byteblaze/cloud-to-butt")
        self.assertEqual(page.click_count,1)

if __name__=="__main__":unittest.main()
