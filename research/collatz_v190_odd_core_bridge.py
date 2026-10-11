"""V190: exact odd-core/zero-defect checks; CONDITIONAL lemma, no Collatz QED."""
from fractions import Fraction as F


def odd_step(a):
    z, k = 3*a+1, 0
    while z % 2 == 0:
        z //= 2
        k += 1
    return z, k


def shortcut(n):
    return n//2 if n % 2 == 0 else (3*n+1)//2


def D(a, k):
    x = a
    for _ in range(k):
        x = shortcut(x)
    return 3**k*(a+1)-2**k*(x+1)


def audit():
    for a in range(1, 10001, 2):
        y, k = odd_step(a)
        assert y % 2 == 1 and y % 3 == (2 if k % 2 else 1)
        assert 2**k*y == 3*a+1
        assert (D(a,k)==0) == (k==1)
    # Do not drop target endpoints above the original-source cutoff.
    direct = {a:odd_step(a) for a in range(1, 1000, 2)}
    inverse = {}
    for y in range(1, 1501, 2):
        if y % 3 == 0:
            continue
        k = 1 if y % 3 == 2 else 2
        while True:
            a = (2**k*y-1)//3
            if a >= 1000:
                break
            assert (2**k*y-1)%3 == 0 and a % 2 == 1
            assert a not in inverse
            inverse[a] = (y,k)
            k += 2
    assert direct == inverse
    assert sum(y>=1000 for y,k in direct.values()) == 84
    assert sum((F(1,a*a) for a in direct),F(0)) == \
        sum((F(9,(2**k*y-1)**2) for y,k in inverse.values()),F(0))
    for c in (5,7):
        a=3
        assert 3*(a+1)-2*((3*a+c)//2+1) == 1-c  # TRUE +1 ONLY

    # All-K universal Mersenne delay has a simple exact proof:
    # T^K(2^K-1)=3^K-1 and T(x)>=x/2 at EVERY subsequent clock.
    # Thus 2^L*(2^K-1)<3^K-1 forbids descent by clock K+L.
    # The first even step is not an automatic recovery event.
    for K in range(3, 102, 2):
        n, x = 2**K-1, 2**K-1
        for i in range(K):
            assert x % 2 == 1
            x=shortcut(x)
        assert x == 3**K-1 and x % 4 == 2
        assert shortcut(x)>n  # first positive-defect event still too high
        for L in range(32):
            assert (2**L)*x >= 3**K-1
            if (2**L)*n < 3**K-1:
                assert x > n
            x=shortcut(x)

    # From V168 saturated-class residue skew, m>=15 and s=2:
    m=15
    R_min=F(1,3)*F(2*m-1,2*m)**2
    W2_min=(5*R_min-1)/3
    assert W2_min==F(301,1620)
    # Positive-defect k>=2 weight transfer is bounded by geometric tails.
    A1=F(3,5)*F(4*m,4*m-1)**2  # endpoints y=1 (mod 3)
    A2=F(3,20)*F(8*m,8*m-1)**2  # endpoints y=2 (mod 3), k>=3
    assert A1==F(2160,3481) and A2==F(2160,14161)
    Z_min=1-A1*(1-W2_min)-A2*W2_min
    assert Z_min==F(3284703,7042063) and Z_min>F(46,100)

    # These aggregate weights satisfy all stated coarse inequalities for
    # arbitrarily high minimum source. They are NOT an actual bad class.
    for m in (15,16,100,1000,10**6):
        w0=F(1,10)
        w1=F(29,45)+F(5,36*m)
        w2=F(23,90)-F(5,36*m)
        lead=F(3,5)*w1+F(12,5)*w2
        r=(w1+4*w2)/5
        assert w0+w1+w2==1 and lead==1-F(1,4*m)
        assert F(1,3)*F(2*m-1,2*m)**2 < r < F(1,3)
        assert 1 <= F(2*m,2*m-1)**2 * lead

    print('PASS: 5000 odd source/clock checks; 500 exact rational guarded transfers; 84 high endpoints')
    print('CONDITIONAL minimum zero-defect odd-core s=2 mass: '
          f'{Z_min} = {float(Z_min)*100:.6f}%')
    print('GLOBAL COLLATZ: UNKNOWN; NOT LEAN-FORMAL')


if __name__=='__main__':
    audit()
