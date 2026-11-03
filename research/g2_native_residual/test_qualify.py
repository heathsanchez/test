import unittest
import tempfile
from qualify import decode_go_events, identity, safe_test_path, transplant_author_test
from pathlib import Path


def json_event(action, test=None):
    import json
    obj={"Time":"T", "Action":action, "Package":"p"}
    if test is not None:obj["Test"]=test
    return json.dumps(obj)


class NativeQualifiedBoundaryTests(unittest.TestCase):
    def test_zero_tests_exit_zero_is_unknown(self):
        self.assertEqual(decode_go_events(json_event("pass"),0)["status"],"UNKNOWN_ZERO_RECOGNIZED_TESTS")

    def test_named_fail_and_nonzero_is_assertion(self):
        s="\n".join([json_event("run","TestRegression"),json_event("fail","TestRegression"),json_event("fail")])
        x=decode_go_events(s,1)
        self.assertEqual(x["status"],"FAIL_NATIVE_ASSERTIONS")
        self.assertEqual(x["failed_count"],1)

    def test_named_pass_and_zero(self):
        s="\n".join([json_event("run","TestRegression"),json_event("pass","TestRegression"),json_event("pass")])
        self.assertEqual(decode_go_events(s,0)["status"],"PASS_NONEMPTY")

    def test_compiler_failure_does_not_imply_assertion(self):
        self.assertEqual(decode_go_events("# build failed",1)["status"],"UNKNOWN_MALFORMED_TEST_STREAM")

    def test_named_pass_with_wrong_exit_is_not_green(self):
        s="\n".join([json_event("run","TestRegression"),json_event("pass","TestRegression")])
        self.assertNotEqual(decode_go_events(s,1)["status"],"PASS_NONEMPTY")

    def test_first_party_new_test_file_is_admitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            original=root/"source"/"runtime.go"
            original.parent.mkdir()
            original.write_bytes(b"package example")
            candidate=root/"source"/"new"/"native_test.go"
            self.assertFalse(candidate.exists())
            transplant_author_test(candidate,b"package example\\n")
            self.assertEqual(candidate.read_bytes(),b"package example\\n")
            self.assertEqual(original.read_bytes(),b"package example")

    def test_existing_test_is_replaced_not_implementation(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"repo_test.go"
            target.write_bytes(b"old")
            transplant_author_test(target,b"new")
            self.assertEqual(target.read_bytes(),b"new")

    def test_untrusted_paths_and_symlinks_refused(self):
        self.assertTrue(safe_test_path("subdir/proof_test.go"))
        for unsafe in ("../escape_test.go", "sub/../../escape_test.go", "./x_test.go", "foo.go", "/tmp/x_test.go"):
            self.assertFalse(safe_test_path(unsafe))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            destination=root/"outside"
            destination.write_bytes(b"protected")
            link=root/"proof_test.go"
            link.symlink_to(destination)
            with self.assertRaisesRegex(ValueError,"unsafe_test_target"):
                transplant_author_test(link,b"replacement")
            self.assertEqual(destination.read_bytes(),b"protected")

    def test_forged_bad_sha_refused(self):
        self.assertFalse(identity(Path("."),"0"*39+"z"))

if __name__=="__main__": unittest.main()
