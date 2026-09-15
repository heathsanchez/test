// Sparse exact Collatz transfer-prefix automaton.
//
// Fixed valuation slice n = 2^K m - 1, m odd.
// At prefix depth p, write m = r + 2^p A and W=K+p.
// For every surviving class we store
//   d = T^W(2^K r - 1), q = odd-step count through W.
// Transfer identity gives
//   T^W(2^K(r + b 2^p + 2^(p+1)A)-1)
//     = d + b*3^q + 2*3^q A.
// Therefore each child b in {0,1} can be extended by exactly ONE shortcut
// step. The child survives iff the new coefficient still satisfies
//   3^q' >= 2^(W+1).
//
// The exact lower-predecessor half-sieve is applied at p=2, so one m mod 4
// child is removed without further expansion. No concrete seed enumeration.

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using u128 = unsigned __int128;

struct State{
  uint64_t r;
  u128 d;
  uint8_t q;
};

static std::string s128(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}

static inline u128 T(u128 x){
  return (x&1)?(3*x+1)/2:x/2;
}

int main(int argc,char**argv){
  if(argc<3||argc>4){
    std::cerr<<"usage: scout K PMAX [MAX_CLASSES]\n";
    return 2;
  }
  const int K=std::stoi(argv[1]);
  const int PMAX=std::stoi(argv[2]);
  const uint64_t MAXC=argc==4?std::stoull(argv[3]):50000000ULL;
  if(K<1||K>50||PMAX<2||PMAX>50||K+PMAX>=127){
    std::cerr<<"BAD_RANGE\n";return 2;
  }

  std::array<u128,128> P3{};
  P3[0]=1;
  for(int i=1;i<128;++i){
    if(P3[i-1] > (~u128(0))/3){break;}
    P3[i]=P3[i-1]*3;
  }

  // Start at p=1: the only odd residue m=1 mod 2.
  int p=1;
  int W=K+p;
  uint64_t r=1;
  u128 x=(u128(1)<<K)-1;
  uint8_t q=0;
  bool alive=true;
  for(int t=1;t<=W;++t){
    if(x&1){++q;x=(3*x+1)/2;} else x/=2;
    if(P3[q] < (u128(1)<<t)) alive=false;
  }
  std::vector<State> cur;
  if(alive) cur.push_back(State{r,x,q});

  std::cout<<"SPARSE_PREFIX_LEVEL"
           <<" K="<<K<<" p=1 W="<<(K+1)
           <<" live="<<cur.size()
           <<" total_odd_classes=1"
           <<" live_fraction="<<(cur.empty()?0.0:1.0)
           <<"\n";

  while(p<PMAX && !cur.empty()){
    const int nextp=p+1;
    const int nextW=K+nextp;
    std::vector<State> nxt;
    nxt.reserve(std::min<uint64_t>(MAXC,cur.size()*2ULL));

    const int killed_mod4=(K&1)?3:1;

    for(const State &st:cur){
      const u128 pq=P3[st.q];
      for(int b=0;b<2;++b){
        const uint64_t rr=st.r + (uint64_t(b)<<p);

        if(nextp==2 && int(rr&3ULL)==killed_mod4)
          continue;

        const u128 y=st.d + u128(b)*pq;
        uint8_t q2=st.q;
        u128 d2;
        if(y&1){++q2;d2=(3*y+1)/2;}
        else d2=y/2;

        if(P3[q2] < (u128(1)<<nextW))
          continue;

        nxt.push_back(State{rr,d2,q2});
        if(nxt.size()>MAXC){
          std::cout<<"SPARSE_PREFIX_ABORT"
                   <<" K="<<K<<" p="<<nextp
                   <<" live_exceeded="<<MAXC<<"\n";
          return 0;
        }
      }
    }

    cur.swap(nxt);
    p=nextp;
    const u128 total=u128(1)<<(p-1);
    long double frac=(long double)cur.size()/(long double)(uint64_t(1)<<(std::min(p-1,63)));
    std::cout<<"SPARSE_PREFIX_LEVEL"
             <<" K="<<K<<" p="<<p<<" W="<<(K+p)
             <<" live="<<cur.size()
             <<" total_odd_classes=2^"<<(p-1)
             <<" live_fraction="<<(double)frac
             <<"\n";
  }

  std::cout<<"SPARSE_PREFIX_DONE K="<<K<<" p="<<p<<" live="<<cur.size()<<"\n";
  return 0;
}
