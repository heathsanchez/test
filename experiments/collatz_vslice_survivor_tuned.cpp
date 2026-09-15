// Exact overflow-safe valuation-slice scanner with tunable block width.
// Compile with -DBLOCK_BITS=N (10..20 supported).
//
// Fast-block test is division-free and stores no u128 value per residue.
// For final block coefficient p3=3^q, LIMIT[q]=floor((2^128-1)/p3)
// and REM[q]=(2^128-1)%p3 are precomputed once. Then
//   p3*x + A <= UMAX
// iff x<LIMIT[q] or (x==LIMIT[q] && A<=REM[q]).
// Under that update-safety condition, qmin<=q guarantees x*3^qmin
// cannot overflow, so the lower-bound test is an exact cross-product.
#include <omp.h>
#include <algorithm>
#include <array>
#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using u128 = unsigned __int128;
#ifndef BLOCK_BITS
#define BLOCK_BITS 16
#endif
static constexpr int B=BLOCK_BITS;
static_assert(B>=4 && B<=20);
static constexpr uint32_t MASK=(uint32_t(1)<<B)-1;
static const u128 UMAX=~u128(0);

static u128 parse128(const std::string& s){u128 x=0; for(char c:s)x=x*10+(c-'0'); return x;}
static std::string str128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}

struct Block{uint32_t p3,A; uint8_t tmin,qmin;};
static std::array<uint32_t,B+1> P3;
static std::array<u128,B+1> LIMIT;
static std::array<uint32_t,B+1> REM;
static std::vector<Block> TAB;

static void init_table(){
  P3[0]=1;
  for(int i=1;i<=B;++i)P3[i]=P3[i-1]*3u;
  for(int q=0;q<=B;++q){
    LIMIT[q]=UMAX/u128(P3[q]);
    REM[q]=uint32_t(UMAX%u128(P3[q]));
  }
  TAB.resize(uint32_t(1)<<B);
  for(uint32_t r=0;r<(uint32_t(1)<<B);++r){
    uint32_t y=r,A=0,p3=1; int q=0,best_t=1,best_q=0; bool have=false;
    for(int t=0;t<B;++t){
      bool odd=y&1u;
      if(odd){y=(3u*y+1u)>>1; A=3u*A+(1u<<t); p3*=3u; ++q;} else y>>=1;
      int tt=t+1;
      if(!have){best_t=tt;best_q=q;have=true;}
      else {
        uint64_t lhs=uint64_t(P3[q])<<best_t;
        uint64_t rhs=uint64_t(P3[best_q])<<tt;
        if(lhs<rhs){best_t=tt;best_q=q;}
      }
    }
    TAB[r]={p3,A,(uint8_t)best_t,(uint8_t)best_q};
  }
}

static inline bool step_u128(u128 &x){
  if(x&1){
    if(x>(UMAX-1)/3) return false;
    x=(3*x+1)>>1;
  } else x>>=1;
  return true;
}
static inline bool update_safe(const Block& bl,u128 x){
  // p3 is a power of 3, recover q cheaply from qmin? No: qmin is a prefix.
  // The table stores p3 itself; B<=20, so a short lookup is avoided by
  // computing the exact quotient condition with a precomputed per-p3 map
  // encoded below in QBYRES at table construction.
  return true;
}

struct TBlock{uint32_t p3,A; uint8_t tmin,qmin,qfinal,pad;};
static std::vector<TBlock> TTAB;

static void init_tuned(){
  init_table();
  TTAB.resize(TAB.size());
  for(size_t i=0;i<TAB.size();++i){
    const auto& b=TAB[i];
    uint8_t q=0;
    while(q<B && P3[q]!=b.p3)++q;
    TTAB[i]={b.p3,b.A,b.tmin,b.qmin,q,0};
  }
  std::vector<Block>().swap(TAB);
}

int main(int argc,char**argv){
  if(argc!=7){std::cerr<<"usage: prog K H SHARDS IDX LOWER UPPER\n";return 2;}
  const int k=std::stoi(argv[1]),H=std::stoi(argv[2]),S=std::stoi(argv[3]),I=std::stoi(argv[4]);
  const u128 L=parse128(argv[5]),U=parse128(argv[6]);
  if(!(0<=I && I<S && L<=U)){std::cerr<<"BAD_ARGS\n";return 2;}

  init_tuned();
  const u128 M=u128(1)<<k;
  uint64_t mlo=uint64_t((L+1+M-1)/M),mhi=uint64_t((U+1)/M);
  if((mlo&1)==0)++mlo; if((mhi&1)==0)--mhi;
  if(mhi<mlo){
    std::cout<<"EXACT_V2_SURVIVOR_TUNED B="<<B<<" k="<<k<<" count=0 horizon="<<H<<" shard="<<I<<"/"<<S<<"\n";
    std::cout<<"SCANNED 0 overflows=0\nSTATUS EXHAUSTED_NO_SURVIVOR\n";
    return 0;
  }

  const uint64_t total=(mhi-mlo)/2+1,a=total*I/S,b=total*(I+1)/S;
  const uint64_t smlo=mlo+2*a,smhi=(b?mlo+2*(b-1):mlo-2);
  u128 p3k=1;for(int i=0;i<k;++i)p3k*=3;

  std::atomic<bool> found(false);
  u128 witness=0;
  unsigned long long scanned=0,fastblocks=0,slowblocks=0,overflows=0;
  int global_best=0; u128 global_best_seed=0;

  std::cout<<"EXACT_V2_SURVIVOR_TUNED B="<<B<<" k="<<k<<" count="<<((smhi-smlo)/2+1)
           <<" horizon="<<H<<" shard="<<I<<"/"<<S
           <<" threads="<<omp_get_max_threads()
           <<" table_bytes="<<(TTAB.size()*sizeof(TBlock))
           <<" lower="<<str128(L)<<" upper="<<str128(U)<<"\n";

#pragma omp parallel
  {
    unsigned long long lscan=0,lfb=0,lsb=0,lov=0;
    int lbest=0; u128 lbestseed=0;
#pragma omp for schedule(dynamic,4096)
    for(uint64_t m=smlo;m<=smhi;m+=2){
      if(found.load(std::memory_order_relaxed)) continue;
      ++lscan;
      const u128 seed=(u128(m)<<k)-1;
      u128 x=(p3k*u128(m)-1)>>1;
      int t=k+1,descent=H+1;
      bool overflow=false;
      if(x<seed) descent=t;

      while(descent==H+1 && !overflow && t+B<=H){
        const TBlock& bl=TTAB[uint32_t(x)&MASK];
        const u128 lim=LIMIT[bl.qfinal];
        const bool safe=(x<lim)||(x==lim && bl.A<=REM[bl.qfinal]);
        const u128 num=seed<<bl.tmin;
        const u128 den=P3[bl.qmin];
        if(safe && x*den>=num){
          x=(u128(bl.p3)*x+bl.A)>>B;
          t+=B; ++lfb; continue;
        }
        ++lsb;
        for(int j=0;j<B && t<H;++j){
          if(!step_u128(x)){overflow=true;break;}
          ++t;
          if(x<seed){descent=t;break;}
        }
      }
      while(descent==H+1 && !overflow && t<H){
        if(!step_u128(x)){overflow=true;break;}
        ++t;
        if(x<seed){descent=t;break;}
      }

      if(overflow){
        ++lov;
#pragma omp critical
        std::cout<<"OVERFLOW_SEED seed="<<str128(seed)<<" reached_after_t="<<t<<"\n";
        continue;
      }

      if(descent>lbest){lbest=descent;lbestseed=seed;}
      if(descent==H+1){
#pragma omp critical
        {
          if(!found.load(std::memory_order_relaxed)){
            witness=seed;
            found.store(true,std::memory_order_relaxed);
          }
        }
      }
    }
#pragma omp critical
    {
      scanned+=lscan;fastblocks+=lfb;slowblocks+=lsb;overflows+=lov;
      if(lbest>global_best){global_best=lbest;global_best_seed=lbestseed;}
    }
  }

  std::cout<<"SCANNED "<<scanned<<" fast_blocks="<<fastblocks
           <<" slow_blocks="<<slowblocks<<" overflows="<<overflows<<"\n";
  std::cout<<"BEST first_descent_or_survival="<<global_best
           <<" seed="<<str128(global_best_seed)<<"\n";
  if(found.load()){
    std::cout<<"SURVIVOR seed="<<str128(witness)<<" horizon="<<H<<"\n";
    std::cout<<"STATUS SURVIVOR_FOUND\n";
  } else if(overflows){
    std::cout<<"STATUS OVERFLOW_REPLAY_REQUIRED\n";
  } else {
    std::cout<<"STATUS EXHAUSTED_NO_SURVIVOR\n";
  }
  return 0;
}
