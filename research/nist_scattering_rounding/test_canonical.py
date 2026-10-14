import hashlib,unittest
from canonical_probe import extract,norm

SCIENCE="For the first approach 0.854 stat sys and for the second approach 0.851 stat sys"
def html_page(description,wrapper="x"):
    return ('<html><head><meta name="description" content="'+description+
       '"></head><body><div>Dynamic nav '+wrapper+'</div></body></html>').encode()

class SourceContentConsequence(unittest.TestCase):
    def test_science_content_stable_under_transport_noise(self):
        a=extract(html_page(SCIENCE,"random javascript shell 100"))
        b=extract(html_page(SCIENCE,"different provider widget 200"))
        self.assertEqual(a["strategy"],"PUBLISHER_DESCRIPTION_META")
        self.assertEqual(b["strategy"],"PUBLISHER_DESCRIPTION_META")
        self.assertEqual(hashlib.sha256(a["abstract"].encode()).hexdigest(),
                         hashlib.sha256(b["abstract"].encode()).hexdigest())
        self.assertNotEqual(hashlib.sha256(html_page(SCIENCE,"100")).hexdigest(),
                            hashlib.sha256(html_page(SCIENCE,"200")).hexdigest())
    def test_scientific_content_mutation_changes_pin(self):
        a=extract(html_page(SCIENCE,"same"))
        b=extract(html_page(SCIENCE.replace("0.851","0.850"),"same"))
        self.assertTrue("abstract" in a)
        self.assertNotEqual(b["strategy"],"PUBLISHER_DESCRIPTION_META")
    def test_missing_uncertainty_labels_cannot_be_pinned(self):
        s=SCIENCE.replace("stat sys","noise")
        r=extract(html_page(s))
        self.assertNotEqual(r["strategy"],"PUBLISHER_DESCRIPTION_META")
    def test_canonical_utf_and_whitespace_stability(self):
        self.assertEqual(norm("  proton\u00a0radius  0.851  "), "proton radius 0.851")

if __name__=="__main__":unittest.main()
