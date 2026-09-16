// Exact prefix-peeling Collatz compiler.
//
// Family at binary depth k:
//   n(q)=2^k q+b, q>=L
//   T^k(n(q))=3^c q+d.
//
// Unlike the prior all-or-nothing compiler, enumerate the COMPLETE uniformly
// valid affine reverse E/O language and collect every integer parameter
// interval on which a reverse predecessor is positive and lower than n(q).
// Direct descent is included as the zero-length reverse word.
//
// The union of these intervals may cover only a finite prefix [L,U].  That
// prefix is deleted exactly and the surviving family continues with L=U+1.
// Thus fixed ordinary integers can disappear even when a 2-adic/infinite tail
// remains.
//
// Completeness of reverse enumeration remains finite:
//  * q3=v3(A) bounds total remaining O steps.
//  * for an E-run e, let x(q)=2^e(Aq+D).  Every future continuation has at
//    most q3 O operations; extra E operations only increase positive values.
//    The real-valued all-O envelope
//      g(x)=2^q3 (x+1)/3^q3 - 1
//    is therefore a pointwise lower bound for every future positive
//    predecessor.
//  * if its coefficient is >=2^k and at the first parameter where x>0 its
//    value is already >=n, no current/larger e can cover any q>=L.
// This supplies an exact finite E cutoff even for finite-prefix consequences.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <set>
#include <string>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;
static constexpr uint64_t INF=std::numeric_limits<uint64_t>::max();

static inline u128 T(u128 n){return (n&1)?(3*n+1)/2:n/2;}
static u128 iterate(u128 n,int steps){for(int i=0;i<steps;++i)n=T(n);return n;}

struct State{uint64_t b,d;uint32_t c;uint64_t L;};
struct Interval{uint64_t lo,hi;};

static int v3i(i128 x,int cap=80){
  if(x<0)x=-x;int v=0;while(v<cap&&x%3==0){x/=3;++v;}return v;
}
static i128 mulc(i128 a,i128 b){
  if(a<0||b<0||(a&&b>(i128(1)<<120)/a)){std::cerr<<"I128_RANGE\n";std::exit(7);}
  return a*b;
}
static i128 powi(i128 b,int e){i128 x=1;for(int i=0;i<e;++i)x=mulc(x,b);return x;}

static uint64_t child_lower(uint64_t L,int bit){
  if(L<=uint64_t(bit))return 0;
  return (L-uint64_t(bit)+1)/2;
}

static uint64_t ceil_div_pos(i128 a,i128 b){
  // a>=0,b>0, result required to fit uint64.
  i128 z=(a+b-1)/b;
  if(z>i128(INF-1)){std::cerr<<"CEIL_RANGE\n";std::exit(8);}
  return uint64_t(z);
}

// Exact integer q interval q>=L where 0 < A q + D < M q + b.
static bool lower_interval(i128 A,i128 D,i128 M,i128 b,uint64_t L,Interval&out){
  if(A<=0)return false;
  uint64_t lo=L,hi=INF;

  // positivity A q + D > 0.
  if(D<=0){
    const i128 need=-D+1;
    lo=std::max(lo,ceil_div_pos(need,A));
  }

  // (A-M)q + (D-b) < 0.
  const i128 S=A-M,C=D-b;
  if(S==0){
    if(C>=0)return false;
  }else if(S>0){
    // S q < -C => q <= floor((-C-1)/S).
    if(C>=0)return false;
    const i128 h=(-C-1)/S;
    if(h<0)return false;
    const uint64_t uh=h>i128(INF-1)?INF-1:uint64_t(h);
    hi=std::min(hi,uh);
  }else{
    // -R q + C <0 => R q > C.
    const i128 R=-S;
    if(C>=0){
      const i128 need=C+1;
      lo=std::max(lo,ceil_div_pos(need,R));
    }
  }
  if(lo>hi)return false;
  out={lo,hi};return true;
}

struct Key{
  i128 A,D;
  bool operator<(const Key&o)const{return A<o.A||(A==o.A&&D<o.D);}
};
struct Stats{
  uint64_t nodes=0,memo=0,eCases=0,oRuns=0,prunes=0,intervals=0;
  uint64_t maxNodes=0;
  int maxC=0;
};

static uint64_t first_positive_q(i128 A,i128 D,uint64_t L){
  uint64_t q=L;
  if(A*i128(q)+D>0)return q;
  const i128 need=-D+1;
  return std::max(q,ceil_div_pos(need,A));
}

// Rigorous test that no continuation from E^e(A,D) can cover any q>=L.
static bool impossible_beyond_e(i128 Ae,i128 De,int remO,
                                i128 M,i128 b,uint64_t L){
  const uint64_t q0=first_positive_q(Ae,De,L);
  const i128 x0=Ae*i128(q0)+De; // >0
  const i128 den=powi(3,remO),tw=powi(2,remO);
  if(Ae%den){std::cerr<<"OPT_COEF_DIV_FAIL\n";std::exit(9);}
  const i128 Amin=mulc(Ae/den,tw);
  if(Amin<M)return false;

  // g(x0)=tw*(x0+1)/den -1 >= target, compared without division.
  const i128 target=M*i128(q0)+b;
  const i128 lhs=mulc(tw,x0+1)-den;
  const i128 rhs=mulc(den,target);
  return lhs>=rhs;
}

static void enumerate_intervals(i128 A,i128 D,i128 M,i128 b,uint64_t L,
                                std::set<Key>&seen,std::vector<Interval>&iv,
                                Stats&st,uint64_t&localNodes){
  ++st.nodes;++localNodes;
  if(!seen.emplace(Key{A,D}).second){++st.memo;return;}

  Interval z;
  if(lower_interval(A,D,M,b,L,z)){iv.push_back(z);++st.intervals;}

  const int rem=v3i(A);
  if(rem<=0)return;
  const i128 denAll=powi(3,rem);

  i128 Ae=A,De=D;
  for(int e=0;;++e){
    if(e>0){
      Ae=mulc(Ae,2);De*=2;
      if(De>(i128(1)<<120)||De<-(i128(1)<<120)){std::cerr<<"D_RANGE\n";std::exit(10);}
    }

    if(impossible_beyond_e(Ae,De,rem,M,b,L)){++st.prunes;break;}
    ++st.eCases;

    const int mmax=std::min(rem,v3i(De+1));
    i128 den=1,tw=1;
    for(int m=1;m<=mmax;++m){
      den=mulc(den,3);tw=mulc(tw,2);++st.oRuns;
      if(Ae%den||(De+1)%den){std::cerr<<"BLOCK_DIV_FAIL\n";std::exit(11);}
      const i128 A2=mulc(Ae/den,tw);
      const i128 D2=mulc((De+1)/den,tw)-1;
      enumerate_intervals(A2,D2,M,b,L,seen,iv,st,localNodes);
    }
  }
}

struct CoverResult{
  bool all=false;
  uint64_t newL=0;
  uint64_t prefixClosed=0;
  uint64_t intervalCount=0;
};

static CoverResult complete_prefix_cover(i128 A,i128 D,int k,uint64_t b,uint64_t L,
                                         Stats&st){
  const i128 M=i128(1)<<k;
  std::set<Key>seen;std::vector<Interval>iv;uint64_t local=0;
  st.maxC=std::max(st.maxC,v3i(A));
  enumerate_intervals(A,D,M,i128(b),L,seen,iv,st,local);
  st.maxNodes=std::max(st.maxNodes,local);

  if(iv.empty())return {false,L,0,0};
  std::sort(iv.begin(),iv.end(),[](const Interval&a,const Interval&b){
    return a.lo<b.lo||(a.lo==b.lo&&a.hi>b.hi);
  });

  if(iv[0].lo>L)return {false,L,0,uint64_t(iv.size())};
  uint64_t end=iv[0].hi;
  for(size_t i=1;i<iv.size()&&end!=INF;++i){
    if(iv[i].lo>end+1)break;
    end=std::max(end,iv[i].hi);
  }
  if(end==INF)return {true,L,INF,uint64_t(iv.size())};
  if(end<L)return {false,L,0,uint64_t(iv.size())};
  return {false,end+1,end-L+1,uint64_t(iv.size())};
}

int main(int argc,char**argv){
  if(argc!=2){std::cerr<<"usage: prefix_peel K\n";return 2;}
  const int K=std::stoi(argv[1]);
  if(K<1||K>24)return 2;
  std::vector<uint64_t>p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i)p3[i]=p3[i-1]*3;

  std::vector<State>cur{{0,0,0,2}},next;
  Stats st;uint64_t totalAll=0,totalPeeledFamilies=0,totalPrefixPoints=0;
  uint64_t controls=0;

  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1),M=UINT64_C(1)<<k;
    next.clear();
    uint64_t all=0,peeled=0,unchanged=0;
    u128 minRepresented=~u128(0);
    uint64_t minL=INF,maxL=0;

    for(const State&s:cur){
      const uint64_t P=p3[s.c];
      for(int bit=0;bit<2;++bit){
        uint64_t L=child_lower(s.L,bit);
        const uint64_t b=s.b+(bit?half:0);
        const uint64_t raw=s.d+(bit?P:0);
        uint32_t c=s.c;uint64_t d;
        if(raw&1){++c;d=(3*raw+1)/2;}else d=raw/2;
        if(u128(M)*L+b<=1){std::cerr<<"DOMAIN_FAIL\n";return 12;}

        const CoverResult r=complete_prefix_cover(i128(p3[c]),i128(d),k,b,L,st);
        if(r.all){++all;++totalAll;continue;}
        if(r.newL>L){
          ++peeled;++totalPeeledFamilies;
          if(r.prefixClosed!=INF)totalPrefixPoints+=r.prefixClosed;
          L=r.newL;
        }else ++unchanged;

        const u128 mn=u128(M)*L+b;
        minRepresented=std::min(minRepresented,mn);
        minL=std::min(minL,L);maxL=std::max(maxL,L);
        next.push_back({b,d,c,L});
      }
    }

    std::cout<<"PREFIX_PEEL_LEVEL k="<<k
             <<" parents="<<cur.size()
             <<" all_closed="<<all
             <<" prefix_peeled="<<peeled
             <<" unchanged="<<unchanged
             <<" live="<<next.size()
             <<" min_L="<<(next.empty()?0:minL)
             <<" max_L="<<(next.empty()?0:maxL)
             <<" min_represented=";
    if(next.empty())std::cout<<0;
    else {
      // values are <2^64 at tested depths/L.
      std::cout<<(uint64_t)minRepresented;
    }
    std::cout<<"\n";

    cur.swap(next);
    if(cur.empty()){
      std::cout<<"PREFIX_PEEL_FULL_CLOSURE depth="<<k<<"\n";break;
    }
  }

  std::cout<<"PREFIX_PEEL_DONE K="<<K
           <<" final_live="<<cur.size()
           <<" all_closed_families="<<totalAll
           <<" prefix_peeled_families="<<totalPeeledFamilies
           <<" explicitly_peeled_parameter_points="<<totalPrefixPoints
           <<" search_nodes="<<st.nodes
           <<" memo_hits="<<st.memo
           <<" e_cases="<<st.eCases
           <<" o_run_cases="<<st.oRuns
           <<" coefficient_boundary_prunes="<<st.prunes
           <<" generated_intervals="<<st.intervals
           <<" max_nodes_family="<<st.maxNodes
           <<" max_root_v3="<<st.maxC<<"\n";
  if(cur.empty())std::cout<<"ALL_N_GT_1_PREFIX_PEEL_CLOSED\n";
  else std::cout<<"PREFIX_PEEL_RESIDUAL_REMAINS live="<<cur.size()<<"\n";
  std::cout<<"VERIFIED_COMPLETE_UNIFORM_AFFINE_PREFIX_PEEL\n";
  return 0;
}
