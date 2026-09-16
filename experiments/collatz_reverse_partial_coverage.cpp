// Exact global Collatz cylinders with UNION coverage from reverse E^e O donors.
//
// State after j accelerated odd steps:
//   n(q)=r+2^(A+1)q
//   x(q)=x+2*3^j q, q>=0.
//
// Every reverse macro word produces an affine donor p(q)=a q+d that reaches
// x(q).  Instead of requiring one donor to satisfy 0<p(q)<n(q) for all q,
// collect the exact integer interval on which each donor is lower.  Since each
// inequality is affine, every contribution is ALL, a PREFIX q<=U, or a
// SUFFIX q>=L.  The union closes the entire cylinder exactly when U+1>=L.
//
// This is strictly stronger than single-donor closure and remains exact.
// Finite macro depth only; survivors are UNKNOWN, never counterexamples.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <cmath>
#include <iostream>
#include <string>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

struct State{u128 r,x;int j,A;};
struct Aff{u128 a,d;};
static std::vector<u128>P3;

static std::string s128(u128 z){
  if(!z)return "0"; std::string s;
  while(z){s.push_back(char('0'+z%10));z/=10;}
  std::reverse(s.begin(),s.end()); return s;
}
static int v2(u128 z){
  if(!z)return 128; uint64_t lo=(uint64_t)z;
  return lo?__builtin_ctzll(lo):64+__builtin_ctzll((uint64_t)(z>>64));
}
static uint64_t invodd(uint64_t a,int bits){
  uint64_t x=a;
  x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;
  return bits==64?x:x&((UINT64_C(1)<<bits)-1);
}
static u128 pow2u(int e){
  if(e<0||e>=127){std::cerr<<"POW2_RANGE\n";std::exit(30);}
  return u128(1)<<e;
}
static State extend_state(const State&s,int a){
  if(a<1||a>=63||s.A+a+1>=126){std::cerr<<"RANGE_LIMIT\n";std::exit(20);}
  const u128 M=pow2u(s.A+1),P=P3.at(s.j);
  const uint64_t mod=UINT64_C(1)<<a,mask=mod-1;
  const u128 raw=3*s.x+1,B=raw>>1;
  const uint64_t odd=(uint64_t)((3*P)&mask),inv=invodd(odd,a);
  const uint64_t target=UINT64_C(1)<<(a-1);
  const uint64_t diff=(target-(uint64_t)(B&mask))&mask;
  const uint64_t q=(uint64_t)((u128(diff)*inv)&mask);
  State z;
  z.r=s.r+M*u128(q);
  const u128 px=s.x+2*P*u128(q),numer=3*px+1;
  if(v2(numer)!=a){std::cerr<<"VALUATION_FAIL\n";std::exit(21);}
  z.x=numer>>a;z.j=s.j+1;z.A=s.A+a; return z;
}

struct Interval{
  enum Kind{EMPTY,ALL,PREFIX,SUFFIX}kind=EMPTY;
  u128 bound=0;
};
static Interval lower_interval(u128 a,u128 d,u128 N,u128 r){
  // Exact q>=0 integers satisfying a*q+d < N*q+r.
  const i128 slope=i128(a)-i128(N),base=i128(d)-i128(r);
  Interval z;
  if(slope==0){if(base<0)z.kind=Interval::ALL;return z;}
  if(slope>0){
    if(base>=0)return z;
    z.kind=Interval::PREFIX;
    z.bound=u128(-base-1)/u128(slope);
    return z;
  }
  if(base<0){z.kind=Interval::ALL;return z;}
  z.kind=Interval::SUFFIX;
  z.bound=u128(base)/u128(-slope)+1;
  return z;
}

struct Cover{
  bool all=false,hasPre=false,hasSuf=false;
  u128 U=0,L=0;
  uint64_t contributing=0;
};
static bool add_interval(Cover&c,const Interval&z){
  if(c.all)return true;
  if(z.kind==Interval::EMPTY)return false;
  ++c.contributing;
  if(z.kind==Interval::ALL){c.all=true;return true;}
  if(z.kind==Interval::PREFIX){
    if(!c.hasPre||z.bound>c.U){c.hasPre=true;c.U=z.bound;}
  }else if(z.kind==Interval::SUFFIX){
    if(!c.hasSuf||z.bound<c.L){c.hasSuf=true;c.L=z.bound;}
  }
  if(c.hasPre&&c.hasSuf&&c.L<=c.U+1)c.all=true;
  return c.all;
}

struct SearchResult{
  bool closed=false;
  int depth=0;
  uint64_t expanded=0,unique=0;
  uint64_t contributors=0;
  bool usedUnion=false;
  bool hasPre=false,hasSuf=false;
  u128 U=0,L=0;
};

static SearchResult reverse_union_closes(const State&s,int MDEPTH,int EMAX){
  SearchResult out;
  const u128 N=pow2u(s.A+1);
  Cover cover;

  // Direct reached value x(q) is itself an exact lower witness wherever lower.
  add_interval(cover,lower_interval(2*P3.at(s.j),s.x,N,s.r));
  if(cover.all){out.closed=true;return out;}

  std::vector<Aff>cur{{2*P3.at(s.j),s.x}},nxt;
  uint64_t indivAll=0;

  for(int depth=1;depth<=MDEPTH;++depth){
    nxt.clear();
    for(const Aff&z:cur){
      if(z.a%3!=0)continue;
      int parity=-1;
      if(z.d%3==2)parity=0;
      else if(z.d%3==1)parity=1;
      else continue;

      for(int e=parity;e<=EMAX;e+=2){
        ++out.expanded;
        const u128 mul=pow2u(e+1);
        if(z.a>(~u128(0))/mul||z.d>(~u128(0))/mul){
          std::cerr<<"MACRO_OVERFLOW\n";std::exit(31);
        }
        const u128 na=mul*z.a,raw=mul*z.d;
        if(raw==0){std::cerr<<"MACRO_ZERO_RAW\n";std::exit(32);}
        const u128 nd=raw-1;
        if(na%3||nd%3){std::cerr<<"MACRO_DIV_FAIL\n";std::exit(33);}
        Aff w{na/3,nd/3};
        if(w.d==0)continue; // positive donor required for q=0.

        const Interval iv=lower_interval(w.a,w.d,N,s.r);
        if(iv.kind==Interval::ALL)++indivAll;
        const bool beforeAll=cover.all;
        if(add_interval(cover,iv)){
          out.closed=true;out.depth=depth;out.contributors=cover.contributing;
          out.usedUnion=(indivAll==0);
          return out;
        }
        (void)beforeAll;
        nxt.push_back(w);
      }
    }
    std::sort(nxt.begin(),nxt.end(),[](const Aff&a,const Aff&b){
      return a.a<b.a||(a.a==b.a&&a.d<b.d);
    });
    nxt.erase(std::unique(nxt.begin(),nxt.end(),[](const Aff&a,const Aff&b){
      return a.a==b.a&&a.d==b.d;
    }),nxt.end());
    out.unique+=nxt.size();
    cur.swap(nxt);
    if(cur.empty())break;
  }
  out.contributors=cover.contributing;
  out.hasPre=cover.hasPre; out.hasSuf=cover.hasSuf;
  out.U=cover.U; out.L=cover.L;
  return out;
}

static int tail_start(const State&s){
  const u128 P=P3.at(s.j),M=pow2u(s.A+1);
  const int a0=v2(3*s.x+1);
  int a=std::max(1,a0+1);
  for(;;++a){
    if(a>=63||s.A+a+1>=126){std::cerr<<"TAIL_RANGE\n";std::exit(23);}
    const u128 two=pow2u(a);
    if(6*P<two*M&&3*s.x+1+6*P<two*(s.r+M))return a;
  }
}
static long double density(const std::vector<State>&v){
  long double z=0;for(const auto&s:v)z+=std::ldexp((long double)1.0,-s.A);
  return z;
}

int main(int argc,char**argv){
  if(argc!=4){std::cerr<<"usage: reverse_union DEPTH MACRO_DEPTH EMAX\n";return 2;}
  const int DEPTH=std::stoi(argv[1]),MD=std::stoi(argv[2]),EM=std::stoi(argv[3]);
  if(DEPTH<1||DEPTH>22||MD<0||MD>9||EM<0||EM>9)return 2;

  P3.resize(90);P3[0]=1;
  for(int i=1;i<(int)P3.size();++i)P3[i]=P3[i-1]*3;

  std::vector<State>live{{1,1,0,0}};
  uint64_t totalClosed=0,totalUnion=0,totalExpanded=0,totalUnique=0;
  std::cout<<"PARTIAL_COVERAGE_START depth="<<DEPTH
           <<" macro_depth="<<MD<<" emax="<<EM<<"\n";

  for(int depth=1;depth<=DEPTH;++depth){
    std::vector<State>next;
    uint64_t closed=0,unionClosed=0,expanded=0,unique=0,children=0,tails=0;
    uint64_t partialAny=0,partialPre=0,partialSuf=0,partialBoth=0,q0Covered=0;
    int deepest=0;u128 minr=~u128(0);int minA=0;
    for(const State&p:live){
      const int tail=tail_start(p);++tails;
      for(int a=1;a<tail;++a){
        ++children;State z=extend_state(p,a);
        auto sr=reverse_union_closes(z,MD,EM);
        expanded+=sr.expanded;unique+=sr.unique;
        if(sr.closed){
          ++closed;deepest=std::max(deepest,sr.depth);
          if(sr.usedUnion)++unionClosed;
          continue;
        }
        if(sr.contributors>0){
          ++partialAny;
          if(sr.hasPre){++partialPre;++q0Covered;}
          if(sr.hasSuf)++partialSuf;
          if(sr.hasPre&&sr.hasSuf)++partialBoth;
        }
        next.push_back(z);
        if(z.r<minr){minr=z.r;minA=z.A;}
      }
    }
    totalClosed+=closed;totalUnion+=unionClosed;
    totalExpanded+=expanded;totalUnique+=unique;
    std::cout<<"PARTIAL_COVERAGE_LEVEL depth="<<depth
             <<" parents="<<live.size()
             <<" children="<<children<<" tails="<<tails
             <<" closed="<<closed
             <<" union_only_closed="<<unionClosed
             <<" reverse_expanded="<<expanded
             <<" reverse_unique="<<unique
             <<" deepest="<<deepest
             <<" partial_any="<<partialAny
             <<" partial_prefix="<<partialPre
             <<" partial_suffix="<<partialSuf
             <<" partial_both="<<partialBoth
             <<" q0_covered="<<q0Covered
             <<" survivors="<<next.size()
             <<" density="<<(double)density(next);
    if(!next.empty())std::cout<<" min_survivor_r="<<s128(minr)
                              <<" min_survivor_A="<<minA;
    std::cout<<"\n";
    live.swap(next);
  }

  std::cout<<"PARTIAL_COVERAGE_RESULT depth="<<DEPTH
           <<" macro_depth="<<MD<<" emax="<<EM
           <<" survivors="<<live.size()
           <<" density="<<(double)density(live)
           <<" closed="<<totalClosed
           <<" union_only_closed="<<totalUnion
           <<" reverse_expanded="<<totalExpanded
           <<" reverse_unique="<<totalUnique<<"\n";
  if(totalUnion>0)std::cout<<"VERIFIED_NONLINEAR_DONOR_UNION_GAIN\n";
  else std::cout<<"NO_DONOR_UNION_GAIN_AT_TESTED_DEPTH\n";
  std::cout<<"FINAL_GATE=PARTIAL_COVERAGE_D"<<DEPTH
           <<"_M"<<MD<<"_E"<<EM<<"\n";
}
