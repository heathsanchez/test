// Zero-ternary neighborhood closure for the exact Collatz residual.
//
// A residual binary family is
//   n(q)=M q+b,  M=2^k,
//   y(q)=A q+d,  A=3^c.
//
// The ordinary boundary q=0 belongs to every nested zero 3-adic refinement
//   q=3^r t.
// After this substitution:
//   n_r(t)=M*3^r t+b
//   y_r(t)=A*3^r t+d.
//
// The coefficient ratio A/M is unchanged, but v3(A) grows by r, enabling
// reverse O steps that were not uniformly valid before refinement.
//
// For each exact hereditary residual family, this program finds the least r
// (if any up to R) for which the ENTIRE zero-neighborhood t>=0 has an exact
// uniform lower consequence under the complete finite reverse E/O language.
// If every residual family has such an r, every q=0 boundary point is
// contained in a closed 3-adic neighborhood at that binary depth.

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

static int v3i(i128 x,int cap=100){
  if(x<0)x=-x;int v=0;while(v<cap&&x%3==0){x/=3;++v;}return v;
}
static i128 mulc(i128 a,i128 b){
  if(a<0||b<0||(a&&b>(i128(1)<<120)/a)){std::cerr<<"I128_RANGE\n";std::exit(7);}
  return a*b;
}
static i128 powi(i128 b,int e){i128 x=1;for(int i=0;i<e;++i)x=mulc(x,b);return x;}

static bool lower_family(i128 A,i128 D,i128 M,i128 b,uint64_t L=0){
  const i128 q=i128(L),s=A-M;
  return A>0 && A*q+D>0 && s<=0 && s*q+D-b<0;
}

struct Key{
  i128 A,D;
  bool operator<(const Key&o)const{return A<o.A||(A==o.A&&D<o.D);}
};

struct SearchStats{uint64_t nodes=0,memo=0,e=0,o=0,prune=0;uint64_t maxNodes=0;};

static bool dfs(i128 A,i128 D,i128 M,i128 b,uint64_t L,
                std::set<Key>&seen,uint64_t&local,SearchStats&st){
  ++local;++st.nodes;
  if(A*i128(L)+D<=0)return false;
  if(!seen.emplace(Key{A,D}).second){++st.memo;return false;}

  const int rem=v3i(A);
  if(rem<=0)return false;
  const i128 denAll=powi(3,rem),twAll=powi(2,rem);

  i128 Ae=A,De=D;
  for(int e=0;;++e){
    if(e){
      Ae=mulc(Ae,2);De*=2;
      if(De>(i128(1)<<120)||De<-(i128(1)<<120)){std::cerr<<"D_RANGE\n";std::exit(8);}
    }

    // Uniform lower witnesses require eventual coefficient <= target M.
    // The smallest coefficient reachable after this E-run uses every
    // remaining O step and no further E.
    if(Ae%denAll){std::cerr<<"COEF_DIV\n";std::exit(9);}
    const i128 amin=mulc(Ae/denAll,twAll);
    if(amin>M){++st.prune;break;}
    ++st.e;

    const int mmax=std::min(rem,v3i(De+1));
    i128 den=1,tw=1;
    for(int m=1;m<=mmax;++m){
      den=mulc(den,3);tw=mulc(tw,2);++st.o;
      const i128 A2=mulc(Ae/den,tw);
      const i128 D2=mulc((De+1)/den,tw)-1;
      if(lower_family(A2,D2,M,b,L))return true;
      if(dfs(A2,D2,M,b,L,seen,local,st))return true;
    }
  }
  return false;
}

static bool complete_reverse(i128 A,i128 D,i128 M,i128 b,uint64_t L,SearchStats&st){
  if(lower_family(A,D,M,b,L))return true;
  std::set<Key>seen;uint64_t local=0;
  const bool ok=dfs(A,D,M,b,L,seen,local,st);
  st.maxNodes=std::max(st.maxNodes,local);
  return ok;
}

static uint64_t child_lower(uint64_t L,int bit){
  if(L<=uint64_t(bit))return 0;
  return (L-uint64_t(bit)+1)/2;
}

// Build hereditary residual using the unrefined complete affine language.
static std::vector<State> build_residual(int K,const std::vector<i128>&p3,SearchStats&buildStats){
  std::vector<State>cur{{0,0,0,2}},next;
  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1);
    const i128 M=i128(1)<<k;
    next.clear();
    for(const State&s:cur){
      for(int bit=0;bit<2;++bit){
        const uint64_t L=child_lower(s.L,bit);
        const uint64_t b=s.b+(bit?half:0);
        const i128 P=p3[s.c];
        const i128 raw=i128(s.d)+(bit?P:0);
        uint32_t c=s.c;i128 d;
        if(raw&1){++c;d=(3*raw+1)/2;}else d=raw/2;
        if(d<0||d>i128(UINT64_MAX)){std::cerr<<"D_BUILD_RANGE\n";std::exit(10);}
        if(u128(uint64_t(1)<<k)*L+b<=1){std::cerr<<"DOMAIN_FAIL\n";std::exit(11);}
        if(complete_reverse(p3[c],d,M,i128(b),L,buildStats))continue;
        next.push_back({b,uint64_t(d),c,L});
      }
    }
    uint64_t l0=0,l1=0,lo=0;
    for(const auto&z:next){if(z.L==0)++l0;else if(z.L==1)++l1;else ++lo;}
    std::cout<<"ZERO_TERNARY_BUILD_LEVEL k="<<k<<" live="<<next.size()
             <<" L0="<<l0<<" L1="<<l1<<" otherL="<<lo<<"\n";
    cur.swap(next);
  }
  return cur;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: zero_ternary K R\n";return 2;}
  const int K=std::stoi(argv[1]),R=std::stoi(argv[2]);
  if(K<1||K>24||R<0||R>24)return 2;

  std::vector<i128>p3(K+R+3,1);
  for(size_t i=1;i<p3.size();++i)p3[i]=mulc(p3[i-1],3);

  SearchStats buildStats;
  const auto residual=build_residual(K,p3,buildStats);
  std::cout<<"ZERO_TERNARY_BASE K="<<K<<" residual="<<residual.size()<<" R="<<R<<"\n";

  SearchStats scout;
  std::map<int,uint64_t>hist;
  uint64_t unresolved=0;
  int maxR=-1;
  uint64_t q0direct=0;

  const i128 M0=i128(1)<<K;
  for(const State&s:residual){
    if(s.L!=0){
      std::cout<<"ZERO_TERNARY_NONZERO_L b="<<s.b<<" d="<<s.d
               <<" c="<<s.c<<" L="<<s.L<<"\n";
    }
    bool done=false;
    i128 scale=1;
    for(int r=0;r<=R;++r){
      const i128 M=mulc(M0,scale);
      const i128 A=mulc(p3[s.c],scale);
      if(complete_reverse(A,i128(s.d),M,i128(s.b),0,scout)){
        ++hist[r];maxR=std::max(maxR,r);done=true;break;
      }
      scale=mulc(scale,3);
    }
    if(!done)++unresolved;
  }

  uint64_t cumulative=0;
  for(const auto&kv:hist){
    cumulative+=kv.second;
    std::cout<<"ZERO_TERNARY_CLOSURE r="<<kv.first
             <<" newly_closed="<<kv.second
             <<" cumulative="<<cumulative
             <<" remaining="<<(residual.size()-cumulative)<<"\n";
  }

  std::cout<<"ZERO_TERNARY_RESULT K="<<K
           <<" R="<<R
           <<" residual="<<residual.size()
           <<" closed="<<(residual.size()-unresolved)
           <<" unresolved="<<unresolved
           <<" max_required_r="<<maxR
           <<" search_nodes="<<scout.nodes
           <<" memo_hits="<<scout.memo
           <<" e_cases="<<scout.e
           <<" o_run_cases="<<scout.o
           <<" coefficient_prunes="<<scout.prune
           <<" max_nodes_family="<<scout.maxNodes<<"\n";
  if(unresolved==0)std::cout<<"ALL_Q0_BOUNDARIES_HAVE_FINITE_ZERO_TERNARY_NEIGHBORHOOD\n";
  else std::cout<<"ZERO_TERNARY_BOUNDARY_RESIDUAL_REMAINS\n";
  std::cout<<"VERIFIED_ZERO_TERNARY_BOUNDARY_SCOUT\n";
  return 0;
}
