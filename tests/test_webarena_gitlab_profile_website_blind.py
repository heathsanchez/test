import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_gitlab_profile_website_blind import (
    parse_profile_website_intent,website_key,
)


class ProfileWebsiteIntentTests(unittest.TestCase):
    def test_generic_profile_website_mutation(self):
        samples={
            "set the homepage URL on my GitLab profile to helloworld.xyz":"helloworld.xyz",
            "set the homepage URL on my GitLab profile to www.byteblaze.com":"www.byteblaze.com",
            "Set the homepage URL on my GitLab profile to https://example.org/abc":"https://example.org/abc",
        }
        for intent,wanted in samples.items():
            self.assertEqual(parse_profile_website_intent(intent),wanted)

    def test_scheme_relative_website_identity(self):
        self.assertEqual(website_key("http://helloworld.xyz/"),website_key("helloworld.xyz"))
        self.assertEqual(website_key("https://www.byteblaze.com"),website_key("www.byteblaze.com"))
        self.assertNotEqual(website_key("elsewhere.invalid"),website_key("www.byteblaze.com"))

    def test_invalid_intent_fails_closed(self):
        for intent in (
            "Delete my GitLab account",
            "set the homepage URL on my GitLab profile to javascript:alert(1)",
            "set the homepage URL on my GitLab profile to localhost 123",
            "set my profile website to evil.com",
        ):
            with self.assertRaises(ValueError):
                parse_profile_website_intent(intent)

    def test_no_task_metadata(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_gitlab_profile_website_blind.py").read_text()
        for token in ("task_id","intent_template_id","instantiation_dict","expected_answer","evaluate_task"):
            self.assertNotIn(token,src)


if __name__=="__main__":
    unittest.main()
