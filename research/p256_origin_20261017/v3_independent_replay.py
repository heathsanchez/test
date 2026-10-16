"""Independent P-256 V3 scanner under pre-frozen finite grammar; no origin claim."""
import ctypes
import hashlib
import json
from pathlib import Path
P=int('FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF',16)
X=int('6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296',16)
Y=int('4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5',16)
B=int('5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B',16)
C=int('7EFBA1662985BE9403CB055C75D4F7E0CE8D84A9C5114ABCAF3177680104FA0D',16)
SEED=bytes.fromhex('C49D360886E704936A6678E1139D26B7819F7E90')
STAMP=871696354
MOD=(1<<107)-1
AM=pow(3,121,MOD)
assert (Y*Y-X*X*X+3*X-B)%P==0
assert hashlib.sha1(b'abc').hexdigest()=='a9993e364706816aba3e25717850c26c9cd0d89d'

def freelip(seed,bits,num):
    s=seed%MOD; bound=MOD-MOD%(1<<bits); v=[]; rejects=0
    for _ in range(num):
        while True:
            s=(s*AM)%MOD
            if s<bound:break
            rejects+=1
        v.append(s%(1<<bits))
    return v,rejects

def number(seq,bits,order):
    a=0
    for v in seq if order=='msf' else seq[::-1]: a=(a<<bits)|v
    return a%P

hist,_=freelip(20420,26,64)
histnum=0
for v in hist[29:40]:histnum=(histnum<<26)|v
assert histnum%int('7fffffffffffffffffffffff7fffffffffff8000000000007fffffffffff',16)==int('ffa963cdca8816ccc33b8642bedf905c3d358573d3f27fbbd3b3cb9aaaf',16)
assert hist[:3]==[28989048,38210655,35035436]
assert freelip(20420,30,3)[0]==[297424504,172428383,437688620]

z=int.from_bytes(SEED,'big')
digests=[hashlib.sha1(((z+i)%(1<<160)).to_bytes(20,'big')).digest() for i in range(4096)]
assert int.from_bytes(digests[0]+digests[1],'big')&((1<<255)-1)==C
assert (B*B*C+27)%P==0
hplanted=int.from_bytes(digests[42]+digests[43],'big')%P
sha_hits=[];sha_positive=False;sha_count=0
for i in range(4095):
    for pair,word in [('AB',digests[i]+digests[i+1]),('BA',digests[i+1]+digests[i])]:
        n=int.from_bytes(word,'big')
        for mode,val in [('modp',n%P),('right',n&((1<<256)-1)),('left',n>>64)]:
            sha_count+=1
            if val==X:sha_hits.append([i,pair,mode])
            if i==42 and pair=='AB' and mode=='modp' and val==hplanted:sha_positive=True
assert sha_count==24570 and sha_positive

s=(STAMP<<16)|0x330e
top=bytearray();low=bytearray();outputs=[]
for i in range(80000):
    s=(s*0x5deece66d+11)&((1<<48)-1)
    out=s>>17
    if i<20:outputs.append(out)
    top.append(s>>40);low.append(out&255)
assert bytes(top[1841*20:1842*20])==SEED
libc=ctypes.CDLL(None)
libc.srand48.argtypes=[ctypes.c_long]
libc.lrand48.restype=ctypes.c_long
libc.srand48(STAMP)
assert [libc.lrand48() for _ in range(20)]==outputs
planted_lrand=int.from_bytes(low[36845:36885],'big')%P
lcount=0;lhits=[];lpositive=False
for name,by in [('top8',top),('low8',low)]:
    for width in (32,33,40,64):
        for endian in ('big','little'):
            for at in range(len(by)-width+1):
                val=int.from_bytes(by[at:at+width],endian)%P
                lcount+=1
                if val==X:lhits.append([name,width,endian,at])
                if name=='low8' and width==40 and endian=='big' and at==36845 and val==planted_lrand:lpositive=True
assert lcount==1279340 and lpositive

seeds={
 'be160':int.from_bytes(SEED,'big'),
 'le160':int.from_bytes(SEED,'little'),
 'sha160':int.from_bytes(hashlib.sha1(SEED).digest(),'big'),
 'high32':int.from_bytes(SEED[:4],'big'),
 'low32':int.from_bytes(SEED[-4:],'big'),
}
testseq,_=freelip(seeds['be160'],30,512)
fplanted=number(testseq[27:37],30,'msf')
fcount=0;fhits=[];fpositive=False;rejects=0
for name,seed in seeds.items():
    for bits in (26,30,62):
        seq,reject=freelip(seed,bits,512);rejects+=reject
        length=(256+bits-1)//bits+1
        for order in ('msf','lsf'):
            for at in range(len(seq)-length+1):
                val=number(seq[at:at+length],bits,order)
                fcount+=1
                if val==X:fhits.append([name,bits,order,at])
                if name=='be160' and bits==30 and order=='msf' and at==27 and val==fplanted:fpositive=True
assert fcount==15120 and fpositive and rejects==0
matches={'sha':sha_hits,'lrand48':lhits,'freelip_seed':fhits}
assert not any(matches.values()),'Numerical fit requires full-point and historical source audit'
record={
 'classification':'WARRANTED_BOUNDED_NEGATIVE_AT_EXACT_SOURCE_IF_CI_GREEN; HISTORICAL_ORIGIN_UNKNOWN',
 'frozen_protocol_commit':'9905639d6e834e126a6b778fbcc2a16ef8d443a8',
 'sha_count':sha_count,'lrand_byte_count':lcount,'freelip_seed_count':fcount,
 'total_checked':sha_count+lcount+fcount,'matches':matches,
 'known_historical_prime239v1':True,'NIST_P256_curve_c_exact':True,
 'lrand48_seed1842_exact':True,'system_libc20':True,
 'actual_positive_controls':{'sha':sha_positive,'lrand48':lpositive,'freelip':fpositive},
 'notes':'Overlapping candidate windows. No strong agent, original 1997 ECC point source or ECDSA break. Other P-curves withheld.'
}
Path(__file__).with_name('V3_CI_RESULT.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps(record,indent=2,sort_keys=True))
