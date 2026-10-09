"""Task-ID-free image repost admission from current Reddit forum context."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from webarena_reddit_repost_blind import parse_intent


class RepostRequest(unittest.TestCase):
    def test_three_image_requests_derive_source_and_target(self):
        cases = {
            'Bald Eagle': ('connecticut', 'from /f/pics'),
            'Firework': ('news', 'from /f/pics'),
            "Wife's costume": ('funny', 'from /f/pics'),
        }
        for content, (forum, title) in cases.items():
            instruction = (
                f'Re-post the image of {content} from this forum to {forum} '
                f'forum using the image URL and title "{title}"'
            )
            result = parse_intent(instruction, '__REDDIT__/f/pics')
            self.assertEqual(result, {
                'source_forum': 'pics',
                'image_phrase': content,
                'destination_forum': forum,
                'post_title': title,
            })

    def test_wrong_source_or_unsafe_forum_rejected(self):
        with self.assertRaises(ValueError):
            parse_intent(
                'Re-post the image of Firework from this forum to news '
                'forum using the image URL and title "from /f/pics"',
                '__GITLAB__',
            )
        with self.assertRaises(ValueError):
            parse_intent(
                'Re-post the image of Firework from this forum to ../secrets '
                'forum using the image URL and title "from /f/pics"',
                '__REDDIT__/f/pics',
            )

    def test_no_benchmark_dispatch(self):
        source = (ROOT / 'scripts' / 'webarena_reddit_repost_blind.py').read_text()
        for forbidden in (
            'task_id', 'intent_template_id', 'instantiation_dict',
            'expected_answer', 'evaluate_task',
        ):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
