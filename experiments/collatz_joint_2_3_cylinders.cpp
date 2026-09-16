// Exact joint 2-adic / 3-adic Collatz cylinder compiler.
//
// Domain: all odd n > 1, represented initially by n(q)=3+2q, q>=0.
//
// A state carries
//   n(q) = r + N q
//   x(q) = x + X q
// where x is the accelerated odd endpoint after j odd steps.
// Invariants:
//   N = 2^(A+1) 3^k
//   X = 2 3^(j+k)
//
// Forward valuation refinement consumes a binary residue q mod 2^a.
// Consequence refinement consumes a ternary residue q mod 3.  The latter
// makes one additional inverse-O divisibility digit uniform when possible.
//
// Every reported closure is an exact affine inequality on an infinite
// arithmetic progression.  This is a finite-depth global certificate only.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using u128 = unsigned __int128;
using i128 = __int128;

struct State {
  u128 r, x;
  int j, A, k;
};

static std::vector<u128> P3;

static std::string s128(u128 z) {
  if (!z) return "0";
  std::string s;
  while (z) { s.push_back(char('0' + z % 10)); z /= 10; }
  std::reverse(s.begin(), s.end());
  return s;
}

static int v2(u128 z) {
  if (!z) return 128;
  uint64_t lo = (uint64_t)z;
  return lo ? __builtin_ctzll(lo)
            : 64 + __builtin_ctzll((uint64_t)(z >> 64));
}

static int v3(u128 z, int cap=128) {
  int c=0;
  while (c<cap && z%3==0) { z/=3; ++c; }
  return c;
}

static u128 Ncoef(const State& s) {
  if (s.A+1 >= 126) { std::cerr << "N_RANGE\n"; std::exit(20); }
  return (u128(1) << (s.A+1)) * P3.at(s.k);
}

static u128 Xcoef(const State& s) {
  return u128(2) * P3.at(s.j+s.k);
}

static uint64_t invodd64(uint64_t a, int bits) {
  uint64_t x=a;
  x*=2-a*x; x*=2-a*x; x*=2-a*x;
  x*=2-a*x; x*=2-a*x; x*=2-a*x;
  if (bits==64) return x;
  return x & ((UINT64_C(1)<<bits)-1);
}

struct Interval {
  enum Kind { EMPTY, ALL, PREFIX, SUFFIX } kind=EMPTY;
  u128 bound=0;
};

static Interval lt_interval(i128 slope, i128 base) {
  // slope*q + base < 0 for q>=0.
  Interval z;
  if (slope==0) {
    if (base<0) z.kind=Interval::ALL;
    return z;
  }
  if (slope>0) {
    if (base>=0) return z;
    z.kind=Interval::PREFIX;
    z.bound=u128(-base-1)/u128(slope);
    return z;
  }
  const u128 S=u128(-slope);
  if (base<0) { z.kind=Interval::ALL; return z; }
  z.kind=Interval::SUFFIX;
  z.bound=u128(base)/S + 1;
  return z;
}

static bool covers_all(const Interval& a, const Interval& b) {
  if (a.kind==Interval::ALL || b.kind==Interval::ALL) return true;
  if (a.kind==Interval::PREFIX && b.kind==Interval::SUFFIX)
    return b.bound <= a.bound+1;
  if (b.kind==Interval::PREFIX && a.kind==Interval::SUFFIX)
    return a.bound <= b.bound+1;
  return false;
}

struct Classification {
  bool closed=false;
  bool partial=false;
  int uniform_o=0;
  int x_v3=0;
};

static Classification classify(const State& s) {
  const u128 N=Ncoef(s), X=Xcoef(s);
  const Interval direct=lt_interval(i128(X)-i128(N),
                                    i128(s.x)-i128(s.r));

  const int xv=v3(X);
  const int o=std::min(v3(s.x+1),xv);
  Interval deep;
  if (o>0) {
    const u128 den=P3[o];
    const u128 tw=u128(1)<<o;
    if ((s.x+1)%den || X%den) {
      std::cerr<<"O_DIV_FAIL\n"; std::exit(21);
    }
    const u128 p0=tw*((s.x+1)/den)-1;
    const u128 P=tw*(X/den);
    if (p0==0) {
      std::cerr<<"ZERO_DONOR_IN_N_GT_1_DOMAIN\n"; std::exit(22);
    }
    deep=lt_interval(i128(P)-i128(N),
                     i128(p0)-i128(s.r));
  }

  Classification c;
  c.uniform_o=o; c.x_v3=xv;
  c.closed=covers_all(direct,deep);
  c.partial=!c.closed &&
    (direct.kind!=Interval::EMPTY || deep.kind!=Interval::EMPTY);
  return c;
}

static State refine3(const State& s, int e) {
  if (e<0 || e>2) std::exit(23);
  const u128 N=Ncoef(s), X=Xcoef(s);
  State z{s.r+N*u128(e), s.x+X*u128(e), s.j, s.A, s.k+1};
  return z;
}

static State extend_forward(const State& s, int a) {
  if (a<1 || a>=63 || s.A+a+1>=126) {
    std::cerr<<"FORWARD_RANGE\n"; std::exit(24);
  }
  const u128 N=Ncoef(s), X=Xcoef(s);
  const uint64_t mod=UINT64_C(1)<<a, mask=mod-1;
  const u128 raw=3*s.x+1;
  const u128 B=raw>>1;
  const u128 C=(3*X)>>1;
  const uint64_t cc=(uint64_t)(C&mask);
  if (!(cc&1)) { std::cerr<<"FORWARD_COEF_NOT_ODD\n"; std::exit(25); }
  const uint64_t inv=invodd64(cc,a);
  const uint64_t target=UINT64_C(1)<<(a-1);
  const uint64_t diff=(target-(uint64_t)(B&mask))&mask;
  const uint64_t q0=(uint64_t)((u128(diff)*inv)&mask);

  State z;
  z.r=s.r+N*u128(q0);
  const u128 xx=s.x+X*u128(q0);
  const u128 numer=3*xx+1;
  if (v2(numer)!=a) { std::cerr<<"VALUATION_FAIL\n"; std::exit(26); }
  z.x=numer>>a;
  z.j=s.j+1; z.A=s.A+a; z.k=s.k;
  return z;
}

static int forward_tail_start(const State& s) {
  const u128 N=Ncoef(s), X=Xcoef(s);
  const int a0=v2(3*s.x+1);
  int a=std::max(1,a0+1);
  for (;;++a) {
    if (a>=63 || s.A+a+1>=126) {
      std::cerr<<"TAIL_RANGE\n"; std::exit(27);
    }
    const u128 two=u128(1)<<a;
    // For a>a0, q0>=1.  If the inequality holds already at q0=1
    // and the slope is negative, every larger q0 and every family q closes.
    const bool slope=3*X < two*N;
    const bool base=3*s.x+1+3*X < two*(s.r+N);
    if (slope && base) return a;
  }
}

struct RefineStats {
  uint64_t closed=0, partial=0, splits=0, leaves=0;
  int max_k=0, max_o=0;
};

static void consequence_refine(const State& s, int budget,
                               std::vector<State>& out,
                               RefineStats& st) {
  const Classification c=classify(s);
  st.max_o=std::max(st.max_o,c.uniform_o);
  if (c.closed) { ++st.closed; return; }
  if (c.partial) ++st.partial;

  // A deeper O digit can depend on q only when the currently guaranteed
  // divisibility exhausts all powers of 3 in the affine coefficient.
  if (budget>0 && c.uniform_o==c.x_v3) {
    ++st.splits;
    for (int e=0;e<3;++e)
      consequence_refine(refine3(s,e),budget-1,out,st);
    return;
  }
  out.push_back(s);
  ++st.leaves;
  st.max_k=std::max(st.max_k,s.k);
}

static long double density(const std::vector<State>& v) {
  long double z=0;
  for (const auto& s:v)
    z += std::ldexp(std::pow((long double)3.0,-s.k),-s.A);
  return z;
}

int main(int argc,char**argv) {
  if (argc!=3) {
    std::cerr<<"usage: joint_cylinders DEPTH TERNARY_BUDGET\n";
    return 2;
  }
  const int DEPTH=std::stoi(argv[1]);
  const int RB=std::stoi(argv[2]);
  if (DEPTH<1 || DEPTH>22 || RB<0 || RB>8) return 2;

  P3.resize(128);
  P3[0]=1;
  for (int i=1;i<(int)P3.size();++i) {
    if (P3[i-1] > (~u128(0))/3) { P3.resize(i); break; }
    P3[i]=P3[i-1]*3;
  }

  // Exactly all odd positive integers >1.
  std::vector<State> live{{3,3,0,0,0}};
  uint64_t totalChildren=0,totalClosed=0,totalSplits=0,totalPartial=0;
  std::cout<<"JOINT23_START depth="<<DEPTH<<" ternary_budget="<<RB<<"\n";

  for (int depth=1; depth<=DEPTH; ++depth) {
    std::vector<State> next;
    RefineStats rs;
    uint64_t children=0,tails=0;
    u128 minr=~u128(0); int minA=0,minK=0;

    for (const State& p:live) {
      const int tail=forward_tail_start(p);
      ++tails;
      for (int a=1;a<tail;++a) {
        ++children;
        const State z=extend_forward(p,a);
        consequence_refine(z,RB,next,rs);
      }
    }

    for (const auto& s:next) {
      if (s.r<minr) { minr=s.r; minA=s.A; minK=s.k; }
    }

    totalChildren+=children; totalClosed+=rs.closed;
    totalSplits+=rs.splits; totalPartial+=rs.partial;

    std::cout<<"JOINT23_LEVEL depth="<<depth
             <<" parents="<<live.size()
             <<" binary_children="<<children
             <<" infinite_binary_tails="<<tails
             <<" ternary_splits="<<rs.splits
             <<" closed="<<rs.closed
             <<" partial="<<rs.partial
             <<" survivors="<<next.size()
             <<" density="<<(double)density(next)
             <<" max_k="<<rs.max_k
             <<" max_uniform_o="<<rs.max_o;
    if (!next.empty())
      std::cout<<" min_survivor_r="<<s128(minr)
               <<" min_survivor_A="<<minA
               <<" min_survivor_k="<<minK;
    std::cout<<"\n";
    live.swap(next);
  }

  std::cout<<"JOINT23_RESULT depth="<<DEPTH
           <<" ternary_budget="<<RB
           <<" survivors="<<live.size()
           <<" density="<<(double)density(live)
           <<" binary_children="<<totalChildren
           <<" consequence_closed="<<totalClosed
           <<" ternary_splits="<<totalSplits
           <<" partial="<<totalPartial<<"\n";
  std::cout<<"EXACT_ALL_ODD_N_GT_1_PARTITION\n";
  std::cout<<"FINAL_GATE=JOINT_2_3_ADIC_CYLINDER_D"<<DEPTH<<"_R"<<RB<<"\n";
  return 0;
}
