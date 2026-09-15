// Reduced consequence-language DAG for exact Collatz transfer survival.
//
// Numerical prefix states can all be distinct while still having identical
// future consequences.  This scout constructs the exact finite live/dead
// suffix tree through TARGET_P, then minimizes it bottom-up as an ordered
// binary decision diagram (ROBDD):
//
//   two nodes merge iff every remaining suffix has the same consequence.
//
// This is the goal-equivalence quotient, not state-identity quotienting.
// Terminal 0 = coefficient contraction proved within the horizon.
// Terminal 1 = survives through TARGET_P.
//
// Scientific scope: coefficient-survival consequence only.  It does not replace
// the exact seed verifier.

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using u128=unsigned __int128;
static constexpr uint32_t DEAD=UINT32_MAX;

static std::string s128(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}

struct State{
  uint64_t lo,hi;
  uint8_t q;
};
static inline u128 val(const State&s){return u128(s.lo)|(u128(s.hi)<<64);}
static inline State state(u128 d,uint8_t q){return State{uint64_t(d),uint64_t(d>>64),q};}

struct Edges{uint32_t z,o;};

struct BKey{
  uint16_t var;
  uint32_t lo,hi;
  bool operator==(const BKey&o)const{return var==o.var&&lo==o.lo&&hi==o.hi;}
};
struct BHash{
  size_t operator()(const BKey&x)const{
    uint64_t z=(uint64_t(x.lo)<<32)|x.hi;
    z^=uint64_t(x.var)*UINT64_C(0x9e3779b97f4a7c15);
    z^=z>>33;z*=UINT64_C(0xff51afd7ed558ccd);
    z^=z>>33;z*=UINT64_C(0xc4ceb9fe1a85ec53);
    z^=z>>33;return(size_t)z;
  }
};

int main(int argc,char**argv){
  if(argc<3||argc>4){
    std::cerr<<"usage: scout K TARGET_P [MAX_LIVE]\n";return 2;
  }
  const int K=std::stoi(argv[1]);
  const int TARGET=std::stoi(argv[2]);
  const uint64_t MAXL=argc==4?std::stoull(argv[3]):55000000ULL;
  if(K<1||K>50||TARGET<3||K+TARGET>=127){std::cerr<<"BAD_RANGE\n";return 2;}

  std::array<u128,128>P3{};
  P3[0]=1;
  for(int i=1;i<128;++i){
    if(P3[i-1]>(~u128(0))/3)break;
    P3[i]=P3[i-1]*3;
  }

  // p=2 after exact predecessor-half removal.
  const int killed_mod4=(K&1)?3:1;
  std::vector<State> cur;
  for(uint64_t r: {1ULL,3ULL}){
    if(int(r&3ULL)==killed_mod4)continue;
    u128 x=(u128(r)<<K)-1;
    uint8_t q=0;bool alive=true;
    for(int t=1;t<=K+2;++t){
      if(x&1){++q;x=(3*x+1)/2;}else x/=2;
      if(P3[q]<(u128(1)<<t))alive=false;
    }
    if(alive)cur.push_back(state(x,q));
  }

  std::vector<std::vector<Edges>> layers;
  std::vector<uint64_t> live_counts;
  live_counts.push_back(cur.size());
  std::cout<<"LANG_FORWARD K="<<K<<" p=2 live="<<cur.size()<<"\n";

  for(int p=2;p<TARGET && !cur.empty();++p){
    const int np=p+1,W=K+np;
    std::vector<State> nxt;
    nxt.reserve(std::min<uint64_t>(MAXL,cur.size()*2ULL));
    std::vector<Edges> edges(cur.size(),Edges{DEAD,DEAD});

    for(size_t i=0;i<cur.size();++i){
      const State&st=cur[i];
      const u128 d=val(st);
      const u128 pq=P3[st.q];
      for(int b=0;b<2;++b){
        u128 y=d+u128(b)*pq;
        uint8_t q2=st.q;
        u128 d2;
        if(y&1){++q2;d2=(3*y+1)/2;}else d2=y/2;
        if(P3[q2]<(u128(1)<<W))continue;
        uint32_t idx=(uint32_t)nxt.size();
        nxt.push_back(state(d2,q2));
        if(b==0)edges[i].z=idx;else edges[i].o=idx;
        if(nxt.size()>MAXL){
          std::cout<<"LANG_ABORT K="<<K<<" p="<<np<<" live_exceeded="<<MAXL<<"\n";
          return 0;
        }
      }
    }

    layers.push_back(std::move(edges));
    cur.swap(nxt);
    live_counts.push_back(cur.size());
    std::cout<<"LANG_FORWARD K="<<K<<" p="<<np<<" live="<<cur.size()<<"\n";
  }

  if((int)layers.size()!=TARGET-2){
    std::cout<<"LANG_INCOMPLETE K="<<K<<" built_p="<<(layers.size()+2)<<"\n";
    return 0;
  }

  // Global reduced ordered BDD.  IDs 0/1 are dead/live terminals.
  uint32_t next_id=2;
  std::unordered_map<BKey,uint32_t,BHash> intern;
  intern.reserve(1000000);

  std::vector<uint32_t> sig_next(cur.size(),1);
  uint64_t total_new_nodes=0;

  for(int li=(int)layers.size()-1;li>=0;--li){
    const int p=li+2; // parent prefix depth
    const auto&edges=layers[li];
    std::vector<uint32_t> sig_cur(edges.size());
    std::unordered_set<uint32_t> distinct;
    distinct.reserve(std::min<size_t>(edges.size(),1000000));

    uint64_t new_here=0,reduced_equal=0;
    for(size_t i=0;i<edges.size();++i){
      uint32_t lo=edges[i].z==DEAD?0:sig_next[edges[i].z];
      uint32_t hi=edges[i].o==DEAD?0:sig_next[edges[i].o];
      uint32_t id;
      if(lo==hi){
        id=lo;
        ++reduced_equal;
      }else{
        BKey key{(uint16_t)p,lo,hi};
        auto [it,inserted]=intern.emplace(key,next_id);
        if(inserted){id=next_id++;++new_here;}
        else id=it->second;
      }
      sig_cur[i]=id;
      distinct.insert(id);
    }
    total_new_nodes+=new_here;
    std::cout<<"LANG_REDUCE K="<<K
             <<" p="<<p
             <<" raw_parents="<<edges.size()
             <<" distinct_signatures="<<distinct.size()
             <<" new_bdd_nodes="<<new_here
             <<" equal_branch_reductions="<<reduced_equal
             <<"\n";
    sig_next.swap(sig_cur);
  }

  if(sig_next.size()!=live_counts[0]){std::cerr<<"ROOT_SIZE_MISMATCH\n";return 3;}
  std::cout<<"LANG_BDD_DONE K="<<K
           <<" target_p="<<TARGET
           <<" final_live_leaves="<<live_counts.back()
           <<" bdd_nonterminal_nodes="<<total_new_nodes
           <<" bdd_total_ids="<<next_id
           <<" root_signature="<<(sig_next.empty()?0:sig_next[0])
           <<" raw_transition_parents=";
  u128 raw=0;for(const auto&v:layers)raw+=v.size();
  std::cout<<s128(raw)<<"\n";
  return 0;
}
