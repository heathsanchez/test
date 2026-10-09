import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_reddit_blind_retrieval_expansion import parse_intent


class RedditBlindRetrieval(unittest.TestCase):
    def test_book_title_projection(self):
        text='Among the top 10 hottest posts in the "Books" forum, get the post titles from those that recommend exactly one book.'
        self.assertEqual(parse_intent(text),
                         ("top_singular_books",{"forum":"Books","number":10,"projection":"post_title"}))

    def test_book_and_author_projection(self):
        samples={
            'Among the top 10 hottest posts in the "Books" forum, get the book titles, exactly as they appear in the post description, from those that recommend exactly one book.':"book_title",
            'Among the top 10 hottest posts in the "Books" forum, get the author names and book titles, exactly as they appear in the post description, from those that recommend exactly one book. Return a list of objects with keys "book" and "author".':"book_author",
        }
        for text,projection in samples.items():
            self.assertEqual(parse_intent(text),
                             ("top_singular_books",{"forum":"Books","number":10,"projection":projection}))

    def test_recent_negative_comment_family(self):
        for forum in ("Worcester","DIY","photoshopbattles"):
            intent=(f"In the {forum} forum, get the username and post title of the most recent post, "
                'and count the number of comments on that post that are not from the author and have more downvotes than upvotes. '
                'Return a list of objects with keys "username", "post_title", and "count".')
            self.assertEqual(parse_intent(intent),("recent_negative_comments",{"forum":forum}))

    def test_fail_closed(self):
        for text in (
            "Delete all Reddit comments",
            'Among the top 1000000 hottest posts in the "Books" forum, get the post titles from those that recommend exactly one book.',
            "Get the latest news",
        ):
            with self.assertRaises(ValueError):
                parse_intent(text)

    def test_no_evaluator_or_task_dispatch(self):
        source=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_reddit_blind_retrieval_expansion.py").read_text()
        for forbidden in ("task_id","intent_template_id","instantiation_dict","expected_answer","evaluate_task"):
            self.assertNotIn(forbidden,source)


if __name__=="__main__":
    unittest.main()
