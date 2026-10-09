"""GitLab blind fork intent, ambiguous identities and observed POST boundaries."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_gitlab_fork_blind import (
    parse_fork_intent,select_exact_project,select_user,
    choose_user_namespace,fork_payload,
)

class ForkIntentContract(unittest.TestCase):
    def test_single_project_intent(self):
        self.assertEqual(parse_fork_intent("Fork MetaSeq."),("single","MetaSeq"))
        self.assertEqual(parse_fork_intent("Fork twitter-bootstrap."),("single","twitter-bootstrap"))

    def test_user_project_collection_intent(self):
        self.assertEqual(parse_fork_intent("Fork all repos from Akilesh Kannan."),
                         ("owner","Akilesh Kannan"))
        self.assertEqual(parse_fork_intent("Fork all repos from facebook."),
                         ("owner","facebook"))

    def test_unknown_or_unsafe_requests_fail_closed(self):
        for text in ("Delete repositories","Fork ../private.","Fork all repos from ..",
                     "Fork everything in company","Fork."):
            with self.subTest(text=text),self.assertRaises(ValueError):
                parse_fork_intent(text)

    def test_resolve_observed_exact_project_not_similar_name(self):
        items=[{"id":3,"name":"MetaSeqOps","path":"metaseqops","path_with_namespace":"x/metaseqops"},
               {"id":2,"name":"MetaSeq","path":"metaseq","path_with_namespace":"x/metaseq"}]
        self.assertEqual(select_exact_project("MetaSeq",items)["id"],2)

    def test_ambiguous_projects_fail_closed(self):
        items=[{"id":3,"name":"MetaSeq","path":"metaseq","path_with_namespace":"x/metaseq"},
               {"id":2,"name":"MetaSeq","path":"metaseq","path_with_namespace":"y/metaseq"}]
        with self.assertRaises(ValueError):select_exact_project("MetaSeq",items)

    def test_author_name_exact_and_ambiguous(self):
        users=[{"id":5,"name":"Akilesh Kannan","username":"akilesh"},
               {"id":7,"name":"Akilesh Kannan Jr","username":"another"}]
        self.assertEqual(select_user("Akilesh Kannan",users)["id"],5)
        with self.assertRaises(ValueError):select_user("nonexistent",users)

    def test_namespace_observed_not_hardcoded(self):
        user={"id":9,"username":"byteblaze"}
        namespaces=[{"id":51,"path":"other","kind":"user","owner_id":8},
                    {"id":777,"path":"byteblaze","kind":"user","owner_id":9}]
        self.assertEqual(choose_user_namespace(user,namespaces),777)

    def test_post_body_uses_actual_project_and_namespace(self):
        project={"id":31,"name":"CacheEval","path":"CacheEval"}
        self.assertEqual(fork_payload(project,777),
                         {"id":31,"name":"CacheEval","namespace_id":777,"path":"CacheEval"})

    def test_agent_source_has_no_benchmark_answers(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_gitlab_fork_blind.py").read_text()
        for token in ("task_id","intent_template_id","instantiation_dict","expected_answer","evaluate_task"):
            self.assertNotIn(token,src)

if __name__=="__main__":unittest.main()
