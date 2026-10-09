"""Reuse of two UI-observed WebArena capabilities from blind natural language."""
import sys
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from webarena_blind_retrieval_bridge import parse_request,execute

STATUS_REQUEST=(
    'Get the status of my latest order and when will it arrive. '
    'Return a list of objects with keys "status" and "arrival_date" '
    '(YYYY-MM-DD format or null if not available), without any additional details.'
)


class Admission(unittest.TestCase):
    def test_user_requested_status_projection(self):
        self.assertEqual(parse_request("shopping",STATUS_REQUEST),
                         ("shopping_order_summary",{"mode":"latest_status"}))
        self.assertIsNone(parse_request("gitlab",STATUS_REQUEST))
        self.assertIsNone(parse_request("shopping","Get everyone's credit card details"))

    def test_admin_customer_grid_navigation(self):
        self.assertEqual(parse_request("shopping_admin","View the details of all customers"),
                         ("admin_customer_directory",{}))
        self.assertIsNone(parse_request("shopping","View the details of all customers"))

    def test_source_never_dispatches_from_evaluator_metadata(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_blind_retrieval_bridge.py").read_text()
        for key in ("task_id","intent_template_id","instantiation_dict","expected_answer","hard.json"):
            self.assertNotIn(key,src)


class NativeReuse(unittest.IsolatedAsyncioTestCase):
    async def test_latest_status_uses_observed_latest_order(self):
        rows=[
            {"order_no":"200","date":datetime(2023,6,12),
             "total":Decimal("12.50"),"status":"Processing"},
            {"order_no":"100","date":datetime(2023,5,12),
             "total":Decimal("19.00"),"status":"Complete"},
        ]
        with patch("webarena_shopping_order_summary.orders",
                   new_callable=AsyncMock,return_value=rows) as scanner:
            result,evidence=await execute(None,None,"shopping","shopping_order_summary",
                {"mode":"latest_status"},"__SHOPPING__")
        self.assertEqual(result,{
            "task_type":"RETRIEVE","status":"SUCCESS",
            "retrieved_data":[{"status":"processing","arrival_date":None}],
            "error_details":None,
        })
        self.assertEqual(evidence["selected"]["order_no"],"200")
        scanner.assert_awaited_once()

    async def test_customer_directory_requires_observed_live_grid(self):
        class Page:
            url="http://localhost:7780/admin/customer/index/"
        page=Page()
        with patch("webarena_blind_retrieval_bridge.visit",
                   new_callable=AsyncMock) as visit, \
             patch("webarena_shopping_admin_customer_lookup.live_table",
                   new_callable=AsyncMock,
                   return_value=(object(),["Name","Email","Phone"])) as grid:
            result,evidence=await execute(page,None,"shopping_admin",
                "admin_customer_directory",{},"__SHOPPING_ADMIN__")
        visit.assert_awaited_once_with(page,"http://localhost:7780/admin/customer/index/")
        grid.assert_awaited_once_with(page)
        self.assertEqual(result["task_type"],"NAVIGATE")
        self.assertEqual(result["status"],"SUCCESS")
        self.assertEqual(evidence["customer_headers"],["Name","Email","Phone"])

if __name__=="__main__":
    unittest.main()
