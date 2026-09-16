// Exact compressed canonical R=2 Collatz consequence compiler.
//
// Empirical structural hypothesis under test:
//   * while every forward valuation is in {1,2}, the ternary survivor
//     decoration is the universal open-core decoration at the current depth;
//   * at the first forward valuation >=3, that decoration freezes forever.
//
// We compute the universal open-core ternary mass m_j exactly from ONE
// representative all-a=1 path, then run only the unrefined k=0 forward tree.
// A state whose initial low-valuation prefix has length ell contributes
//
//     2^(-A) * m_ell.
//
// Through VALIDATE_DEPTH we also construct the full canonical R=2 cylinder
// forest independently and require exact rational equality.  Beyond that,
// the compressed run is a prospective consequence of the validated
// structural law, not yet a universal proof.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
#include <string>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

struct State {
  u128 r,x;
  int j,A,k;
  int lowPrefix;
  bool lowOnly;
};
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
static u128 Ncoef(const State&s){
  if(s.A+1>=126){std::cerr<<"N_RANGE\n";std::exit(20);}
  return (u128(1)<<(s.A+1))*P3.at(s.k);
}
static u128 Xcoef(const State&s){return u128(2)*P3.at(s.j+s.k);}
static uint64_t invodd(uint64_t a,int bits){
  uint64_t x=a;
  x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;
  if(bits==64)return x;
  return x&((UINT64_C(1)<<bits)-1);
}

struct Interval{
  enum Kind{EMPTY,ALL,PREFIX,SUFFIX}kind=EMPTY;u128 bound=0;
};
static Interval lt_interval(i128 slope,i128 base){
  Interval z;
  if(slope==0){if(base<0)z.kind=Interval::ALL;return z;}
  if(slope>0){
    if(base>=0)return z;
    z.kind=Interval::PREFIX;z.bound=u128(-base-1)/u128(slope);return z;
  }
  const u128 S=u128(-slope);
  if(base<0){z.kind=Interval::ALL;return z;}
  z.kind=Interval::SUFFIX;z.bound=u128(base)/S+1;return z;
}
static bool covers_all(const Interval&a,const Interval&b){
  if(a.kind==Interval::ALL||b.kind==Interval::ALL)return true;
  if(a.kind==Interval::PREFIX&&b.kind==Interval::SUFFIX)return b.bound<=a.bound+1;
  if(b.kind==Interval::PREFIX&&a.kind==Interval::SUFFIX)return a.bound<=b.bound+1;
  return false;
}
static bool classify_closed(const State&s){
  const u128 N=Ncoef(s),X=Xcoef(s);
  const Interval direct=lt_interval(i128(X)-i128(N),i128(s.x)-i128(s.r));
  const int o=std::min(v3(s.x+1),v3(X));
  Interval deep;
  if(o>0){
    const u128 den=P3[o],tw=u128(1)<<o;
    const u128 p0=tw*((s.x+1)/den)-1;
    const u128 P=tw*(X/den);
    if(p0!=0)deep=lt_interval(i128(P)-i128(N),i128(p0)-i128(s.r));
  }
  return covers_all(direct,deep);
}

struct RevAff{u128 a,d;};
static bool reverse_closed(const State&s){
  const u128 N=Ncoef(s);
  RevAff z{Xcoef(s),s.x};
  for(int depth=1;depth<=s.j+s.k;++depth){
    if(z.a%3!=0)break;
    int b=0;
    if(z.d%3==2)b=1;
    else if(z.d%3==1)b=2;
    else break;
    z={(u128(1)<<b)*z.a/3,((u128(1)<<b)*z.d-1)/3};
    if(z.d>0&&z.a<=N&&z.d<s.r)return true;
  }
  return false;
}
static int reverse_length(const State&s,int&sumB){
  RevAff z{Xcoef(s),s.x};sumB=0;int L=0;
  for(int depth=1;depth<=s.j+s.k;++depth){
    if(z.a%3!=0)break;
    int b=0;
    if(z.d%3==2)b=1;
    else if(z.d%3==1)b=2;
    else break;
    z={(u128(1)<<b)*z.a/3,((u128(1)<<b)*z.d-1)/3};
    ++L;sumB+=b;
  }
  return L;
}

static State refine3(const State&s,int e){
  const u128 N=Ncoef(s),X=Xcoef(s);
  return {s.r+N*u128(e),s.x+X*u128(e),s.j,s.A,s.k+1,
          s.lowPrefix,s.lowOnly};
}
static State extend_forward(const State&s,int a){
  if(a<1||a>=63||s.A+a+1>=126){std::cerr<<"FORWARD_RANGE\n";std::exit(21);}
  const u128 N=Ncoef(s),X=Xcoef(s);
  const uint64_t mod=UINT64_C(1)<<a,mask=mod-1;
  const u128 B=(3*s.x+1)>>1,C=(3*X)>>1;
  const uint64_t q0=(uint64_t)((u128(
      ((UINT64_C(1)<<(a-1))-(uint64_t)(B&mask))&mask)
      *invodd((uint64_t)(C&mask),a))&mask);
  const u128 xx=s.x+X*u128(q0),numer=3*xx+1;
  if(v2(numer)!=a){std::cerr<<"VALUATION_FAIL\n";std::exit(22);}
  const bool low=s.lowOnly&&a<=2;
  return {s.r+N*u128(q0),numer>>a,s.j+1,s.A+a,s.k,
          low?s.j+1:s.lowPrefix,low};
}
static int tail_start(const State&s){
  const u128 N=Ncoef(s),X=Xcoef(s);
  int a=std::max(1,v2(3*s.x+1)+1);
  for(;;++a){
    if(a>=63||s.A+a+1>=126){std::cerr<<"TAIL_RANGE\n";std::exit(23);}
    const u128 two=u128(1)<<a;
    if(3*X<two*N&&3*s.x+1+3*X<two*(s.r+N))return a;
  }
}

static void consequence_r2(const State&s,int budget,std::vector<State>&out){
  if(classify_closed(s)||reverse_closed(s))return;
  if(budget>0){
    std::vector<State>trial;
    for(int e=0;e<3;++e)consequence_r2(refine3(s,e),budget-1,trial);
    int K=s.k;
    for(const auto&z:trial)K=std::max(K,z.k);
    u128 sm=0;
    for(const auto&z:trial)sm+=P3.at(K-z.k);
    const u128 pm=P3.at(K-s.k);
    if(sm<pm){out.insert(out.end(),trial.begin(),trial.end());return;}
  }
  out.push_back(s);
}

struct Mass { u128 num; int K=0; };

static long double ld128(u128 z){
  return (long double)(uint64_t)z
       + std::ldexp((long double)(uint64_t)(z>>64),64);
}
static u128 checked_mul(u128 a,u128 b){
  const u128 M=~u128(0);
  if(b && a>M/b){std::cerr<<"EXACT_MASS_OVERFLOW\n";std::exit(24);}
  return a*b;
}
static u128 checked_add(u128 a,u128 b){
  const u128 M=~u128(0);
  if(a>M-b){std::cerr<<"EXACT_MASS_OVERFLOW\n";std::exit(24);}
  return a+b;
}

static Mass ternary_mass(const std::vector<State>&v){
  int K=0;for(const auto&s:v)K=std::max(K,s.k);
  u128 n=0;
  for(const auto&s:v)n=checked_add(n,P3.at(K-s.k));
  return {n,K};
}
static long double mass_ld(const Mass&m){
  long double n=ld128(m.num);
  for(int i=0;i<m.K;++i)n/=3.0L;
  return n;
}

static u128 scaled_brute(const std::vector<State>&v,int Amax,int Kmax){
  u128 n=0;
  for(const auto&s:v){
    const int da=Amax-s.A;
    if(da<0||da>=128){std::cerr<<"SCALE_A_RANGE\n";std::exit(25);}
    u128 term=u128(1)<<da;
    term=checked_mul(term,P3.at(Kmax-s.k));
    n=checked_add(n,term);
  }
  return n;
}
static u128 scaled_compressed(const std::vector<State>&v,
                              const std::vector<Mass>&m,
                              int Amax,int Kmax){
  u128 n=0;
  for(const auto&s:v){
    const Mass& q=m.at(s.lowPrefix);
    const int da=Amax-s.A;
    if(da<0||da>=128){std::cerr<<"SCALE_A_RANGE\n";std::exit(25);}
    u128 term=checked_mul(q.num,u128(1)<<da);
    term=checked_mul(term,P3.at(Kmax-q.K));
    n=checked_add(n,term);
  }
  return n;
}
static long double scaled_ld(u128 n,int Amax,int Kmax){
  long double x=ld128(n);
  x=std::ldexp(x,-Amax);
  for(int i=0;i<Kmax;++i)x/=3.0L;
  return x;
}

int main(int argc,char**argv){
  if(argc<2||argc>3){std::cerr<<"usage: compressed DEPTH [VALIDATE=12]\n";return 2;}
  const int DEPTH=std::stoi(argv[1]);
  const int VALIDATE=argc==3?std::stoi(argv[2]):12;
  if(DEPTH<1||DEPTH>22||VALIDATE<0||VALIDATE>12||VALIDATE>DEPTH)return 2;

  P3.resize(128);P3[0]=1;
  for(int i=1;i<(int)P3.size();++i)P3[i]=P3[i-1]*3;

  std::vector<Mass> openMass(DEPTH+1);
  openMass[0]={u128(1),0};
  std::vector<State> universal{{3,3,0,0,0,0,true}};

  std::vector<State> base{{3,3,0,0,0,0,true}};
  std::vector<State> brute{{3,3,0,0,0,0,true}};

  std::cout<<"COMPRESSED_CANONICAL_R2_START depth="<<DEPTH
           <<" validate="<<VALIDATE<<"\n";

  for(int depth=1;depth<=DEPTH;++depth){
    // Universal open-core ternary decoration: any all-{1,2} word is
    // isomorphic; choose all a=1 as the representative.
    std::vector<State> unext;
    for(const auto&p:universal)
      consequence_r2(extend_forward(p,1),2,unext);
    universal.swap(unext);
    openMass[depth]=ternary_mass(universal);

    // Exact unrefined canonical forward survivor tree.
    std::vector<State> next;
    uint64_t full=0,stopped=0,badDual=0;
    std::map<int,uint64_t> prefixCount;
    for(const auto&p:base){
      const int tail=tail_start(p);
      for(int a=1;a<tail;++a){
        State z=extend_forward(p,a);
        if(classify_closed(z)||reverse_closed(z))continue;
        int C=0;const int L=reverse_length(z,C);
        const bool isFull=L==z.j;
        if(isFull)++full;else ++stopped;
        if(isFull!=z.lowOnly || (isFull&&C!=z.A))++badDual;
        ++prefixCount[z.lowPrefix];
        next.push_back(z);
      }
    }
    if(badDual){
      std::cerr<<"LOW12_DUALITY_FAIL depth="<<depth<<" count="<<badDual<<"\n";
      return 60;
    }
    base.swap(next);

    int Amax=0;
    for(const auto&s:base)Amax=std::max(Amax,s.A);
    const int Kmax=openMass[depth].K;
    const u128 comp=scaled_compressed(base,openMass,Amax,Kmax);

    bool exactMatch=true;
    uint64_t bruteLeaves=0;
    if(depth<=VALIDATE){
      std::vector<State> bn;
      for(const auto&p:brute){
        const int tail=tail_start(p);
        for(int a=1;a<tail;++a)
          consequence_r2(extend_forward(p,a),2,bn);
      }
      brute.swap(bn);
      bruteLeaves=brute.size();
      int bA=0,bK=0;
      for(const auto&s:brute){bA=std::max(bA,s.A);bK=std::max(bK,s.k);}
      const int CA=std::max(Amax,bA),CK=std::max(Kmax,bK);
      u128 cn=comp;
      const int da=CA-Amax;
      if(da<0||da>=128){std::cerr<<"COMPARE_A_RANGE\n";return 62;}
      cn=checked_mul(cn,u128(1)<<da);
      cn=checked_mul(cn,P3.at(CK-Kmax));
      const u128 bnExact=scaled_brute(brute,CA,CK);
      exactMatch=(cn==bnExact);
      if(!exactMatch){
        std::cerr<<"COMPRESSED_EXACT_MISMATCH depth="<<depth<<"\n";
        return 61;
      }
    } else {
      std::vector<State>().swap(brute);
    }

    std::cout<<"COMPRESSED_CANONICAL_R2_LEVEL depth="<<depth
             <<" base_states="<<base.size()
             <<" full_reverse="<<full
             <<" stopped="<<stopped
             <<" open_mass_num="<<s128(openMass[depth].num)
             <<" open_mass_k="<<openMass[depth].K
             <<" open_mass="<<(double)mass_ld(openMass[depth])
             <<" compressed_density="<<(double)scaled_ld(comp,Amax,Kmax)
             <<" brute_leaves="<<bruteLeaves
             <<" exact_match="<<(exactMatch?1:0)
             <<" prefix_classes="<<prefixCount.size();
    for(const auto&kv:prefixCount)
      std::cout<<" p"<<kv.first<<"="<<kv.second;
    std::cout<<"\n";
  }

  std::cout<<"VERIFIED_COMPRESSED_CANONICAL_R2";
  if(VALIDATE>0)std::cout<<"_THROUGH_D"<<VALIDATE;
  std::cout<<"\n";
  std::cout<<"FINAL_GATE=COMPRESSED_CANONICAL_R2_D"<<DEPTH
           <<"_V"<<VALIDATE<<"\n";
  return 0;
}
