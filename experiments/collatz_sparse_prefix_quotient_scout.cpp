// Quotiented sparse exact Collatz prefix automaton.
//
// After fixed valuation K and prefix depth p, each surviving residue class has
// an exact transformed state (d,q), where d is the low-family image after
// W=K+p shortcut steps and q is the number of odd steps.
//
// Future bit extensions depend ONLY on (d,q), not on the historical residue.
// Therefore residues with identical (d,q) are goal-equivalent for transfer
// survival and may be quotient-merged. We retain a multiplicity count so the
// exact number of represented residue classes is preserved.
//
// This is a scientific scout: it measures whether quotienting turns the sparse
// prefix tree into a compact DAG. It does not itself certify concrete seeds.

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

using u128=unsigned __int128;

static std::string s128(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}

struct Key{
  uint64_t lo,hi;
  uint8_t q;
  bool operator==(const Key&o)const{return lo==o.lo&&hi==o.hi&&q==o.q;}
};
struct Hash{
  size_t operator()(const Key&x)const{
    uint64_t z=x.lo ^ (x.hi*UINT64_C(0x9e3779b97f4a7c15)) ^ (uint64_t(x.q)<<56);
    z^=z>>33; z*=UINT64_C(0xff51afd7ed558ccd);
    z^=z>>33; z*=UINT64_C(0xc4ceb9fe1a85ec53);
    z^=z>>33; return (size_t)z;
  }
};
struct Node{
  u128 d;
  uint8_t q;
  u128 multiplicity;
};

static Key key_of(u128 d,uint8_t q){
  return Key{(uint64_t)d,(uint64_t)(d>>64),q};
}

static inline u128 T(u128 x){return(x&1)?(3*x+1)/2:x/2;}

int main(int argc,char**argv){
  if(argc<3||argc>4){
    std::cerr<<"usage: scout K PMAX [MAX_NODES]\n";return 2;
  }
  int K=std::stoi(argv[1]),PMAX=std::stoi(argv[2]);
  uint64_t MAXN=argc==4?std::stoull(argv[3]):10000000ULL;
  if(K<1||K>50||PMAX<2||K+PMAX>=127){std::cerr<<"BAD_RANGE\n";return 2;}

  std::array<u128,128>P3{};
  P3[0]=1;
  for(int i=1;i<128;++i){
    if(P3[i-1]>(~u128(0))/3)break;
    P3[i]=P3[i-1]*3;
  }

  // Build the single surviving p=2 class explicitly, applying the exact
  // predecessor-half sieve before quotient dynamics begin.
  const int killed_mod4=(K&1)?3:1;
  std::vector<Node> cur;
  u128 represented=0;
  for(uint64_t r: {1ULL,3ULL}){
    if((int)(r&3ULL)==killed_mod4)continue;
    u128 x=(u128(r)<<K)-1;
    uint8_t q=0; bool alive=true;
    const int W=K+2;
    for(int t=1;t<=W;++t){
      if(x&1){++q;x=(3*x+1)/2;}else x/=2;
      if(P3[q]<(u128(1)<<t))alive=false;
    }
    if(alive){cur.push_back(Node{x,q,1});represented+=1;}
  }

  std::cout<<"QUOTIENT_PREFIX_LEVEL"
           <<" K="<<K<<" p=2 W="<<(K+2)
           <<" nodes="<<cur.size()
           <<" represented_live_classes="<<s128(represented)
           <<" compression=1\n";

  for(int p=2;p<PMAX && !cur.empty();++p){
    const int np=p+1;
    const int W=K+np;
    std::unordered_map<Key,size_t,Hash> index;
    index.reserve(std::min<uint64_t>(MAXN,cur.size()*2ULL));
    std::vector<Node> nxt;
    nxt.reserve(std::min<uint64_t>(MAXN,cur.size()*2ULL));
    u128 live=0;

    for(const Node&st:cur){
      const u128 pq=P3[st.q];
      for(int b=0;b<2;++b){
        u128 y=st.d + u128(b)*pq;
        uint8_t q2=st.q;
        u128 d2;
        if(y&1){++q2;d2=(3*y+1)/2;}else d2=y/2;
        if(P3[q2]<(u128(1)<<W))continue;

        Key k=key_of(d2,q2);
        auto it=index.find(k);
        if(it==index.end()){
          size_t pos=nxt.size();
          index.emplace(k,pos);
          nxt.push_back(Node{d2,q2,st.multiplicity});
          if(nxt.size()>MAXN){
            std::cout<<"QUOTIENT_PREFIX_ABORT"
                     <<" K="<<K<<" p="<<np
                     <<" nodes_exceeded="<<MAXN<<"\n";
            return 0;
          }
        }else{
          nxt[it->second].multiplicity += st.multiplicity;
        }
        live += st.multiplicity;
      }
    }

    cur.swap(nxt);
    represented=live;
    long double comp = cur.empty()?0.0L:
      (long double)(uint64_t)std::min<u128>(represented,u128(UINT64_MAX))/
      (long double)cur.size();
    std::cout<<"QUOTIENT_PREFIX_LEVEL"
             <<" K="<<K<<" p="<<np<<" W="<<W
             <<" nodes="<<cur.size()
             <<" represented_live_classes="<<s128(represented)
             <<" compression="<<(double)comp
             <<"\n";
  }

  std::cout<<"QUOTIENT_PREFIX_DONE K="<<K
           <<" nodes="<<cur.size()
           <<" represented_live_classes="<<s128(represented)<<"\n";
  return 0;
}
