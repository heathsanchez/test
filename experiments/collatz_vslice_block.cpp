// Exact compiled Collatz valuation-slice scanner.
// For n = 2^k m - 1 with m odd:
//   T^k(n) = 3^k m - 1,
// and the next shortcut step is forced even.
// The remaining orbit is processed in exact 16-step residue blocks.
// A coefficient-only lower bound certifies whole blocks that cannot descend;
// only near a possible descent are individual steps expanded.
#include <omp.h>
#include <algorithm>
#include <array>
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
  if(argc<3||argc>5){std::cerr<<"usage: prog K H [SHARDS IDX]\n";return 2;}
  int k=std::stoi(argv[1]),H=std::stoi(argv[2]),S=1,I=0;
  if(argc==5){S=std::stoi(argv[3]);I=std::stoi(argv[4]);}
  init_table();
  const u128 L=parse128("2392312122059207475200"),U=parse128("4722366482869645213695");
  const u128 M=u128(1)<<k;
  uint64_t mlo=uint64_t((L+1+M-1)/M),mhi=uint64_t((U+1)/M);
  if((mlo&1)==0)++mlo; if((mhi&1)==0)--mhi;
  uint64_t total=(mhi-mlo)/2+1,a=total*I/S,b=total*(I+1)/S;
  uint64_t smlo=mlo+2*a,smhi=(b?mlo+2*(b-1):mlo-2);
  if(I==S-1)smhi=mhi;
  u128 p3k=1;for(int i=0;i<k;++i)p3k*=3;
  const u128 UMAX=~u128(0);
  int global_best=0;u128 global_seed=0;unsigned long long scanned=0,fastblocks=0,slowblocks=0;
  std::cout<<"EXACT_V2_BLOCK k="<<k<<" count="<<((smhi-smlo)/2+1)<<" horizon="<<H<<" shard="<<I<<"/"<<S<<" threads="<<omp_get_max_threads()<<"\n";
#pragma omp parallel
  {
    int lbest=0;u128 lseed=0;unsigned long long lscan=0,lfb=0,lsb=0;
#pragma omp for schedule(dynamic,4096)
    for(uint64_t m=smlo;m<=smhi;m+=2){
      ++lscan;u128 seed=(u128(m)<<k)-1;u128 x=(p3k*u128(m)-1)>>1;int t=k+1,descent=H+1;
      if(x<seed)descent=t;
      while(descent==H+1&&t+B<=H){
        const Block&bl=TAB[uint32_t(x)&MASK];
        u128 num=seed<<bl.tmin,den=P3[bl.qmin];
        u128 threshold=(num+den-1)/den;
        if(x>=threshold && x<=(UMAX-bl.A)/bl.p3){
          x=(u128(bl.p3)*x+bl.A)>>B;t+=B;++lfb;continue;
        }
        ++lsb;
        for(int j=0;j<B&&t<H;++j){step_u128(x);++t;if(x<seed){descent=t;break;}}
      }
      while(descent==H+1&&t<H){step_u128(x);++t;if(x<seed){descent=t;break;}}
      if(descent>lbest){lbest=descent;lseed=seed;}
    }
#pragma omp critical
    {scanned+=lscan;fastblocks+=lfb;slowblocks+=lsb;if(lbest>global_best){global_best=lbest;global_seed=lseed;}}
  }
  std::cout<<"SCANNED "<<scanned<<" fast_blocks="<<fastblocks<<" slow_blocks="<<slowblocks<<"\n";
  std::cout<<"BEST first_descent="<<global_best<<" seed="<<str128(global_seed)<<"\n";
  std::cout<<(global_best==H+1?"STATUS SURVIVOR_AT_HORIZON\n":"STATUS COMPILED\n");
}
