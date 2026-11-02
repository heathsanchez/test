import json
import unittest
from qualify import original_suite_receipt

def event(action, name='TestOne', pkg='fixture'):
    return json.dumps({'Action':action, 'Test':name, 'Package':pkg})

class QualificationParser(unittest.TestCase):
    def test_recognized_valid_suite(self):
        r=original_suite_receipt(event('pass')+'\n'+event('pass'),0)
        self.assertEqual(r['status'],'ORIGINAL_SUITE_PASS_NONEMPTY')
        self.assertEqual(r['recognized_passes'],1)
    def test_nonempty_exit_zero_does_not_replace_test_count(self):
        self.assertEqual(original_suite_receipt(json.dumps({'Action':'pass','Package':'fixture'}),0)['status'],'UNKNOWN_ZERO_RECOGNIZED_TESTS')
    def test_forged_or_malformed_json_abstains(self):
        self.assertEqual(original_suite_receipt('unparsed JSON',0)['status'],'UNKNOWN_TEST_EVENT_STREAM')
    def test_failed_tests_fail_closed(self):
        s=event('pass')+'\n'+event('fail','TestTwo')
        self.assertEqual(original_suite_receipt(s,0)['status'],'UNKNOWN_ORIGINAL_TEST_FAILURE')
        self.assertEqual(original_suite_receipt(event('pass'),1)['status'],'UNKNOWN_ORIGINAL_TEST_FAILURE')

if __name__=='__main__':unittest.main()
