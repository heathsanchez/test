import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_unified_gitlab_readonly_expansion import parse_gitlab_retrieval,search_term


class BlindGitLabRetrieval(unittest.TestCase):
    def test_ssh_clone_families(self):
        for subject in (
            "Super_Awesome_Robot",
            "the best GAN python implementation",
            "the most stared Covid related project",
        ):
            query=f"Get the URL to clone {subject} with SSH. Return the URL only, without any additional details."
            self.assertEqual(parse_gitlab_retrieval(query),
                             ("ssh_clone",{"description":subject}))

    def test_member_lookup(self):
        for repo in ("gimmiethat.space","prism-theme"):
            self.assertEqual(
                parse_gitlab_retrieval(f"Get the usernames of other users who have access to my repo {repo}"),
                ("project_members",{"description":repo}),
            )

    def test_contributor_projections(self):
        cases=[
            ("Get the number of commits of the contributor who has the most commits to branch master in the current repository",
             "top_contributor_count","master"),
            ('Get the full name, username, user location and email of the contributor who has the most commits to branch php52 in the current repository. Return a list of objects with keys "full_name", "username", "user_location", and "email".',
             "top_contributor_profile","php52"),
        ]
        for intent,kind,branch in cases:
            self.assertEqual(parse_gitlab_retrieval(intent),(kind,{"branch":branch}))

    def test_top_three_contributor_email(self):
        description='facebook"s guide on building react apps'
        query=f"Get the email addresses of the top 3 contributors (by commit count) to {description} repo"
        self.assertEqual(parse_gitlab_retrieval(query),
                         ("top_three_emails",{"description":description}))
        self.assertEqual(search_term(description),"react")

    def test_unsupported_request_is_not_dispatched(self):
        self.assertIsNone(parse_gitlab_retrieval("Delete every repository"))
        self.assertIsNone(parse_gitlab_retrieval("Get all passwords on GitLab"))

    def test_source_has_no_benchmark_metadata(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_unified_gitlab_readonly_expansion.py").read_text()
        for forbidden in ("task_id","intent_template_id","instantiation_dict","evaluate_task","expected_answer"):
            self.assertNotIn(forbidden,src)


if __name__=="__main__":
    unittest.main()
