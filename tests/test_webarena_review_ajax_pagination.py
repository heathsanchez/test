"""Read-only Magento AJAX pagination keeps real repeated review observations."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class Response:
    status=200

class Locator:
    def __init__(self,page):self.page=page
    async def count(self):
        return 1 if self.page.screens[self.page.url][1] else 0
    def nth(self,index):
        if index!=0:raise AssertionError(index)
        return self
    async def get_attribute(self,name):
        assert name=='href'
        return self.page.screens[self.page.url][1]

class Page:
    def __init__(self,screens):
        self.screens=screens
        self.url=next(iter(screens))
        self.visits=[]
    def locator(self,selector):
        assert selector=='.pages-item-next a'
        return Locator(self)
    async def goto(self,url,**kwargs):
        self.visits.append(url)
        if url not in self.screens:raise AssertionError(url)
        self.url=url
        return Response()

async def rows(page):
    return page.screens[page.url][0]

class Pagination(unittest.IsolatedAsyncioTestCase):
    async def test_ajax_page2_preserves_duplicate_real_review(self):
        from webarena_review_ajax_pagination import collect_all_reviews
        page=Page({
            'http://localhost:7770/product.html':(
                [{'title':'Review A','stars':5},{'title':'Review B','stars':1}],
                '/review/product/listAjax/id/1/?p=2'),
            'http://localhost:7770/review/product/listAjax/id/1/?p=2':(
                [{'title':'Review B','stars':1}],None),
        })
        observed,visited=await collect_all_reviews(page,'http://localhost:7770',rows)
        self.assertEqual([x['title'] for x in observed],['Review A','Review B','Review B'])
        self.assertEqual(len(page.visits),1)
        self.assertEqual(len(visited),2)

    async def test_untrusted_offsite_pager_fails_closed(self):
        from webarena_review_ajax_pagination import collect_all_reviews
        page=Page({'http://localhost:7770/product.html':(
            [{'title':'A','stars':1}], 'https://external.invalid/review/product/listAjax/id/1/?p=2')})
        with self.assertRaises(RuntimeError):
            await collect_all_reviews(page,'http://localhost:7770',rows)

    async def test_pager_cycle_fails_closed(self):
        from webarena_review_ajax_pagination import collect_all_reviews
        a='http://localhost:7770/product.html'
        b='http://localhost:7770/review/product/listAjax/id/1/?p=2'
        page=Page({a:([{'title':'A','stars':2}], b),
                   b:([{'title':'B','stars':1}], b)})
        with self.assertRaises(RuntimeError):
            await collect_all_reviews(page,'http://localhost:7770',rows)

if __name__=='__main__':unittest.main()
