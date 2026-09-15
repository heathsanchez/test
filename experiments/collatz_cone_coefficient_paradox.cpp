// Exact exhaustive test of whether the deterministic cone kills
// coefficient-paradoxical odd checkpoints before they can obstruct induction.
//
// For the accelerated odd map U(x)=(3x+1)/2^a, a=v2(3x+1), after j odd
// transitions with A=sum a we have an affine leading multiplier 3^j/2^A.
// We ask whether, BEFORE any exact cone/direct closure relative to the start n,
// a coefficient-favourable checkpoint can nevertheless fail both exact tests.
//
// This is a falsification experiment, not a global proof.

#include <boost/multiprecision/cpp_int.hpp>
#include <boost/multiprecision/integer.hpp>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <vector>

using u128 = unsigned __int128;
using Big = boost::multiprecision::cpp_int;

static int v2_128(u128 x) {
  if (!x) return 128;
  uint64_t lo = (uint64_t)x;
  if (lo) return __builtin_ctzll(lo);
  return 64 + __builtin_ctzll((uint64_t)(x >> 64));
}

static bool cone(u128 x, u128 n) {
  return x % 3 == 2 && 2*x < 3*n + 1;
}

struct Thresholds {
  std::vector<int> directA;
  std::vector<int> coneA;
};

static Thresholds thresholds(int J) {
  Thresholds t;
  t.directA.resize(J+1);
  t.coneA.resize(J+1);
  Big p3 = 1;
  for (int j=1;j<=J;++j) {
    p3 *= 3;
    // Smallest A with 2^A > 3^j.
    int d = boost::multiprecision::msb(p3) + 1;
    t.directA[j] = d;
    // Smallest A with 3*2^A > 2*3^j.
    int c = std::max(0,d-2);
    while ( (Big(3) << c) <= 2*p3 ) ++c;
    t.coneA[j] = c;
  }
  return t;
}

struct Stats {
  uint64_t odd=0, t0=0, closed=0;
  uint64_t direct_close=0, cone_close=0;
  uint64_t preclose_coeff_favourable=0;
  uint64_t paradox=0;
  int max_j=0, max_A=0;
  uint64_t max_j_seed=0;
  uint64_t first_paradox_seed=0;
  int first_paradox_j=0, first_paradox_A=0;
  u128 first_paradox_x=0;
};

static std::string s128(u128 x) {
  if (!x) return "0";
  std::string s;
  while(x){ s.push_back(char('0'+x%10)); x/=10; }
  std::reverse(s.begin(),s.end());
  return s;
}

static Stats scan_shell(int K, int JMAX, const Thresholds& th) {
  Stats st;
  const uint64_t lo = UINT64_C(1) << K;
  const uint64_t hi = UINT64_C(1) << (K+1);
  for (uint64_t nn=lo+1; nn<hi; nn+=2) {
    ++st.odd;
    const u128 n=nn;
    if (n%3==2) { ++st.t0; ++st.closed; ++st.cone_close; continue; }
    u128 x=n;
    int A=0;
    bool done=false;
    for (int j=1;j<=JMAX;++j) {
      if (x > (std::numeric_limits<u128>::max()-1)/3) {
        std::cerr<<"U128_OVERFLOW K="<<K<<" n="<<nn<<"\n";
        std::exit(8);
      }
      u128 z=3*x+1;
      int a=v2_128(z);
      x=z>>a;
      A+=a;

      bool d = x<n;
      bool c = cone(x,n);
      bool df = A>=th.directA[j];
      bool cf = (x%3==2 && A>=th.coneA[j]);
      bool favourable = df || cf;

      if (!d && !c && favourable) {
        ++st.paradox;
        if (!st.first_paradox_seed) {
          st.first_paradox_seed=nn;
          st.first_paradox_j=j;
          st.first_paradox_A=A;
          st.first_paradox_x=x;
        }
      }
      if (favourable) ++st.preclose_coeff_favourable;

      if (d || c) {
        ++st.closed;
        if(d) ++st.direct_close; else ++st.cone_close;
        if(j>st.max_j){st.max_j=j;st.max_j_seed=nn;}
        st.max_A=std::max(st.max_A,A);
        done=true;
        break;
      }
    }
    if(!done){
      std::cerr<<"UNCLOSED_WITHIN_JMAX K="<<K<<" n="<<nn<<" JMAX="<<JMAX<<"\n";
      std::exit(9);
    }
  }
  return st;
}

// Positive control: deliberately ignore earlier cone closure and verify that
// ordinary coefficient-paradoxical odd checkpoints really do exist.
static void positive_control(const Thresholds& th) {
  uint64_t found=0, first_n=0; int first_j=0,first_A=0; u128 first_x=0;
  for(uint64_t nn=3;nn<(UINT64_C(1)<<20);nn+=2){
    u128 n=nn,x=n; int A=0;
    for(int j=1;j<=256;++j){
      u128 z=3*x+1; int a=v2_128(z); x=z>>a; A+=a;
      if(A>=th.directA[j] && x>=n){
        ++found;
        if(!first_n){first_n=nn;first_j=j;first_A=A;first_x=x;}
        break;
      }
    }
  }
  if(!found){ std::cerr<<"POSITIVE_CONTROL_FAILED\n"; std::exit(10); }
  std::cout<<"COEFFICIENT_PARADOX_POSITIVE_CONTROL"
           <<" found_seeds="<<found
           <<" first_n="<<first_n
           <<" first_j="<<first_j
           <<" first_A="<<first_A
           <<" first_x="<<s128(first_x)<<"\n";
  std::cout<<"VERIFIED_PARADOX_TEST_SENSITIVITY\n";
}

int main(int argc,char**argv){
  if(argc!=2){std::cerr<<"usage: cone_coeff K\n";return 2;}
  int K=std::stoi(argv[1]);
  if(K<10||K>26)return 2;
  constexpr int JMAX=2048;
  auto th=thresholds(JMAX);
  positive_control(th);
  auto s=scan_shell(K,JMAX,th);
  std::cout<<"PRE_CLOSURE_COEFFICIENT_RESULT"
           <<" K="<<K<<" odd="<<s.odd<<" t0="<<s.t0
           <<" closed="<<s.closed<<" direct_close="<<s.direct_close
           <<" cone_close="<<s.cone_close
           <<" coefficient_favourable_checkpoints="<<s.preclose_coeff_favourable
           <<" paradox="<<s.paradox
           <<" max_j="<<s.max_j<<" max_j_seed="<<s.max_j_seed
           <<" max_A="<<s.max_A;
  if(s.paradox){
    std::cout<<" first_paradox_seed="<<s.first_paradox_seed
             <<" first_paradox_j="<<s.first_paradox_j
             <<" first_paradox_A="<<s.first_paradox_A
             <<" first_paradox_x="<<s128(s.first_paradox_x);
  }
  std::cout<<"\n";
  if(s.closed!=s.odd){std::cerr<<"ACCOUNTING_FAIL\n";return 11;}
  if(s.paradox){std::cerr<<"PRE_CLOSURE_COEFFICIENT_PARADOX_FOUND\n";return 12;}
  std::cout<<"NO_PRE_CLOSURE_COEFFICIENT_PARADOX\n";
  std::cout<<"FINAL_GATE=CONE_KILLS_COEFFICIENT_PARADOX_K"<<K<<"\n";
  return 0;
}
