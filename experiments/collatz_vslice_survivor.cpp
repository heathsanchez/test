// Exact early-exit valuation-slice survivor scanner for shortcut Collatz.
// n = 2^k m - 1, m odd => T^k(n)=3^k m-1; next step forced even.
// Each 16-step residue block is either certified non-descending by an exact
// coefficient lower bound or expanded step-by-step.  A found survivor is an
// exact concrete witness; if all shards finish with none, the entire slice is
// exhausted through the requested horizon.
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
static constexpr int B=16;
static constexpr uint64_t MASK=(1u<<B)-1;

static u128 parse128(const std::string& s){u128 x=0; for(char c:s)x=x*10+(c-'0'); return x;}
static std::string str128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}

struct Block{uint32_t p3,A; uint8_t tmin,qmin;};
static std::array<uint32_t,B+1> P3;
static std::vector<Block> TAB;

static void init_table(){
  P3[0]=1; for(int i=1;i<=B;++i)P3[i]=P3[i-1]*3u;
  TAB.resize(1u<<B);
  for(uint32_t r=0;r<(1u<<B);++r){
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

static inline void step_u128(u128 &x){
  if(x&1){
    const u128 UMAX=~u128(0);
    if(x>(UMAX-1)/3){std::cerr<<"U128_OVERFLOW_REQUIRED\n"; std::abort();}
    x=(3*x+1)>>1;
  } else x>>=1;
}

int main(int argc,char**argv){
  if(argc!=7){
    std::cerr<<"usage: prog K H SHARDS IDX LOWER UPPER\n";
    return 2;
  }
  const int k=std::stoi(argv[1]),H=std::stoi(argv[2]),S=std::stoi(argv[3]),I=std::stoi(argv[4]);
  const u128 L=parse128(argv[5]),U=parse128(argv[6]);
  if(!(0<=I && I<S && L<=U)){std::cerr<<"BAD_ARGS\n";return 2;}

  init_table();
  const u128 M=u128(1)<<k;
  uint64_t mlo=uint64_t((L+1+M-1)/M),mhi=uint64_t((U+1)/M);
  if((mlo&1)==0)++mlo; if((mhi&1)==0)--mhi;
  if(mhi<mlo){
    std::cout<<"EXACT_V2_SURVIVOR k="<<k<<" count=0 horizon="<<H<<" shard="<<I<<"/"<<S<<"\n";
    std::cout<<"SCANNED 0\nSTATUS EXHAUSTED_NO_SURVIVOR\n";
    return 0;
  }
  const uint64_t total=(mhi-mlo)/2+1,a=total*I/S,b=total*(I+1)/S;
  const uint64_t smlo=mlo+2*a,smhi=(b?mlo+2*(b-1):mlo-2);
  u128 p3k=1;for(int i=0;i<k;++i)p3k*=3;
  const u128 UMAX=~u128(0);

  std::atomic<bool> found(false);
  u128 witness=0;
  unsigned long long scanned=0,fastblocks=0,slowblocks=0;
  int global_best=0; u128 global_best_seed=0;

  std::cout<<"EXACT_V2_SURVIVOR k="<<k<<" count="<<((smhi-smlo)/2+1)
           <<" horizon="<<H<<" shard="<<I<<"/"<<S
           <<" threads="<<omp_get_max_threads()
           <<" lower="<<str128(L)<<" upper="<<str128(U)<<"\n";

#pragma omp parallel
  {
    unsigned long long lscan=0,lfb=0,lsb=0;
    int lbest=0; u128 lbestseed=0;
#pragma omp for schedule(dynamic,4096)
    for(uint64_t m=smlo;m<=smhi;m+=2){
      if(found.load(std::memory_order_relaxed)) continue;
      ++lscan;
      const u128 seed=(u128(m)<<k)-1;
      u128 x=(p3k*u128(m)-1)>>1;
      int t=k+1,descent=H+1;
      if(x<seed) descent=t;

      while(descent==H+1 && t+B<=H){
        const Block& bl=TAB[uint32_t(x)&MASK];
        const u128 num=seed<<bl.tmin, den=P3[bl.qmin];
        const u128 threshold=(num+den-1)/den;
        if(x>=threshold && x<=(UMAX-bl.A)/bl.p3){
          x=(u128(bl.p3)*x+bl.A)>>B;
          t+=B; ++lfb; continue;
        }
        ++lsb;
        for(int j=0;j<B && t<H;++j){
          step_u128(x); ++t;
          if(x<seed){descent=t;break;}
        }
      }
      while(descent==H+1 && t<H){
        step_u128(x); ++t;
        if(x<seed){descent=t;break;}
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
      scanned+=lscan;fastblocks+=lfb;slowblocks+=lsb;
      if(lbest>global_best){global_best=lbest;global_best_seed=lbestseed;}
    }
  }

  std::cout<<"SCANNED "<<scanned<<" fast_blocks="<<fastblocks<<" slow_blocks="<<slowblocks<<"\n";
  std::cout<<"BEST first_descent_or_survival="<<global_best<<" seed="<<str128(global_best_seed)<<"\n";
  if(found.load()){
    std::cout<<"SURVIVOR seed="<<str128(witness)<<" horizon="<<H<<"\n";
    std::cout<<"STATUS SURVIVOR_FOUND\n";
  } else {
    std::cout<<"STATUS EXHAUSTED_NO_SURVIVOR\n";
  }
  return 0;
}
