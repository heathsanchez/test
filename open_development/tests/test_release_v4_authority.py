import copy,unittest
from open_development.runtime import digest
from open_development.release_v4_authority import build
class AuthorityTests(unittest.TestCase):
 def test_regression_binding_fails_closed(self):
  # The full scientific round trip is exercised by test_release_v4; this checks
  # that the final wrapper rejects an unbound current-head regression first.
  import open_development.release_v4_authority as a
  old=a.validate_science;a.validate_science=lambda *x:None
  try:
   science={"source_commit":a.SCIENCE_COMMIT,"run_id":a.SCIENCE_RUN,"claim":"x","canonical_parent":"p","v3":{},"limitations":[]}
   regression={"source_commit":"b"*40,"run_id":1,"core_result":"RELEASE_EVIDENCE_PASS","core_evidence_digest":"c"*64,"semantics_result":"TYPED_PROGRAM_SEMANTICS_LEAN_PASS","axioms_pass_count":11,"artifact_digests":["sha256:"+"d"*64]}
   build("heathsanchez/test","b"*40,2,science,{}, {}, {}, {},regression)
   bad=copy.deepcopy(regression);bad["source_commit"]="e"*40
   with self.assertRaisesRegex(ValueError,"current-head"):build("heathsanchez/test","b"*40,2,science,{}, {}, {}, {},bad)
  finally:a.validate_science=old
