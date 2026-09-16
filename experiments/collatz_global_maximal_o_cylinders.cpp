// Global Collatz valuation cylinders with the maximal uniform inverse-odd cone.
//
// Prefix state:
//   n(q) = r + 2^(A+1) q
//   x(q) = x + 2*3^j q, q>=0
//
// If s = min(v3(x+1),j), then every member of the cylinder admits s uniform
// inverse odd steps and therefore the exact predecessor family
//
//   p_s(q) = 2^s*(x(q)+1)/3^s - 1.
//
// This is the strongest pure-O predecessor that is guaranteed uniformly over
// the whole cylinder.  Direct descent and this predecessor are treated as
// affine inequalities in q; their union is closed exactly when it covers all
// q>=0.
//
// Finite-depth global certificate only; emptiness of the infinite survivor
// intersection is not assumed.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

struct State{u128 r,x;int j,A;};

static std::string s128(u128 z){
  if(!z)return "0";std::string s;
  while(z){s.push_back(char('0'+z%10));z/=10;}
  std::reverse(s.begin(),s.end());return s;
}
static int v2(u128 z){
  if(!z)return 128;uint64_t lo=(uint64_t)z;
  return lo?__builtin_ctzll(lo):64+__builtin_ctzll((uint64_t)(z>>64));
}
static int v3(u128 z,int cap=128){
  int r=0;while(r<cap&&z%3==0){z/=3;++r;}return r;
}
static u128 p3(int j){u128 z=1;while(j--)z*=3;return z;}
static uint64_t invodd(uint64_t a,int bits){
  uint64_t x=a;
  x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;
  if(bits==64)return x;
  return x&((UINT64_C(1)<<bits)-1);
}

static State extend_state(const State&s,int a){
  if(a<1||a>=63||s.A+a+1>=127){std::cerr<<"RANGE_LIMIT\n";std::exit(20);}
  const u128 M=u128(1)<<(s.A+1);
  const uint64_t mod=UINT64_C(1)<<a,mask=mod-1;
  const u128 P=p3(s.j);
  const u128 raw=3*s.x+1,B=raw>>1;
  const uint64_t odd=(uint64_t)((3*P)&mask);
  const uint64_t inv=invodd(odd,a);
  const uint64_t target=UINT64_C(1)<<(a-1);
  const uint64_t diff=(target-(uint64_t)(B&mask))&mask;
  const uint64_t q=(uint64_t)((u128(diff)*inv)&mask);
  State z;
  z.r=s.r+M*u128(q);
  const u128 px=s.x+2*P*u128(q);
  const u128 numer=3*px+1;
  if(v2(numer)!=a){std::cerr<<"VALUATION_CONSTRUCTION_FAIL\n";std::exit(21);}
  z.x=numer>>a;z.j=s.j+1;z.A=s.A+a;
  return z;
}

struct Interval{
  enum Kind{EMPTY,ALL,PREFIX,SUFFIX} kind=EMPTY;
  u128 bound=0; // PREFIX q<=bound; SUFFIX q>=bound
};

static Interval lt_interval(i128 slope,i128 base,u128 minq=0){
  // slope*q+base < 0 on q>=minq.
  Interval z;
  if(slope==0){
    if(base<0){z.kind=Interval::ALL;z.bound=minq;}
    return z;
  }
  if(slope>0){
    if(base>=0)return z;
    const u128 S=(u128)slope;
    const u128 N=(u128)(-base-1);
    u128 U=N/S;
    if(U<minq)return z;
    if(minq==0){z.kind=Interval::PREFIX;z.bound=U;}
    else{
      // We only use minq>0 for predecessor positivity.  A bounded interval
      // starting above zero cannot by itself help cover all q>=0; encode empty
      // for the global-coverage test.
      z.kind=Interval::EMPTY;
    }
    return z;
  }
  const u128 S=(u128)(-slope);
  u128 L=minq;
  if(base>=0){
    const u128 need=(u128)base/S+1;
    if(need>L)L=need;
  }
  if(L==0){z.kind=Interval::ALL;z.bound=0;}
  else{z.kind=Interval::SUFFIX;z.bound=L;}
  return z;
}

static bool covers_all(const Interval&a,const Interval&b){
  if(a.kind==Interval::ALL||b.kind==Interval::ALL)return true;
  auto isPre=[](const Interval&z){return z.kind==Interval::PREFIX;};
  auto isSuf=[](const Interval&z){return z.kind==Interval::SUFFIX;};
  if(isPre(a)&&isSuf(b))return b.bound<=a.bound+1;
  if(isPre(b)&&isSuf(a))return a.bound<=b.bound+1;
  return false;
}

struct Classify{
  bool closed=false;
  bool partial=false;
  int guaranteed_o=0;
};

static Classify classify(const State&s){
  const u128 Ncoef=u128(1)<<(s.A+1);
  const u128 Xcoef=2*p3(s.j);
  const i128 dSlope=i128(Xcoef)-i128(Ncoef);
  const i128 dBase=i128(s.x)-i128(s.r);
  const Interval direct=lt_interval(dSlope,dBase);

  Interval deep;
  int rr=std::min(v3(s.x+1),s.j);
  if(rr>0){
    u128 den=p3(rr),pow2=u128(1)<<rr;
    if((s.x+1)%den){std::cerr<<"DEEP_DIV_FAIL\n";std::exit(22);}
    u128 p0=pow2*((s.x+1)/den)-1;
    u128 Pcoef=(u128(1)<<(rr+1))*p3(s.j-rr);
    // p=0 is not a positive predecessor at q=0; q>=1 remains admissible.
    u128 minq=(p0==0)?1:0;
    deep=lt_interval(i128(Pcoef)-i128(Ncoef),
                     i128(p0)-i128(s.r),minq);
  }

  Classify c;c.guaranteed_o=rr;
  c.closed=covers_all(direct,deep);
  if(!c.closed){
    c.partial=(direct.kind!=Interval::EMPTY||deep.kind!=Interval::EMPTY);
  }
  return c;
}

static int direct_tail_start(const State&s){
  const u128 P=p3(s.j),M=u128(1)<<(s.A+1);
  const int a0=v2(3*s.x+1);
  int a=std::max(1,a0+1);
  for(;;++a){
    if(a>=63){std::cerr<<"TAIL_BOUND_RANGE_FAIL\n";std::exit(23);}
    const u128 lhs=3*s.x+1+6*P;
    const u128 rhs=(u128(1)<<a)*(s.r+M);
    const bool slope=(6*P)<((u128(1)<<a)*M);
    if(slope&&lhs<rhs)return a;
  }
}

static long double density(const std::vector<State>&v){
  long double z=0;for(auto&s:v)z+=std::ldexp((long double)1.0,-s.A);return z;
}

int main(int argc,char**argv){
  int DEPTH=18;if(argc==2)DEPTH=std::stoi(argv[1]);
  if(DEPTH<1||DEPTH>26)return 2;
  std::vector<State> live{{1,1,0,0}};
  uint64_t totalClosed=0,totalPartial=0,totalTails=0;
  std::cout<<"GLOBAL_MAXO_START depth="<<DEPTH<<"\n";
  for(int depth=1;depth<=DEPTH;++depth){
    std::vector<State> next;
    uint64_t closed=0,partial=0,tails=0,children=0;
    uint64_t o1=0,o2p=0;
    u128 minr=~u128(0);int minA=0,maxO=0;
    for(const State&parent:live){
      int tail=direct_tail_start(parent);++tails;++totalTails;
      for(int a=1;a<tail;++a){
        ++children;
        State z=extend_state(parent,a);
        auto c=classify(z);
        maxO=std::max(maxO,c.guaranteed_o);
        if(c.guaranteed_o==1)++o1;
        if(c.guaranteed_o>=2)++o2p;
        if(c.closed){++closed;++totalClosed;continue;}
        if(c.partial){++partial;++totalPartial;}
        next.push_back(z);
        if(z.r<minr){minr=z.r;minA=z.A;}
      }
    }
    std::cout<<"GLOBAL_MAXO_LEVEL depth="<<depth
             <<" parents="<<live.size()
             <<" explicit_children="<<children
             <<" infinite_direct_tails="<<tails
             <<" closed="<<closed
             <<" partial="<<partial
             <<" survivors="<<next.size()
             <<" density="<<(double)density(next)
             <<" o1_children="<<o1
             <<" o2plus_children="<<o2p
             <<" max_uniform_o="<<maxO;
    if(!next.empty())std::cout<<" min_survivor_r="<<s128(minr)
                              <<" min_survivor_A="<<minA;
    std::cout<<"\n";
    live.swap(next);
  }
  std::cout<<"GLOBAL_MAXO_RESULT depth="<<DEPTH
           <<" survivors="<<live.size()
           <<" density="<<(double)density(live)
           <<" total_closed="<<totalClosed
           <<" total_partial="<<totalPartial
           <<" infinite_direct_tails="<<totalTails<<"\n";
  if(totalPartial==0)std::cout<<"MAXO_NO_PARTIAL_CYLINDERS\n";
  else std::cout<<"MAXO_PARTIAL_CYLINDERS_RETAINED\n";
  std::cout<<"FINAL_GATE=GLOBAL_MAXIMAL_O_CYLINDER_DEPTH_"<<DEPTH<<"\n";
}
