// Exact valuation-slice scanner with inductive lower-predecessor half sieve.
//
// For n = 2^K m - 1 (m odd), set p=(n-1)/2.
// If 3^(K-1)m == 3 (mod 4), then
//     T^(K+2)(n) = T^(K+1)(p).
// Equivalently the killed m class is:
//     m == 3 mod 4 for K odd,
//     m == 1 mod 4 for K even.
//
// On the tightened live interval U < 2L+1, p<L for every n<=U, so the
// killed half merges into the already-lower region and needs no seedwise scan.
// Only the complementary m mod 4 class is scanned here.
//
// The survivor scan is the exact cache-tuned, synchronization-free block
// compiler. Rare u128 overflow seeds are emitted for external big-int replay.
#include <omp.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using u128 = unsigned __int128;
#ifndef BLOCK_BITS
#define BLOCK_BITS 10
#endif
static constexpr int B=BLOCK_BITS;
static_assert(B>=4 && B<=20);
static constexpr uint32_t MASK=(uint32_t(1)<<B)-1;
static const u128 UMAX=~u128(0);

static u128 parse128(const std::string& s){u128 x=0; for(char c:s)x=x*10+(c-'0'); return x;}
static std::string str128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}

struct Block{uint32_t p3,A; uint8_t tmin,qmin,qfinal,pad;};
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
      const bool odd=y&1u;
      if(odd){y=(3u*y+1u)>>1; A=3u*A+(1u<<t); p3*=3u; ++q;} else y>>=1;
      const int tt=t+1;
      if(!have){best_t=tt;best_q=q;have=true;}
      else {
        const uint64_t lhs=uint64_t(P3[q])<<best_t;
        const uint64_t rhs=uint64_t(P3[best_q])<<tt;
        if(lhs<rhs){best_t=tt;best_q=q;}
      }
    }
    TAB[r]={p3,A,(uint8_t)best_t,(uint8_t)best_q,(uint8_t)q,0};
  }
}

static inline bool step_u128(u128 &x){
  if(x&1){
    if(x>(UMAX-1)/3) return false;
    x=(3*x+1)>>1;
  } else x>>=1;
  return true;
}

static uint64_t first_congruent(uint64_t lo,int r){
  uint64_t d=(uint64_t(r)+4-(lo&3u))&3u;
  return lo+d;
}
static uint64_t last_congruent(uint64_t hi,int r){
  uint64_t d=((hi&3u)+4-uint64_t(r))&3u;
  return hi-d;
}

int main(int argc,char**argv){
  if(argc!=7){std::cerr<<"usage: prog K H SHARDS IDX LOWER UPPER\n";return 2;}
  const int k=std::stoi(argv[1]),H=std::stoi(argv[2]),S=std::stoi(argv[3]),I=std::stoi(argv[4]);
  const u128 L=parse128(argv[5]),U=parse128(argv[6]);
  if(!(1<=k && 0<=I && I<S && L<=U)){std::cerr<<"BAD_ARGS\n";return 2;}
  if(!(U < 2*L + 1)){std::cerr<<"MERGE_INTERVAL_PRECONDITION_FAILED\n";return 3;}

  init_table();
  const u128 M=u128(1)<<k;
  uint64_t mlo=uint64_t((L+1+M-1)/M),mhi=uint64_t((U+1)/M);
  if((mlo&1)==0)++mlo; if((mhi&1)==0)--mhi;

  const int killed=(k&1)?3:1;
  const int survivor=(k&1)?1:3;

  if(mhi<mlo){
    std::cout<<"EXACT_V2_MERGE_SCAN B="<<B<<" k="<<k<<" full_count=0 survivor_count=0 horizon="<<H<<" shard="<<I<<"/"<<S<<"\n";
    std::cout<<"MERGE_KILLED_MOD4 "<<killed<<" SURVIVOR_MOD4 "<<survivor<<"\n";
    std::cout<<"SCANNED 0 overflows=0\nSTATUS INDUCTIVE_HALF_CLOSED_AND_SURVIVORS_EXHAUSTED\n";
    return 0;
  }

  const uint64_t full_total=(mhi-mlo)/2+1;
  uint64_t sfirst=first_congruent(mlo,survivor);
  uint64_t slast=last_congruent(mhi,survivor);
  uint64_t survivor_total=(sfirst<=slast)?((slast-sfirst)/4+1):0;
  const uint64_t killed_total=full_total-survivor_total;

  const uint64_t a=survivor_total*I/S,b=survivor_total*(I+1)/S;
  const uint64_t smlo=sfirst+4*a;
  const uint64_t smhi=(b?sfirst+4*(b-1):sfirst-4);

  u128 p3k=1;for(int i=0;i<k;++i)p3k*=3;

  bool any_survivor=false;
  u128 witness=0;
  unsigned long long scanned=0,fastblocks=0,slowblocks=0,overflows=0;
  int global_best=0; u128 global_best_seed=0;

  std::cout<<"EXACT_V2_MERGE_SCAN B="<<B<<" k="<<k
           <<" full_count="<<full_total
           <<" survivor_count="<<survivor_total
           <<" killed_count="<<killed_total
           <<" horizon="<<H<<" shard="<<I<<"/"<<S
           <<" threads="<<omp_get_max_threads()
           <<" lower="<<str128(L)<<" upper="<<str128(U)<<"\n";
  std::cout<<"MERGE_KILLED_MOD4 "<<killed<<" SURVIVOR_MOD4 "<<survivor<<"\n";

  if(a<b){
#pragma omp parallel
    {
      unsigned long long lscan=0,lfb=0,lsb=0,lov=0;
      int lbest=0; u128 lbestseed=0,lwitness=0;
      bool lsurvivor=false;
#pragma omp for schedule(static)
      for(uint64_t m=smlo;m<=smhi;m+=4){
        ++lscan;
        const u128 seed=(u128(m)<<k)-1;
        u128 x=(p3k*u128(m)-1)>>1;
        int t=k+1,descent=H+1;
        bool overflow=false;
        if(x<seed) descent=t;

        while(descent==H+1 && !overflow && t+B<=H){
          const Block& bl=TAB[uint32_t(x)&MASK];
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
        if(descent==H+1 && !lsurvivor){lsurvivor=true;lwitness=seed;}
      }
#pragma omp critical
      {
        scanned+=lscan;fastblocks+=lfb;slowblocks+=lsb;overflows+=lov;
        if(lbest>global_best){global_best=lbest;global_best_seed=lbestseed;}
        if(lsurvivor && !any_survivor){any_survivor=true;witness=lwitness;}
      }
    }
  }

  std::cout<<"SCANNED "<<scanned<<" fast_blocks="<<fastblocks
           <<" slow_blocks="<<slowblocks<<" overflows="<<overflows<<"\n";
  std::cout<<"BEST first_descent_or_survival="<<global_best
           <<" seed="<<str128(global_best_seed)<<"\n";
  if(any_survivor){
    std::cout<<"SURVIVOR seed="<<str128(witness)<<" horizon="<<H<<"\n";
    std::cout<<"STATUS SURVIVOR_FOUND\n";
  } else if(overflows){
    std::cout<<"STATUS OVERFLOW_REPLAY_REQUIRED\n";
  } else {
    std::cout<<"STATUS INDUCTIVE_HALF_CLOSED_AND_SURVIVORS_EXHAUSTED\n";
  }
  return 0;
}
