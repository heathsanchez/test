#!/usr/bin/env python3
"""Hosted exact H2 separator check for the frozen ac-03887 V1 collision."""
import json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import future_quotient_v1 as fq
CONTACT=((2,1,2,-1,-1,-2,-2,1,1,2,1,2,-1,-2),(-2,-1,-2,-1,2,1,-2,-1,-1))
REPRESENTATIVE=((2,1,2,2,2,1,-2,-1,-2,-2,1,2,-1,-2),(-2,-1,-2,1,2,-1,-2,-2,-1))
H1="bd6a8f51a1573c865f1d204b206733fe3dab9d36600e5eba86c6fffb82cf19cb"
C2="e3b8400b970b3b285ceae77238450f9834aab39ef4e7410d44cf02865c62130b"
R2="54bd39e2ad509c3961891957bfd969bb0ed6c7816717ee097eca0966a6726777"
def h2(core,state):
    root=fq.base_signature(state); xs=[]
    for m in range(core.NUM_MOVES):
        n=core.apply_move(state,m)
        xs.append(fq.future_signature(core,n,10000)[0])
    return fq.digest_parts((root,*xs)).hex()
def main():
    root=Path(sys.argv[1]); sys.path.insert(0,str(root/"competition/tools"))
    from verifier import core
    c1=fq.future_signature(core,CONTACT,10000)[0].hex()
    r1=fq.future_signature(core,REPRESENTATIVE,10000)[0].hex()
    c2=h2(core,CONTACT); r2=h2(core,REPRESENTATIVE)
    assert c1==r1==H1 and c2==C2 and r2==R2 and c2!=r2
    out={"status":"WARRANTED_SEPARATOR","official_pin":fq.OFFICIAL_PIN,"source_artifact":10838365781,"contact_state_key":fq.key_state(CONTACT).hex(),"representative_state_key":fq.key_state(REPRESENTATIVE).hex(),"v1_h1":c1,"contact_h2":c2,"representative_h2":r2,"h2_separates_v1_collision":True,"claim_boundary":"H2 remains search guidance only."}
    Path("h2-separator-evidence.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("ACC_H2_SEPARATOR",json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
