// Global Collatz cylinders with exact reverse E^e O macro consequences.
//
// State after j accelerated odd steps:
//   n(q) = r + 2^(A+1) q
//   x(q) = x + 2*3^j q, q>=0.
//
// Baseline closure uses direct descent plus the maximal uniform O^s donor.
// Remaining states are searched by reverse macro blocks E^e O:
//   y -> 2^e y -> (2^(e+1)y - 1)/3.
// A macro donor is accepted only when it is uniformly integral, positive, and
// strictly below n(q) for every q>=0.  Failure remains UNKNOWN.
//
// Finite-depth global certificate only; no global Collatz claim is made.

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
struct Aff{u128 a,d;};

static std::vector<u128>P3;

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
static uint64_t invodd(uint64_t a,int bits){
  uint64_t x=a;
  x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;
  if(bits==64)return x;
  return x&((UINT64_C(1)<<bits)-1);
}
static u128 pow2u(int e){
  if(e<0||e>=127){std::cerr<<"POW2_RANGE\n";std::exit(30);}
  return u128(1)<<e;
}

static State extend_state(const State&s,int a){
  if(a<1||a>=63||s.A+a+1>=126){std::cerr<<"RANGE_LIMIT\n";std::exit(20);}
  const u128 M=pow2u(s.A+1);
  const uint64_t mod=UINT64_C(1)<<a,mask=mod-1;
  const u128 P=P3.at(s.j);
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
  if(v2(numer)!=a){std::cerr<<"VALUATION_FAIL\n";std::exit(21);}
  z.x=numer>>a;z.j=s.j+1;z.A=s.A+a;
  return z;
}

struct Interval{
  enum Kind{EMPTY,ALL,PREFIX,SUFFIX}kind=EMPTY;
  u128 bound=0;
};
static Interval lt_interval(i128 slope,i128 base,u128 minq=0){
  Interval z;
  if(slope==0){
    if(base<0){z.kind=Interval::ALL;z.bound=minq;}
    return z;
  }
  if(slope>0){
    if(base>=0)return z;
    u128 U=u128(-base-1)/u128(slope);
    if(U<minq)return z;
    if(minq==0){z.kind=Interval::PREFIX;z.bound=U;}
    return z;
  }
  u128 L=minq,S=u128(-slope);
  if(base>=0)L=std::max(L,u128(base)/S+1);
  if(L==0)z.kind=Interval::ALL;
  else{z.kind=Interval::SUFFIX;z.bound=L;}
  return z;
}
static bool covers_all(const Interval&a,const Interval&b){
  if(a.kind==Interval::ALL||b.kind==Interval::ALL)return true;
  if(a.kind==Interval::PREFIX&&b.kind==Interval::SUFFIX)
    return b.bound<=a.bound+1;
  if(b.kind==Interval::PREFIX&&a.kind==Interval::SUFFIX)
    return a.bound<=b.bound+1;
  return false;
}

struct BaseClass{bool closed=false,partial=false;};

static BaseClass baseline(const State&s){
  const u128 N=pow2u(s.A+1),X=2*P3.at(s.j);
  if(s.r==1&&s.x==1&&X<N)return {true,false};
  const Interval direct=lt_interval(i128(X)-i128(N),
                                    i128(s.x)-i128(s.r));
  Interval deep;
  const int o=std::min(v3(s.x+1),s.j);
  if(o>0){
    const u128 den=P3.at(o),tw=pow2u(o);
    const u128 p0=tw*((s.x+1)/den)-1;
    const u128 pc=pow2u(o+1)*P3.at(s.j-o);
    deep=lt_interval(i128(pc)-i128(N),i128(p0)-i128(s.r),
                     p0==0?1:0);
  }
  const bool c=covers_all(direct,deep);
  return {c,!c&&(direct.kind!=Interval::EMPTY||deep.kind!=Interval::EMPTY)};
}

static bool reverse_eo_closes(const State&s,int MDEPTH,int EMAX,
                              int&usedDepth,int&usedE,uint64_t&expanded){
  if(MDEPTH<=0)return false;
  const u128 N=pow2u(s.A+1);
  std::vector<Aff>cur{{2*P3.at(s.j),s.x}},nxt,uniq;

  for(int depth=1;depth<=MDEPTH;++depth){
    nxt.clear();
    for(const Aff&z:cur){
      if(z.a%3!=0)continue;
      int parity=-1;
      if(z.d%3==2)parity=0;
      else if(z.d%3==1)parity=1;
      else continue;

      for(int e=parity;e<=EMAX;e+=2){
        ++expanded;
        const u128 mul=pow2u(e+1);
        if(z.a>(~u128(0))/mul||z.d>(~u128(0))/mul){
          std::cerr<<"MACRO_OVERFLOW\n";std::exit(31);
        }
        const u128 na=mul*z.a;
        const u128 nd=mul*z.d-1;
        if(na%3||nd%3){std::cerr<<"MACRO_DIV_FAIL\n";std::exit(32);}
        const Aff w{na/3,nd/3};
        if(w.d>0&&w.a<=N&&w.d<s.r){
          usedDepth=depth;usedE=e;return true;
        }
        nxt.push_back(w);
      }
    }
    std::sort(nxt.begin(),nxt.end(),[](const Aff&a,const Aff&b){
      return a.a<b.a||(a.a==b.a&&a.d<b.d);
    });
    nxt.erase(std::unique(nxt.begin(),nxt.end(),[](const Aff&a,const Aff&b){
      return a.a==b.a&&a.d==b.d;
    }),nxt.end());
    cur.swap(nxt);
    if(cur.empty())break;
  }
  return false;
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
  if(argc!=4){
    std::cerr<<"usage: reverse_eo DEPTH MACRO_DEPTH EMAX\n";return 2;
  }
  const int DEPTH=std::stoi(argv[1]);
  const int MD=std::stoi(argv[2]);
  const int EM=std::stoi(argv[3]);
  if(DEPTH<1||DEPTH>22||MD<0||MD>8||EM<0||EM>9)return 2;

  P3.resize(80);P3[0]=1;
  for(int i=1;i<(int)P3.size();++i)P3[i]=P3[i-1]*3;

  std::vector<State>live{{1,1,0,0}};
  uint64_t totalBase=0,totalMacro=0,totalExpanded=0,totalPartial=0;
  std::cout<<"GLOBAL_REVERSE_EO_START depth="<<DEPTH
           <<" macro_depth="<<MD<<" emax="<<EM<<"\n";

  for(int depth=1;depth<=DEPTH;++depth){
    std::vector<State>next;
    uint64_t basec=0,macroc=0,expanded=0,partial=0,children=0,tails=0;
    int deepest=0,maxe=-1;
    u128 minr=~u128(0);int minA=0;

    for(const State&p:live){
      const int tail=tail_start(p);++tails;
      for(int a=1;a<tail;++a){
        ++children;State z=extend_state(p,a);
        BaseClass b=baseline(z);
        if(b.closed){++basec;continue;}
        if(b.partial)++partial;
        int ud=0,ue=-1;uint64_t ex=0;
        if(reverse_eo_closes(z,MD,EM,ud,ue,ex)){
          ++macroc;deepest=std::max(deepest,ud);maxe=std::max(maxe,ue);
          expanded+=ex;continue;
        }
        expanded+=ex;
        next.push_back(z);
        if(z.r<minr){minr=z.r;minA=z.A;}
      }
    }

    totalBase+=basec;totalMacro+=macroc;
    totalExpanded+=expanded;totalPartial+=partial;

    std::cout<<"GLOBAL_REVERSE_EO_LEVEL depth="<<depth
             <<" parents="<<live.size()
             <<" children="<<children
             <<" tails="<<tails
             <<" baseline_closed="<<basec
             <<" macro_closed="<<macroc
             <<" macro_expanded="<<expanded
             <<" partial="<<partial
             <<" deepest_macro="<<deepest
             <<" max_used_e="<<maxe
             <<" survivors="<<next.size()
             <<" density="<<(double)density(next);
    if(!next.empty())std::cout<<" min_survivor_r="<<s128(minr)
                              <<" min_survivor_A="<<minA;
    std::cout<<"\n";
    live.swap(next);
  }

  std::cout<<"GLOBAL_REVERSE_EO_RESULT depth="<<DEPTH
           <<" macro_depth="<<MD
           <<" emax="<<EM
           <<" survivors="<<live.size()
           <<" density="<<(double)density(live)
           <<" baseline_closed="<<totalBase
           <<" macro_closed="<<totalMacro
           <<" macro_expanded="<<totalExpanded
           <<" partial="<<totalPartial<<"\n";
  if(totalPartial==0)std::cout<<"REVERSE_EO_NO_PARTIAL_BASELINE\n";
  std::cout<<"FINAL_GATE=GLOBAL_REVERSE_EO_D"<<DEPTH
           <<"_M"<<MD<<"_E"<<EM<<"\n";
  return 0;
}
