// Global, magnitude-independent valuation-cylinder compiler for the accelerated
// odd Collatz map S(n)=(3n+1)/2^a, a=v2(3n+1).
//
// A prefix of valuations with total A and length j determines one residue
// class n = r + 2^(A+1) q, q>=0, and an affine endpoint
// x = x0 + 2*3^j q.
//
// We classify the entire class by direct descent x<n or by the deterministic
// inverse-odd cone p=(2x-1)/3<n when x==2 mod 3.  If a coefficient is
// favourable (negative affine slope), checking the least representative
// certifies the whole class.  Coefficient-unfavourable children remain whole
// residue classes and are recursively retained.
//
// For every parent, all sufficiently large next valuations are certified
// direct-closed in one infinite-tail inequality, so branching is finite.
//
// This is an exact finite-depth global cylinder certificate, NOT a proof that
// the survivor set is empty at infinite depth.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

using u128 = unsigned __int128;

struct State {
  u128 r;       // least positive odd representative
  u128 x;       // accelerated endpoint for r
  int j;        // odd accelerated steps
  int A;        // total v2 stripped
};

static std::string s128(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}

static int v2_128(u128 x){
  if(!x)return 128;
  uint64_t lo=(uint64_t)x;
  if(lo)return __builtin_ctzll(lo);
  return 64+__builtin_ctzll((uint64_t)(x>>64));
}

static u128 pow3(int j){
  u128 z=1;
  for(int i=0;i<j;++i)z*=3;
  return z;
}

static uint64_t inv_odd_mod_pow2(uint64_t a,int bits){
  // Newton iteration gives inverse modulo 2^64 for odd a.
  uint64_t x=a;
  x*=2-a*x; x*=2-a*x; x*=2-a*x;
  x*=2-a*x; x*=2-a*x; x*=2-a*x;
  if(bits==64)return x;
  uint64_t mask=(UINT64_C(1)<<bits)-1;
  return x&mask;
}

static State extend_state(const State&s,int a){
  if(a<1||a>=63||s.A+a+1>=127){
    std::cerr<<"RANGE_LIMIT a="<<a<<" A="<<s.A<<"\n";
    std::exit(20);
  }
  const u128 M=u128(1)<<(s.A+1);
  const uint64_t mod=UINT64_C(1)<<a;
  const uint64_t mask=mod-1;
  const u128 P=pow3(s.j);
  const u128 raw=3*s.x+1;
  const u128 B=raw>>1;
  const uint64_t odd=(uint64_t)((3*P)&mask); // 3^(j+1)
  const uint64_t inv=inv_odd_mod_pow2(odd,a);
  const uint64_t target=UINT64_C(1)<<(a-1);
  const uint64_t bmod=(uint64_t)(B&mask);
  const uint64_t diff=(target-bmod)&mask;
  const uint64_t q=(uint64_t)((u128(diff)*inv)&mask);

  State z;
  z.r=s.r+M*u128(q);
  const u128 parent_x=s.x+2*P*u128(q);
  const u128 numer=3*parent_x+1;
  if(v2_128(numer)!=a){
    std::cerr<<"VALUATION_CONSTRUCTION_FAIL\n";std::exit(21);
  }
  z.x=numer>>a;
  z.j=s.j+1;
  z.A=s.A+a;

  const u128 Mp=u128(1)<<(z.A+1);
  if(!(z.r>0 && (z.r&1) && z.r<Mp && (z.x&1))){
    std::cerr<<"STATE_INVARIANT_FAIL\n";std::exit(22);
  }
  return z;
}

struct Classify {
  bool direct_actual=false, cone_actual=false;
  bool direct_favourable=false, cone_favourable=false;
  bool uniform_close=false;
  bool mixed=false;
};

static Classify classify(const State&s){
  Classify c;
  const u128 P=pow3(s.j);
  const u128 twoA=u128(1)<<s.A;
  c.direct_actual=s.x<s.r;
  c.direct_favourable=P<twoA;

  if(s.x%3==2){
    const u128 p=(2*s.x-1)/3;
    c.cone_actual=p<s.r;
    c.cone_favourable=(2*pow3(s.j-1))<twoA;
  }
  c.uniform_close=(c.direct_actual&&c.direct_favourable)
               || (c.cone_actual&&c.cone_favourable);

  const bool actual=c.direct_actual||c.cone_actual;
  const bool favourable=c.direct_favourable||c.cone_favourable;
  c.mixed=(actual!=favourable) || (actual&&favourable&&!c.uniform_close);
  // n=1 is the unique base-point exception: its class may have favourable
  // negative slope while the least representative is the solved fixed point.
  if(s.r==1 && s.x==1 && favourable){
    const u128 M=u128(1)<<(s.A+1);
    const u128 x1=s.x+2*P;
    const u128 r1=s.r+M;
    bool q1=(x1<r1) || (x1%3==2 && (2*x1-1)/3<r1);
    if(q1){c.uniform_close=true;c.mixed=false;}
  }
  return c;
}

static int direct_threshold_a(const State&s){
  // first a such that 3^(j+1) < 2^(A+a)
  const u128 P=3*pow3(s.j);
  int a=1;
  while((u128(1)<<(s.A+a))<=P)++a;
  return a;
}

static int tail_start(const State&s){
  // For a beyond this bound q=0 is impossible, the affine slope is negative,
  // and q>=1 is already direct-closed. Hence every larger valuation closes.
  const u128 P=pow3(s.j);
  const u128 M=u128(1)<<(s.A+1);
  const int a0=v2_128(3*s.x+1);
  int a=std::max(a0+1,direct_threshold_a(s));
  for(;;++a){
    if(a>=63){std::cerr<<"TAIL_BOUND_RANGE_FAIL\n";std::exit(23);}
    const u128 lhs=3*s.x+1+6*P;
    const u128 rhs=(u128(1)<<a)*(s.r+M);
    const bool slope=(6*P)<((u128(1)<<a)*M);
    if(slope && lhs<rhs)return a;
  }
}

static long double density(const std::vector<State>& v){
  long double z=0;
  for(auto&s:v)z+=std::ldexp((long double)1.0,-s.A);
  return z;
}

int main(int argc,char**argv){
  int DEPTH=18;
  if(argc==2)DEPTH=std::stoi(argv[1]);
  if(DEPTH<1||DEPTH>28)return 2;

  std::vector<State> live{{1,1,0,0}};
  uint64_t total_explicit=0,total_uniform=0,total_tail=0,total_base=0;
  uint64_t mixed=0;
  std::cout<<"GLOBAL_CYLINDER_START depth="<<DEPTH<<"\n";

  for(int depth=1;depth<=DEPTH;++depth){
    std::vector<State> next;
    uint64_t level_explicit=0,level_uniform=0,level_tail=0,level_mixed=0;
    u128 min_r=~u128(0); int min_A=0; u128 min_x=0;

    for(const auto& parent:live){
      const int tail=tail_start(parent);
      ++level_tail;
      ++total_tail;
      // a>=tail is one certified infinite closed tail. Enumerate only a<tail.
      for(int a=1;a<tail;++a){
        ++level_explicit;++total_explicit;
        State z=extend_state(parent,a);
        Classify c=classify(z);
        if(c.mixed){
          ++level_mixed;++mixed;
          if(level_mixed<=3){
            std::cout<<"GLOBAL_CYLINDER_MIXED depth="<<depth
                     <<" a="<<a<<" r="<<s128(z.r)<<" x="<<s128(z.x)
                     <<" j="<<z.j<<" A="<<z.A
                     <<" direct_actual="<<c.direct_actual
                     <<" cone_actual="<<c.cone_actual
                     <<" direct_favourable="<<c.direct_favourable
                     <<" cone_favourable="<<c.cone_favourable<<"\n";
          }
          continue;
        }
        if(c.uniform_close){
          ++level_uniform;++total_uniform;
          if(z.r==1)++total_base;
        }else{
          // With no mixed state, not closed means both coefficient criteria
          // are unfavourable and the whole infinite residue class survives.
          next.push_back(z);
          if(z.r<min_r){min_r=z.r;min_A=z.A;min_x=z.x;}
        }
      }
    }

    long double rho=density(next);
    int maxA=0,minA=9999;
    for(auto&s:next){maxA=std::max(maxA,s.A);minA=std::min(minA,s.A);}
    if(next.empty())minA=0;
    std::cout<<"GLOBAL_CYLINDER_LEVEL"
             <<" depth="<<depth
             <<" parents="<<live.size()
             <<" explicit_children="<<level_explicit
             <<" infinite_closed_tails="<<level_tail
             <<" uniform_closed="<<level_uniform
             <<" mixed="<<level_mixed
             <<" survivors="<<next.size()
             <<" survivor_density="<<(double)rho
             <<" minA="<<minA<<" maxA="<<maxA;
    if(!next.empty()){
      std::cout<<" min_survivor_r="<<s128(min_r)
               <<" min_survivor_x="<<s128(min_x)
               <<" min_survivor_A="<<min_A;
    }
    std::cout<<"\n";

    if(level_mixed){
      std::cerr<<"MIXED_RESIDUE_CLASS_OBSTRUCTION\n";
      return 12;
    }
    live.swap(next);
  }

  std::cout<<"GLOBAL_CYLINDER_RESULT"
           <<" depth="<<DEPTH
           <<" survivors="<<live.size()
           <<" survivor_density="<<(double)density(live)
           <<" explicit_children="<<total_explicit
           <<" uniform_closed="<<total_uniform
           <<" infinite_closed_tails="<<total_tail
           <<" base_one_classes="<<total_base
           <<" mixed="<<mixed<<"\n";
  std::cout<<"NO_FINITE_OFFSET_MIXED_CLASSES_THROUGH_DEPTH_"<<DEPTH<<"\n";
  std::cout<<"FINAL_GATE=GLOBAL_VALUATION_CYLINDER_QUOTIENT_DEPTH_"<<DEPTH<<"\n";
  return 0;
}
