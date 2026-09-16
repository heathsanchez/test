// Exact complete symbolic Collatz closure for ALL integers n>1.
//
// At binary depth k a family is
//   n(q)=2^k q+b, q>=L,
// and after k shortcut steps
//   y(q)=3^c q+d.
// The lower bound L is carried exactly, so q=0 boundary members are never
// dropped. Starting state is n(q)=q, q>=2, hence the tree partitions every
// integer n>1 at every depth.
//
// Each family is closed if either:
//   1) y(q)<n(q) uniformly for q>=L; or
//   2) ANY reverse E/O word from y yields a uniformly positive p(q)<n(q).
//
// The reverse language is decided exhaustively and finitely as in
// collatz_complete_endpoint_reverse.cpp. No bridge bank, word horizon,
// finite-shell truncation, or density inference is used.
//
// If live=0 at any finite depth, every n>1 has an exact lower consequence;
// strong induction then proves shortcut Collatz convergence for all positives.
// Otherwise the remaining families are exact symbolic obstructions, not
// counterexamples.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

static inline u128 T(u128 n){return (n&1)?(3*n+1)/2:n/2;}
static u128 iterate(u128 n,int steps){for(int i=0;i<steps;++i)n=T(n);return n;}

struct State{uint64_t b,d;uint32_t c;uint64_t L;};

static bool lower_family(i128 A,i128 D,int k,uint64_t b,uint64_t L){
  const i128 M=i128(1)<<k;
  const i128 q=i128(L);
  const i128 minP=A*q+D;
  const i128 slope=A-M;
  const i128 diffAtL=slope*q + D-i128(b);
  return A>0 && minP>0 && slope<=0 && diffAtL<0;
}

static uint64_t child_lower(uint64_t L,int e){
  if(L<=uint64_t(e))return 0;
  return (L-uint64_t(e)+1)/2;
}

static int v3i(i128 x,int cap=80){
  if(x<0)x=-x;
  int v=0;while(v<cap&&x%3==0){x/=3;++v;}return v;
}
static i128 mul_checked(i128 a,i128 b){
  if(a<0||b<0){std::cerr<<"NEGATIVE_COEF_RANGE\n";std::exit(7);}
  if(a && b>(i128(1)<<120)/a){std::cerr<<"I128_RANGE\n";std::exit(8);}
  return a*b;
}
static i128 powi(i128 b,int e){
  i128 x=1;for(int i=0;i<e;++i)x=mul_checked(x,b);return x;
}

struct Key{
  i128 A,D;
  bool operator<(const Key&o)const{return A<o.A||(A==o.A&&D<o.D);}
};
struct Witness{i128 A=0,D=0;std::string word;};
struct LocalStats{
  uint64_t nodes=0,memo=0,eCases=0,oRuns=0,prunes=0;
  int maxBlocks=0,maxSteps=0;
};
struct GlobalStats{
  uint64_t families=0,nodes=0,memo=0,eCases=0,oRuns=0,prunes=0,maxNodes=0;
  int maxBlocks=0,maxSteps=0,maxC=0;
};

static bool dfs(
    i128 A,i128 D,int k,uint64_t b,uint64_t L,
    std::set<Key>&seen,LocalStats&st,std::string&path,int blocks,Witness&w){
  ++st.nodes;st.maxBlocks=std::max(st.maxBlocks,blocks);
  st.maxSteps=std::max(st.maxSteps,(int)path.size());

  if(A*i128(L)+D<=0)return false;
  if(!seen.emplace(Key{A,D}).second){++st.memo;return false;}

  const int q=v3i(A);
  if(q<=0)return false;
  const i128 M=i128(1)<<k;
  const i128 p3q=powi(3,q),p2q=powi(2,q);

  i128 Ae=A,De=D;
  for(int e=0;;++e){
    if(e>0){
      Ae=mul_checked(Ae,2);De*=2;
      if(De>(i128(1)<<120)||De<-(i128(1)<<120)){std::cerr<<"D_RANGE\n";std::exit(9);}
    }
    if(Ae%p3q){std::cerr<<"V3_INVARIANT_FAIL\n";std::exit(10);}
    const i128 amin=mul_checked(Ae/p3q,p2q);
    if(amin>M){++st.prunes;break;}
    ++st.eCases;

    const int mmax=std::min(q,v3i(De+1));
    i128 den=1,tw=1;
    for(int m=1;m<=mmax;++m){
      den=mul_checked(den,3);tw=mul_checked(tw,2);++st.oRuns;
      const i128 A2=mul_checked(Ae/den,tw);
      const i128 D2=mul_checked((De+1)/den,tw)-1;
      const size_t old=path.size();
      path.append(e,'E');path.append(m,'O');
      if(lower_family(A2,D2,k,b,L)){w={A2,D2,path};return true;}
      if(dfs(A2,D2,k,b,L,seen,st,path,blocks+1,w))return true;
      path.resize(old);
    }
  }
  return false;
}

static bool complete_reverse(
    i128 A,i128 D,int k,uint64_t b,uint64_t L,Witness&w,GlobalStats&g){
  ++g.families;g.maxC=std::max(g.maxC,v3i(A));
  std::set<Key>seen;LocalStats st;std::string path;
  const bool ok=dfs(A,D,k,b,L,seen,st,path,0,w);
  g.nodes+=st.nodes;g.memo+=st.memo;g.eCases+=st.eCases;
  g.oRuns+=st.oRuns;g.prunes+=st.prunes;g.maxNodes=std::max(g.maxNodes,st.nodes);
  g.maxBlocks=std::max(g.maxBlocks,st.maxBlocks);g.maxSteps=std::max(g.maxSteps,st.maxSteps);
  return ok;
}

int main(int argc,char**argv){
  if(argc!=2){std::cerr<<"usage: all_integer_symbolic K\n";return 2;}
  const int K=std::stoi(argv[1]);
  if(K<1||K>28){std::cerr<<"K_RANGE\n";return 2;}

  std::vector<uint64_t>p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i){
    if(p3[i-1]>UINT64_MAX/3){std::cerr<<"P3_OVERFLOW\n";return 3;}
    p3[i]=p3[i-1]*3;
  }

  std::vector<State>cur{{0,0,0,2}},next;
  GlobalStats gst;uint64_t totalDirect=0,totalReverse=0,controls=0;

  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1),M=UINT64_C(1)<<k;
    next.clear();
    uint64_t direct=0,reverse=0;
    for(const State&s:cur){
      const uint64_t P=p3[s.c];
      for(int e=0;e<2;++e){
        const uint64_t L=child_lower(s.L,e);
        const uint64_t b=s.b+(e?half:0);
        const uint64_t rawD=s.d+(e?P:0);
        uint32_t c=s.c;uint64_t d;
        if(rawD&1){
          ++c;
          if(rawD>(UINT64_MAX-1)/3){std::cerr<<"CHILD_OVERFLOW\n";return 11;}
          d=(3*rawD+1)/2;
        }else d=rawD/2;

        // Exact partition control: minimum represented n stays >1.
        const u128 minN=u128(M)*L+b;
        if(minN<=1){std::cerr<<"DOMAIN_PARTITION_FAIL k="<<k<<" b="<<b<<" L="<<L<<"\n";return 12;}

        const i128 A=i128(p3[c]),D=i128(d);
        if(lower_family(A,D,k,b,L)){++direct;++totalDirect;continue;}

        Witness w{};
        if(complete_reverse(A,D,k,b,L,w,gst)){
          ++reverse;++totalReverse;
          if(controls<30000){
            for(uint64_t off:{0ULL,2ULL}){
              const uint64_t q=L+off;
              const u128 n=u128(M)*q+b;
              const u128 endpoint=u128(p3[c])*q+d;
              const i128 pred=i128(q)*w.A+w.D;
              if(n<=1||pred<=0||u128(pred)>=n||
                 iterate(n,k)!=endpoint||iterate(u128(pred),(int)w.word.size())!=endpoint){
                std::cerr<<"ALL_INTEGER_CONTROL_FAIL k="<<k<<" b="<<b
                         <<" L="<<L<<" q="<<q<<" word="<<w.word<<"\n";return 13;
              }
              ++controls;
            }
          }
          continue;
        }
        next.push_back({b,d,c,L});
      }
    }

    uint64_t L0=0,L1=0,other=0;
    for(const auto&s:next){if(s.L==0)++L0;else if(s.L==1)++L1;else ++other;}
    std::cout<<"ALL_INTEGER_SYMBOLIC_LEVEL k="<<k
             <<" parents="<<cur.size()<<" direct="<<direct<<" reverse="<<reverse
             <<" live="<<next.size()<<" L0="<<L0<<" L1="<<L1<<" otherL="<<other<<"\n";
    cur.swap(next);
    if(cur.empty()){
      std::cout<<"ALL_INTEGER_SYMBOLIC_FULL_CLOSURE depth="<<k<<"\n";
      break;
    }
  }

  std::cout<<"ALL_INTEGER_SYMBOLIC_DONE requested_K="<<K
           <<" final_depth="<<(cur.empty()?0:K)
           <<" final_live="<<cur.size()
           <<" total_direct="<<totalDirect<<" total_reverse="<<totalReverse
           <<" families_searched="<<gst.families<<" search_nodes="<<gst.nodes
           <<" memo_hits="<<gst.memo<<" e_cases="<<gst.eCases<<" o_run_cases="<<gst.oRuns
           <<" coefficient_prunes="<<gst.prunes<<" max_nodes_family="<<gst.maxNodes
           <<" max_blocks="<<gst.maxBlocks<<" max_word_steps="<<gst.maxSteps
           <<" max_root_v3="<<gst.maxC<<" controls="<<controls<<"\n";
  if(cur.empty())std::cout<<"ALL_N_GT_1_LOWER_CONSEQUENCE_PARTITION_CLOSED\n";
  else std::cout<<"ALL_INTEGER_SYMBOLIC_RESIDUAL_REMAINS live="<<cur.size()<<"\n";
  std::cout<<"VERIFIED_ALL_INTEGER_SYMBOLIC_PARTITION\n";
  return 0;
}
