// Exact global Collatz cylinders combining one ternary consequence split
// with finite reverse E^e O macro search.
//
// Domain starts at all odd n>1: n(q)=3+2q.
// State:
//   n(q)=r + 2^(A+1) 3^k q
//   x(q)=x + 2 3^(j+k) q.
//
// Binary refinement advances the accelerated odd orbit exactly.
// A ternary split q=3q'+e is applied when one additional inverse-O digit is
// not uniform but becomes uniform after residue refinement.
// Remaining exact cylinders are searched by reverse E^e O words.
//
// Every closure is a strict lower witness on an infinite arithmetic family.
// Finite depth/budget only; survivors remain UNKNOWN.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

struct State{u128 r,x;int j,A,k;};
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
  int c=0;while(c<cap&&z%3==0){z/=3;++c;}return c;
}
static u128 pow2u(int e){
  if(e<0||e>=126){std::cerr<<"POW2_RANGE\n";std::exit(30);}
  return u128(1)<<e;
}
static uint64_t invodd(uint64_t a,int bits){
  uint64_t x=a;
  x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;
  return bits==64?x:x&((UINT64_C(1)<<bits)-1);
}
static u128 Ncoef(const State&s){return pow2u(s.A+1)*P3.at(s.k);}
static u128 Xcoef(const State&s){return u128(2)*P3.at(s.j+s.k);}

struct Interval{enum Kind{EMPTY,ALL,PREFIX,SUFFIX}kind=EMPTY;u128 bound=0;};
static Interval lt_interval(i128 slope,i128 base){
  Interval z;
  if(slope==0){if(base<0)z.kind=Interval::ALL;return z;}
  if(slope>0){
    if(base>=0)return z;
    z.kind=Interval::PREFIX;z.bound=u128(-base-1)/u128(slope);return z;
  }
  if(base<0){z.kind=Interval::ALL;return z;}
  z.kind=Interval::SUFFIX;z.bound=u128(base)/u128(-slope)+1;return z;
}
static bool covers_all(const Interval&a,const Interval&b){
  if(a.kind==Interval::ALL||b.kind==Interval::ALL)return true;
  if(a.kind==Interval::PREFIX&&b.kind==Interval::SUFFIX)return b.bound<=a.bound+1;
  if(b.kind==Interval::PREFIX&&a.kind==Interval::SUFFIX)return a.bound<=b.bound+1;
  return false;
}

struct BaseClass{bool closed=false,partial=false;int uniform_o=0,xv3=0;};
static BaseClass baseline(const State&s){
  const u128 N=Ncoef(s),X=Xcoef(s);
  const Interval direct=lt_interval(i128(X)-i128(N),i128(s.x)-i128(s.r));
  const int xv=v3(X);
  const int o=std::min(v3(s.x+1),xv);
  Interval deep;
  if(o>0){
    const u128 den=P3.at(o),tw=pow2u(o);
    if((s.x+1)%den||X%den){std::cerr<<"BASE_DIV_FAIL\n";std::exit(31);}
    const u128 p0=tw*((s.x+1)/den)-1;
    const u128 pc=tw*(X/den);
    if(p0>0)deep=lt_interval(i128(pc)-i128(N),i128(p0)-i128(s.r));
  }
  const bool c=covers_all(direct,deep);
  return {c,!c&&(direct.kind!=Interval::EMPTY||deep.kind!=Interval::EMPTY),o,xv};
}

static State refine3(const State&s,int e){
  const u128 N=Ncoef(s),X=Xcoef(s);
  return {s.r+N*u128(e),s.x+X*u128(e),s.j,s.A,s.k+1};
}

static State extend_state(const State&s,int a){
  if(a<1||a>=63||s.A+a+1>=125){std::cerr<<"FORWARD_RANGE\n";std::exit(32);}
  const u128 N=Ncoef(s),X=Xcoef(s);
  const uint64_t mod=UINT64_C(1)<<a,mask=mod-1;
  const u128 raw=3*s.x+1,B=raw>>1,C=(3*X)>>1;
  const uint64_t cc=(uint64_t)(C&mask);
  if(!(cc&1)){std::cerr<<"FORWARD_COEF_NOT_ODD\n";std::exit(33);}
  const uint64_t inv=invodd(cc,a),target=UINT64_C(1)<<(a-1);
  const uint64_t diff=(target-(uint64_t)(B&mask))&mask;
  const uint64_t q0=(uint64_t)((u128(diff)*inv)&mask);
  State z;
  z.r=s.r+N*u128(q0);
  const u128 xx=s.x+X*u128(q0),numer=3*xx+1;
  if(v2(numer)!=a){std::cerr<<"VALUATION_FAIL\n";std::exit(34);}
  z.x=numer>>a;z.j=s.j+1;z.A=s.A+a;z.k=s.k;return z;
}

static int tail_start(const State&s){
  const u128 N=Ncoef(s),X=Xcoef(s);
  const int a0=v2(3*s.x+1);
  int a=std::max(1,a0+1);
  for(;;++a){
    if(a>=63||s.A+a+1>=125){std::cerr<<"TAIL_RANGE\n";std::exit(35);}
    const u128 two=pow2u(a);
    if(3*X<two*N && 3*s.x+1+3*X<two*(s.r+N))return a;
  }
}

struct MacroResult{bool closed=false;int depth=0;uint64_t expanded=0;};
static MacroResult macro_closes(const State&s,int MD,int EM){
  MacroResult out;
  if(MD<=0)return out;
  const u128 N=Ncoef(s);
  std::vector<Aff>cur{{Xcoef(s),s.x}},nxt;
  for(int depth=1;depth<=MD;++depth){
    nxt.clear();
    for(const Aff&z:cur){
      if(z.a%3!=0)continue;
      int parity=-1;
      if(z.d%3==2)parity=0;
      else if(z.d%3==1)parity=1;
      else continue;
      for(int e=parity;e<=EM;e+=2){
        ++out.expanded;
        const u128 mul=pow2u(e+1);
        if(z.a>(~u128(0))/mul||z.d>(~u128(0))/mul){
          std::cerr<<"MACRO_OVERFLOW\n";std::exit(36);
        }
        const u128 na=mul*z.a,raw=mul*z.d;
        if(raw==0){std::cerr<<"MACRO_ZERO\n";std::exit(37);}
        const u128 nd=raw-1;
        if(na%3||nd%3){std::cerr<<"MACRO_DIV_FAIL\n";std::exit(38);}
        Aff w{na/3,nd/3};
        if(w.d>0){
          const auto iv=lt_interval(i128(w.a)-i128(N),i128(w.d)-i128(s.r));
          if(iv.kind==Interval::ALL){out.closed=true;out.depth=depth;return out;}
          nxt.push_back(w);
        }
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
  return out;
}

struct Stats{
  uint64_t ternary_splits=0,base_closed=0,macro_closed=0,partial=0,expanded=0;
  int deepest=0,maxk=0,maxo=0;
};

static void classify_refined(const State&s,int RB,int MD,int EM,
                             std::vector<State>&out,Stats&st){
  const BaseClass b=baseline(s);
  st.maxo=std::max(st.maxo,b.uniform_o);
  if(b.closed){++st.base_closed;return;}
  if(b.partial)++st.partial;

  auto mr=macro_closes(s,MD,EM);
  st.expanded+=mr.expanded;
  if(mr.closed){
    ++st.macro_closed;st.deepest=std::max(st.deepest,mr.depth);return;
  }

  // Adaptive consequence refinement: when all currently uniform reverse
  // consequences fail, split the parameter modulo 3 and restart the exact
  // closure search independently on each subcylinder.  This can unlock
  // reverse-O integrality after a macro path has exhausted the current
  // 3-adic coefficient.  All three children are retained/proved, so the
  // partition is exact.
  if(RB>0){
    ++st.ternary_splits;
    for(int e=0;e<3;++e)classify_refined(refine3(s,e),RB-1,MD,EM,out,st);
    return;
  }

  st.maxk=std::max(st.maxk,s.k);
  out.push_back(s);
}

static long double density(const std::vector<State>&v){
  long double z=0;
  for(const auto&s:v)z+=std::ldexp(std::pow((long double)3.0,-s.k),-s.A);
  return z;
}

int main(int argc,char**argv){
  if(argc!=5){std::cerr<<"usage: joint_reverse DEPTH RB MD EM\n";return 2;}
  const int DEPTH=std::stoi(argv[1]),RB=std::stoi(argv[2]);
  const int MD=std::stoi(argv[3]),EM=std::stoi(argv[4]);
  if(DEPTH<1||DEPTH>21||RB<0||RB>3||MD<0||MD>8||EM<0||EM>9)return 2;

  P3.resize(100);P3[0]=1;
  for(int i=1;i<(int)P3.size();++i)P3[i]=P3[i-1]*3;

  std::vector<State>live{{3,3,0,0,0}};
  uint64_t totalBase=0,totalMacro=0,totalSplit=0,totalExpanded=0,totalPartial=0;
  std::cout<<"ADAPTIVE_REVERSE_START depth="<<DEPTH<<" rb="<<RB
           <<" macro_depth="<<MD<<" emax="<<EM<<"\n";

  for(int depth=1;depth<=DEPTH;++depth){
    std::vector<State>next;Stats st;
    uint64_t children=0,tails=0;u128 minr=~u128(0);int minA=0,minK=0;
    for(const State&p:live){
      const int tail=tail_start(p);++tails;
      for(int a=1;a<tail;++a){
        ++children;
        classify_refined(extend_state(p,a),RB,MD,EM,next,st);
      }
    }
    for(const auto&s:next)if(s.r<minr){minr=s.r;minA=s.A;minK=s.k;}
    totalBase+=st.base_closed;totalMacro+=st.macro_closed;
    totalSplit+=st.ternary_splits;totalExpanded+=st.expanded;totalPartial+=st.partial;
    std::cout<<"ADAPTIVE_REVERSE_LEVEL depth="<<depth
             <<" parents="<<live.size()<<" children="<<children<<" tails="<<tails
             <<" ternary_splits="<<st.ternary_splits
             <<" base_closed="<<st.base_closed
             <<" macro_closed="<<st.macro_closed
             <<" macro_expanded="<<st.expanded
             <<" deepest_macro="<<st.deepest
             <<" partial="<<st.partial
             <<" survivors="<<next.size()
             <<" density="<<(double)density(next)
             <<" max_k="<<st.maxk<<" max_o="<<st.maxo;
    if(!next.empty())std::cout<<" min_survivor_r="<<s128(minr)
                              <<" min_survivor_A="<<minA
                              <<" min_survivor_k="<<minK;
    std::cout<<"\n";
    live.swap(next);
  }
  std::cout<<"ADAPTIVE_REVERSE_RESULT depth="<<DEPTH<<" rb="<<RB
           <<" macro_depth="<<MD<<" emax="<<EM
           <<" survivors="<<live.size()<<" density="<<(double)density(live)
           <<" base_closed="<<totalBase<<" macro_closed="<<totalMacro
           <<" ternary_splits="<<totalSplit<<" macro_expanded="<<totalExpanded
           <<" partial="<<totalPartial<<"\n";
  std::cout<<"FINAL_GATE=ADAPTIVE_REVERSE_D"<<DEPTH<<"_R"<<RB
           <<"_M"<<MD<<"_E"<<EM<<"\n";
}
