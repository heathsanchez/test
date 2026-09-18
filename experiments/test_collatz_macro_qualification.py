import copy
import unittest
import collatz_macro_authority as a

class QualificationTests(unittest.TestCase):
    def test_exact_path_and_corruption(self):
        cap=a.capability([[2,3,1]])  # 3 -> 5 -> 8 -> 4 -> 2 -> 1
        self.assertEqual(a.replay(cap,1)['minimum'],1)
        bad=copy.deepcopy(cap); bad['A']+=1
        with self.assertRaises(ValueError): a.verify_capability(bad)
    def test_canonical_restart_and_digest_attack(self):
        bank=a.seal([a.capability([[2,3,1]])])
        self.assertEqual(a.restore(a.canonical(bank)),bank)
        bad=copy.deepcopy(bank);bad['capabilities'][0]['steps']+=1
        with self.assertRaises(ValueError):a.restore(a.canonical(bad))
    def test_authority_mismatch(self):
        bank=a.seal([]);bank['contract']['verifier']='stale'
        bank['digest']=a.digest({k:v for k,v in bank.items() if k!='digest'})
        with self.assertRaises(ValueError):a.restore(a.canonical(bank))
    def test_task_certificate_rejects_wrong_endpoint(self):
        a.verify_descent(3,4,2)
        with self.assertRaises(ValueError):a.verify_descent(3,4,1)
    def test_wrong_episode_guard_rejects(self):
        cap=a.capability([[2,3,1]])
        self.assertFalse(a.replay(cap,3)['legal'])
    def test_revocation_survives_restart(self):
        cap=a.capability([[2,3,1]])
        bank=a.seal([cap],[cap['id']])
        self.assertEqual(a.active(a.restore(a.canonical(bank))),[])

if __name__=='__main__':unittest.main()
