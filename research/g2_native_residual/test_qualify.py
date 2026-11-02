import unittest
from qualify import decode_go_events, identity
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

    def test_forged_bad_sha_refused(self):
        self.assertFalse(identity(Path("."),"0"*39+"z"))

if __name__=="__main__": unittest.main()
