"""Regression controls for intent-derived, task-ID-free forum discovery."""
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from webarena_reddit_forum_resolver import candidate_forum_slugs, compact, resolve_forum


class Response:
    def __init__(self, status):
        self.status = status


class EmptyLinks:
    async def count(self):
        return 0


class FakePage:
    def __init__(self, valid):
        self.valid = valid
        self.url = ""
        self.visited = []

    def locator(self, selector):
        return EmptyLinks()

    async def goto(self, url, **kwargs):
        self.url = url
        self.visited.append(url)
        return Response(200 if url in self.valid else 404)


class ForumDiscoveryTests(unittest.IsolatedAsyncioTestCase):
    def test_written_digit_variant_is_generated(self):
        variants = candidate_forum_slugs("explain like im 5")
        self.assertIn("explainlikeimfive", variants)
        self.assertNotIn("eli5", variants)
        self.assertEqual(compact("explainlikeimfive"), compact(variants[-1]))

    def test_compound_forum_names_retain_semantic_words(self):
        from webarena_reddit_forum_resolver import score,toks
        self.assertEqual(toks("BuyItForLife"),["buy","it","for","life"])
        intent="Must have product at last for ever recommendations"
        self.assertGreater(
            score(intent,"/f/BuyItForLife BuyItForLife","BuyItForLife"),
            score(intent,"/f/Art Art","Art"),
        )
        self.assertGreater(
            score("DIY toolkit recommendations","/f/DIY DIY","DIY"),
            score("DIY toolkit recommendations","/f/Art Art","Art"),
        )

    def test_other_forums_not_rewritten_as_aliases(self):
        self.assertIn("deeplearning", candidate_forum_slugs("deep learning"))
        self.assertIn("books", candidate_forum_slugs("books"))

    async def test_evidence_bound_direct_discovery(self):
        page = FakePage({"http://localhost:9999/f/explainlikeimfive"})
        result = await resolve_forum(page, "http://localhost:9999", "explain like im 5")
        self.assertEqual(result["slug"], "explainlikeimfive")
        self.assertIn("http://localhost:9999/f/explainlikeimfive", page.visited)
        self.assertFalse(any("/forums/by_name/" in url for url in page.visited))

    async def test_unrelated_successful_page_not_accepted(self):
        page = FakePage({"http://localhost:9999/f/unrelated"})
        # Unlike a legitimate canonical forum match, this is not a source-derived path.
        # No candidate resolves and no index links exist: fail closed.
        with self.assertRaises(RuntimeError):
            await resolve_forum(page, "http://localhost:9999", "explain like im 5", max_pages=1)


if __name__ == "__main__":
    unittest.main()
