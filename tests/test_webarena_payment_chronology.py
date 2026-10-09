"""The last N orders need complete pagination and chronological ordering."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_shopping_admin_payment_fold_v2 import collect_rows,compute

HEADERS=["ID","Purchase Date","Grand Total (Purchased)","Status"]

class Cell:
    def __init__(self,value):self.value=value
    async def inner_text(self):return self.value

class Cells:
    def __init__(self,row):self.row=row
    async def count(self):return len(self.row)
    def nth(self,index):return Cell(self.row[index])

class Row:
    def __init__(self,row):self.row=row
    async def count(self):return 1
    def locator(self,css):
        if css!="td":raise AssertionError(css)
        return Cells(self.row)

class Rows:
    def __init__(self,rows):self.rows=rows
    async def count(self):return len(self.rows)
    def nth(self,index):return Row(self.rows[index])
    @property
    def first(self):return self.nth(0)

class Table:
    def __init__(self,rows):self.rows=rows
    def locator(self,css):
        if css!="tbody tr":raise AssertionError(css)
        return Rows(self.rows)

class Next:
    def __init__(self,page):self.page=page
    async def count(self):return 1
    async def is_enabled(self):return self.page.index<len(self.page.pages)-1
    async def click(self,force=False):self.page.index+=1

class Pager:
    def __init__(self,page):self.page=page
    async def count(self):return 1
    def nth(self,index):
        if index!=0:raise AssertionError(index)
        return self
    def locator(self,css):
        if css!="button.action-next":raise AssertionError(css)
        return Next(self.page)

class Page:
    def __init__(self,pages):self.pages=pages;self.index=0
    def locator(self,css):
        if css!=".admin__data-grid-pager-wrap:visible":raise AssertionError(css)
        return Pager(self)
    async def wait_for_timeout(self,milliseconds):pass

class PaymentChronology(unittest.IsolatedAsyncioTestCase):
    def test_select_recent_orders_by_date_not_grid_encounter_order(self):
        def entry(ident,date,price):
            return {"id":ident,"purchase_date":date,"payment":Decimal(price),"status_class":"completed"}
        rows=[
            entry("old-a","Jun 11, 2022 8:29:39 PM","163.00"),
            entry("old-b","Jun 7, 2022 5:19:20 PM","65.00"),
            entry("new-a","May 19, 2023 8:11:51 AM","93.40"),
            entry("new-b","May 14, 2023 1:22:46 AM","89.00"),
        ]
        amount,evidence=compute({"mode":"sum","n":2,"predicate":"completed"},rows)
        self.assertEqual(amount,Decimal("182.40"))
        self.assertEqual([x["id"] for x in evidence["selected"]],["new-a","new-b"])

    async def test_scan_next_page_even_after_first_page_matches(self):
        pages=[
            [["old-a","Jun 11, 2022 8:29:39 PM","$163.00","Complete"],
             ["old-b","Jun 7, 2022 5:19:20 PM","$65.00","Complete"]],
            [["new-a","May 19, 2023 8:11:51 AM","$93.40","Complete"],
             ["new-b","May 14, 2023 1:22:46 AM","$89.00","Complete"]],
        ]
        page=Page(pages)
        async def table_headers(target):
            return Table(target.pages[target.index]),HEADERS
        with patch("webarena_shopping_admin_payment_fold_v2.table_headers",new=table_headers):
            rows=await collect_rows(page,{"completed":2},max_pages=3)
        self.assertEqual(len(rows),4)
        self.assertEqual(page.index,1)
        self.assertEqual({r["id"] for r in rows},{"old-a","old-b","new-a","new-b"})

if __name__=="__main__":unittest.main()
