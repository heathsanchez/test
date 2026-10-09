import json
def step(n):
    return n//2 if n%2==0 else (3*n+1)//2
def inspect(k):
    M=2**k
    words=set()
    counts={"guarded":0,"unknown":0}
    for r in range(M):
        x=r; odd=0; word=[]
        for _ in range(k):
            b=x%2; odd+=b; word.append(b); x=step(x)
        w=tuple(word)
        assert w not in words
        words.add(w)
        A=3**odd
        for q in [0,1,2,7]:
            y=r+M*q
            for b in w:
                assert y%2==b
                y=step(y)
            assert y==x+A*q
        if A<M:
            q0=max(0,(x-r)//(M-A)+1)
            assert x+A*q0<r+M*q0
            counts["guarded"]+=1
        else:
            counts["unknown"]+=1
    assert len(words)==M
    return {"depth":k,**counts}
if __name__=="__main__":
    print(json.dumps({"status":"BOUNDED_EXACT_ONLY","qed":False,"rows":[inspect(k) for k in range(1,13)]},indent=2))
