// Deterministic zero-child tail closure of the exact Collatz residual.
//
// Build the exact hereditary residual at binary depth K using complete affine
// reverse-language closure. Every final state has L=0.
//
// For the ordinary boundary q=0, all future binary parameter bits are zero.
// Hence b is fixed and the endpoint intercept follows the concrete shortcut
// orbit d -> T(d), while k increases and c records odd steps.
//
// At each zero-child extension we test the ENTIRE resulting affine family by
// the complete reverse-language decision. If it closes, the q=0 boundary is
// certainly closed. This is stronger than merely checking the concrete b.
//
// The census records the exact number of extra zero steps needed for every
// residual boundary. It is a finite-depth theorem scout, not by itself a
// global proof unless a depth-independent rank/bound is established.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <vector>

using i128=__int128;
using u128=unsigned __int128;

struct State{uint64_t b,d;uint32_t c;uint64_t L;};

static int v3i(i128 x,int cap=120){if(x<0)x=-x;int v=0;while(v<cap&&x%3==0){x/=3;++v;}return v;}
static i128 mulc(i128 a,i128 b){
  if(a<0||b<0||(a&&b>(i128(1)<<122)/a)){std::cerr<<"I128_RANGE\n";std::exit(7);}
  return a*b;
}
static i128 powi(i128 b,int e){i128 x=1;for(int i=0;i<e;++i)x=mulc(x,b);return x;}
static uint64_t child_lower(uint64_t L,int bit){if(L<=uint64_t(bit))return 0;return (L-uint64_t(bit)+1)/2;}

static bool lower_family(i128 A,i128 D,i128 M,i128 b,uint64_t L){
  const i128 q=i128(L),s=A-M;
  return A>0 && A*q+D>0 && s<=0 && s*q+D-b<0;
}

struct Key{i128 A,D;bool operator<(const Key&o)const{return A<o.A||(A==o.A&&D<o.D);}};
struct Stats{uint64_t nodes=0,memo=0,e=0,o=0,prunes=0,maxNodes=0;};

static bool dfs(i128 A,i128 D,i128 M,i128 b,uint64_t L,
                std::set<Key>&seen,uint64_t&local,Stats&st){
  ++local;++st.nodes;
  if(A*i128(L)+D<=0)return false;
  if(!seen.emplace(Key{A,D}).second){++st.memo;return false;}
  const int rem=v3i(A);if(rem<=0)return false;
  const i128 denAll=powi(3,rem),twAll=powi(2,rem);
  i128 Ae=A,De=D;
  for(int e=0;;++e){
    if(e){Ae=mulc(Ae,2);De*=2;if(De>(i128(1)<<122)||De<-(i128(1)<<122)){std::cerr<<"D_RANGE\n";std::exit(8);}}
    if(Ae%denAll){std::cerr<<"COEF_DIV\n";std::exit(9);}
    const i128 amin=mulc(Ae/denAll,twAll);
    if(amin>M){++st.prunes;break;}
    ++st.e;
    const int mmax=std::min(rem,v3i(De+1));
    i128 den=1,tw=1;
    for(int m=1;m<=mmax;++m){
      den=mulc(den,3);tw=mulc(tw,2);++st.o;
      const i128 A2=mulc(Ae/den,tw),D2=mulc((De+1)/den,tw)-1;
      if(lower_family(A2,D2,M,b,L))return true;
      if(dfs(A2,D2,M,b,L,seen,local,st))return true;
    }
  }
  return false;
}
static bool closes(i128 A,i128 D,i128 M,i128 b,uint64_t L,Stats&st){
  if(lower_family(A,D,M,b,L))return true;
  std::set<Key>seen;uint64_t local=0;
  bool ok=dfs(A,D,M,b,L,seen,local,st);
  st.maxNodes=std::max(st.maxNodes,local);return ok;
}

static std::vector<State> build(int K,const std::vector<i128>&p3,Stats&st){
  std::vector<State>cur{{0,0,0,2}},next;
  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1);const i128 M=i128(1)<<k;
    next.clear();
    for(const auto&s:cur){
      for(int bit=0;bit<2;++bit){
        uint64_t L=child_lower(s.L,bit),b=s.b+(bit?half:0);
        i128 raw=i128(s.d)+(bit?p3[s.c]:0);uint32_t c=s.c;i128 d;
        if(raw&1){++c;d=(3*raw+1)/2;}else d=raw/2;
        if(closes(p3[c],d,M,b,L,st))continue;
        next.push_back({b,uint64_t(d),c,L});
      }
    }
    cur.swap(next);
  }
  return cur;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: zero_tail K H\n";return 2;}
  const int K=std::stoi(argv[1]),H=std::stoi(argv[2]);
  if(K<1||K>24||H<1||H>1024)return 2;

  std::vector<i128>p3(K+H+3,1);
  for(size_t i=1;i<p3.size();++i)p3[i]=mulc(p3[i-1],3);

  Stats buildStats;
  const auto residual=build(K,p3,buildStats);
  const std::map<int,uint64_t> frozen{{12,144},{16,1363},{20,15870},{24,172868}};
  auto fi=frozen.find(K);
  if(fi!=frozen.end()&&residual.size()!=fi->second){
    std::cerr<<"ZERO_TAIL_BASELINE_DRIFT\n";return 10;
  }

  Stats scout;std::map<int,uint64_t>hist;
  uint64_t unresolved=0;int maxT=-1;uint64_t maxB=0;
  uint64_t directBoundaryDescent=0,reverseFamilyClose=0;
  for(const auto&s0:residual){
    if(s0.L!=0){std::cerr<<"EXPECTED_L0\n";return 11;}
    uint64_t d=s0.d;uint32_t c=s0.c;bool done=false;
    for(int t=1;t<=H;++t){
      // zero child: b fixed, q=0, endpoint intercept follows T.
      if(d&1){++c;d=(3*d+1)/2;}else d/=2;
      const int kk=K+t;
      const i128 M=i128(1)<<kk;
      const i128 A=p3[c];
      if(closes(A,i128(d),M,i128(s0.b),0,scout)){
        ++hist[t];if(t>maxT){maxT=t;maxB=s0.b;}
        if(d<s0.b)++directBoundaryDescent;else ++reverseFamilyClose;
        done=true;break;
      }
    }
    if(!done)++unresolved;
  }

  uint64_t cum=0;
  for(const auto&kv:hist){
    cum+=kv.second;
    if(kv.first<=32 || kv.first==maxT)
      std::cout<<"ZERO_TAIL_CLOSURE t="<<kv.first<<" newly="<<kv.second
               <<" cumulative="<<cum<<" remaining="<<(residual.size()-cum)<<"\n";
  }
  std::cout<<"ZERO_TAIL_RESULT K="<<K<<" H="<<H
           <<" residual="<<residual.size()
           <<" closed="<<(residual.size()-unresolved)
           <<" unresolved="<<unresolved
           <<" max_extra_steps="<<maxT
           <<" max_witness_b="<<maxB
           <<" boundary_d_below_at_close="<<directBoundaryDescent
           <<" reverse_family_close="<<reverseFamilyClose
           <<" search_nodes="<<scout.nodes
           <<" memo_hits="<<scout.memo
           <<" e_cases="<<scout.e
           <<" o_run_cases="<<scout.o
           <<" prunes="<<scout.prunes
           <<" max_nodes_family="<<scout.maxNodes<<"\n";
  if(!unresolved)std::cout<<"ALL_RESIDUAL_ZERO_TAILS_CLOSE_WITHIN_H"<<H<<"\n";
  else std::cout<<"ZERO_TAIL_RESIDUAL_REMAINS\n";
  std::cout<<"VERIFIED_ZERO_TAIL_CLOSURE_CENSUS\n";
  return 0;
}
