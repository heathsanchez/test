from falsifier import machine, fixed, evaluate

def test_fixed():
    n, obs, tr = machine('contains101')
    assert fixed(obs,tr) == (0,1,2,3)
    assert evaluate('contains101',('both','same','states'))['pass']

if __name__ == '__main__':
    test_fixed()
