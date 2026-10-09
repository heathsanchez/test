"""Controls on intent-only Magento catalog search sorting, not score claims."""
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
MODULE = ROOT / 'scripts' / 'webarena_shopping_sort_blind.py'

class MagentoSearchSortContract(unittest.TestCase):
    def test_agent_exists(self):
        self.assertTrue(MODULE.is_file(), 'missing intent-only search sorting agent')

    def test_three_natural_language_sort_forms(self):
        from webarena_shopping_sort_blind import parse_intent
        cases = {
            'Pull up the page with all "mouth night guard" listings sorted by descending price.': ('mouth night guard','price','desc'),
            'Pull up the page with all "iphone 12 phone case" listings sorted by name alphabetically.': ('iphone 12 phone case','name','asc'),
            'Pull up the page with all "iphone 12 phone case" listings sorted by price.': ('iphone 12 phone case','price','asc'),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                spec = parse_intent(text)
                self.assertEqual((spec['query'],spec['field'],spec['direction']), expected)

    def test_url_preserves_query_and_sort_order(self):
        from webarena_shopping_sort_blind import build_url
        url = build_url({'query':'iphone 12 phone case', 'field':'name', 'direction':'asc'})
        parsed = urlparse(url)
        self.assertEqual(parsed.path, '/catalogsearch/result/index')
        self.assertEqual(parsed.netloc, 'localhost:7770')
        self.assertEqual(parse_qs(parsed.query), {
            'q':['iphone 12 phone case'],
            'product_list_order':['name'],
            'product_list_dir':['asc'],
        })

    def test_unsafe_or_unsupported_intents_fail_closed(self):
        from webarena_shopping_sort_blind import parse_intent, validate_start
        for intent in ('Buy my phone', 'Pull up all products and delete them.',
                       'Pull up the page with all "x" listings sorted by magic.',
                       'Pull up the page with all "" listings sorted by price.'):
            with self.subTest(intent=intent), self.assertRaises(ValueError):
                parse_intent(intent)
        with self.assertRaises(ValueError):validate_start('__GITLAB__')
        with self.assertRaises(ValueError):validate_start('https://example.org')

    def test_benchmark_metadata_is_not_in_agent_source(self):
        source = MODULE.read_text()
        for forbidden in ('task_id','intent_template_id','instantiation_dict',
                          'evaluate_task','expected_answer'):
            self.assertNotIn(forbidden, source)

class MagentoSortNavigation(unittest.IsolatedAsyncioTestCase):
    async def test_descending_price_default_is_verified_by_actual_ui(self):
        from webarena_shopping_sort_blind import navigate
        class Reply:
            status=200
        class Marker:
            async def count(self):return 1
        class FakePage:
            def __init__(self):self.url='';self.visits=[]
            async def goto(self,url,**kwargs):
                self.url=url;self.visits.append(url);return Reply()
            async def title(self):return 'Search results'
            def locator(self,selector):
                self.seen_selector=selector
                return Marker()
        page=FakePage()
        result=await navigate(page, {'query':'mouth night guard','field':'price','direction':'desc'})
        self.assertEqual(len(page.visits),1,
                         'last-navigation-only evaluation requires canonical final URL')
        self.assertEqual(parse_qs(urlparse(page.visits[0]).query),
                         {'q':['mouth night guard'],'product_list_order':['price']})
        self.assertIn('sort-desc',page.seen_selector)
        self.assertEqual(result['observed_url'],page.visits[0])

    async def test_missing_descending_ui_state_fails_closed(self):
        from webarena_shopping_sort_blind import navigate
        class Reply:status=200
        class Marker:
            async def count(self):return 0
        class FakePage:
            url=''
            async def goto(self,url,**kwargs):self.url=url;return Reply()
            async def title(self):return 'Search results'
            def locator(self,selector):return Marker()
        with self.assertRaises(RuntimeError):
            await navigate(FakePage(),{'query':'mouth night guard','field':'price','direction':'desc'})

    async def test_read_only_navigation_uses_compiled_search_url(self):
        from webarena_shopping_sort_blind import navigate
        class Response:
            status=200
        class FakePage:
            url=''
            async def goto(self, url, **kwargs):
                self.url=url
                return Response()
            async def title(self):return 'Search results for: iphone 12 phone case'
        page=FakePage()
        observed=await navigate(page, {'query':'iphone 12 phone case', 'field':'price','direction':'asc'})
        self.assertEqual(observed['observed_url'],page.url)
        self.assertEqual(observed['sort_field'],'price')
        self.assertEqual(observed['sort_direction'],'asc')

if __name__=='__main__':unittest.main()
