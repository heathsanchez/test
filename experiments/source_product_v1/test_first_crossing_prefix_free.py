"""Coverage audit: first-coefficient-crossing terminals are prefix-free."""
import unittest


def terminal_words(max_depth=24):
    frontier=[('',0)]
    terminal=[]
    for k in range(max_depth):
        nxt=[]
        for w,q in frontier:
            for b in (0,1):
                q2=q+b
                w2=w+str(b)
                d=k+1
                if 3**q2 < 2**d:
                    terminal.append(w2)
                else:
                    nxt.append((w2,q2))
        frontier=nxt
    return terminal


class FirstCrossingCoverageTests(unittest.TestCase):
    def test_terminal_language_prefix_free(self):
        words=terminal_words(24)
        term=set(words)
        self.assertTrue(words)
        for w in words:
            for i in range(1,len(w)):
                self.assertNotIn(w[:i],term)

    def test_no_terminal_has_a_later_first_crossing_extension(self):
        for w in terminal_words(24):
            for b in '01':
                z=w+b
                q=0
                first=None
                for i,ch in enumerate(z,1):
                    q += ch=='1'
                    if 3**q < 2**i:
                        first=i
                        break
                self.assertEqual(first,len(w))


if __name__ == '__main__':
    unittest.main(verbosity=2)
