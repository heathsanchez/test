"""Cross-site workflows must provision every site their agent can observe."""
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/webarena_blind_retrieval_matrix.yml"


class CrosssiteServiceClosure(unittest.TestCase):
    def test_crosssite_starts_shopping_reddit_and_gitlab(self):
        source = WORKFLOW.read_text()
        services = {
            "shopping": 'if [ "$LANE" = shopping ] || [ "$LANE" = crosssite ]; then',
            "reddit": 'if [ "$LANE" = reddit ] || [ "$LANE" = crosssite ]; then',
            "gitlab": 'if [ "$LANE" = gitlab ] || [ "$LANE" = crosssite ]; then',
        }
        for name, condition in services.items():
            with self.subTest(site=name):
                self.assertIn(condition, source)

    def test_unique_service_bindings(self):
        source = WORKFLOW.read_text()
        for port in ("7770:80", "9999:80", "8023:8023"):
            with self.subTest(port=port):
                self.assertEqual(source.count(port), 1)


if __name__ == "__main__":
    unittest.main()
