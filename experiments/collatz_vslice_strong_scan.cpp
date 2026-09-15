// Exact valuation-slice scanner with a strong-induction low-bit convergence sieve.
//
// The low-bit sieve is generated from first principles at startup; no external
// map or published bitset is trusted.
//
// For residue b mod 2^S:
//   T^S(a*2^S+b)=a*3^c+d.
// A residue is inductively dead if:
//   (1) a lower-bit prefix is already dead;
//   (2) a smaller b' has the same (c,d), so both affine families coalesce;
//   (3) the affine image is below the start for every a>=1.
//
// Only final live residues are explicitly scanned with the exact 10-bit affine
// block compiler. Dead residues are closed by strong induction/minimal
// counterexample reasoning; live residues remain verifier-gated by exact scan.

#include <omp.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <unordered_set>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;
#ifndef BLOCK_BITS
#define BLOCK_BITS 10
#endif
#ifndef STRONG_BITS
#define STRONG_BITS 22
#endif
static constexpr int B=BLOCK_BITS;
static constexpr int S=STRONG_BITS;
static_assert(B>=4&&B<=20);
static_assert(S>=4&&S<=24);
static constexpr uint32_t BMASK=(uint32_t(1)<<B)-1;
static constexpr uint32_t SMASK=(uint32_t(1)<<S)-1;
static const u128 UMAX=~u128(0);

static u128 parse128(const std::string&s){u128 x=0;for(char c:s)x=x*10+(c-'0');return x;}
static std::string str128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}
static inline u128 T(u128 n){return (n&1)?(3*n+1)/2:n/2;}

struct Block{uint32_t p3,A;uint8_t tmin,qmin,qfinal,pad;};
static std::array<uint32_t,B+1>P3;
static std::array<u128,B+1>LIMIT;
static std::array<uint32_t,B+1>REM;
static std::vector<Block>TAB;
static std::vector<uint8_t>STRONG_LIVE;

static void init_blocks(){
  P3[0]=1;
  for(int i=1;i<=B;++i)P3[i]=P3[i-1]*3u;
  for(int q=0;q<=B;++q){
    LIMIT[q]=UMAX/u128(P3[q]);
    REM[q]=uint32_t(UMAX%u128(P3[q]));
  }
  TAB.resize(uint32_t(1)<<B);
  for(uint32_t r=0;r<(uint32_t(1)<<B);++r){
    uint32_t y=r,A=0,p3=1;int q=0,best_t=1,best_q=0;bool have=false;
    for(int t=0;t<B;++t){
      bool odd=y&1u;
      if(odd){y=(3u*y+1u)>>1;A=3u*A+(1u<<t);p3*=3u;++q;}else y>>=1;
      int tt=t+1;
      if(!have){best_t=tt;best_q=q;have=true;}
      else{
        uint64_t lhs=uint64_t(P3[q])<<best_t;
        uint64_t rhs=uint64_t(P3[best_q])<<tt;
        if(lhs<rhs){best_t=tt;best_q=q;}
      }
    }
    TAB[r]={p3,A,(uint8_t)best_t,(uint8_t)best_q,(uint8_t)q,0};
  }
}

static uint64_t pow3u(int c){
  uint64_t x=1;
  for(int i=0;i<c;++i){if(x>UINT64_MAX/3){std::exit(7);}x*=3;}
  return x;
}
struct CD{int c;uint64_t d;};
static CD Tk(uint64_t b,int k){
  u128 n=b;int c=0;
  for(int i=0;i<k;++i){if(n&1)++c;n=T(n);}
  if(n>UINT64_MAX){std::exit(8);}
  return {c,(uint64_t)n};
}
static uint64_t key(int c,uint64_t d){
  if(d>=(UINT64_C(1)<<56)){std::exit(9);}
  return (uint64_t(c)<<56)|d;
}
static void init_strong(){
  std::vector<uint8_t> prev(1,1),cur;
  for(int k=1;k<=S;++k){
    uint64_t N=UINT64_C(1)<<k;
    uint64_t pmask=(UINT64_C(1)<<(k-1))-1;
    cur.assign(N,0);
    std::unordered_set<uint64_t> seen;
    seen.reserve((size_t)(N*1.2));
    for(uint64_t b=0;b<N;++b){
      CD cd=Tk(b,k);
      uint64_t q=key(cd.c,cd.d);
      bool dup=seen.find(q)!=seen.end();
      seen.insert(q);
      if(k>1&&!prev[b&pmask])continue;
      if(dup)continue;
      i128 l=i128(pow3u(cd.c))-i128(UINT64_C(1)<<k);
      i128 r=i128(b)-i128(cd.d);
      if(l<0&&l<r)continue;
      cur[b]=1;
    }
    prev.swap(cur);
  }
  STRONG_LIVE=std::move(prev);
}

static inline bool step_u128(u128&x){
  if(x&1){if(x>(UMAX-1)/3)return false;x=(3*x+1)>>1;}
  else x>>=1;
  return true;
}

int main(int argc,char**argv){
  if(argc!=7){std::cerr<<"usage: prog K H SHARDS IDX LOWER UPPER\n";return 2;}
  int k=std::stoi(argv[1]),H=std::stoi(argv[2]),NS=std::stoi(argv[3]),I=std::stoi(argv[4]);
  u128 L=parse128(argv[5]),U=parse128(argv[6]);
  if(!(1<=k&&0<=I&&I<NS&&L<=U)){std::cerr<<"BAD_ARGS\n";return 2;}

  init_blocks();
  init_strong();

  u128 M=u128(1)<<k;
  u128 qmlo=(L+1+M-1)/M,qmhi=(U+1)/M;
  if(qmhi>u128(UINT64_MAX)){std::cerr<<"M_SPACE_EXCEEDS_U64\n";return 3;}
  uint64_t mlo=uint64_t(qmlo),mhi=uint64_t(qmhi);
  if((mlo&1)==0)++mlo;if((mhi&1)==0)--mhi;
  if(mhi<mlo){std::cout<<"STATUS STRONG_SIEVE_AND_SCAN_CLOSED\n";return 0;}

  uint64_t total=(mhi-mlo)/2+1;
  uint64_t a=total*I/NS,b=total*(I+1)/NS;
  uint64_t smlo=mlo+2*a,smhi=(b?mlo+2*(b-1):mlo-2);

  u128 p3k=1;for(int i=0;i<k;++i)p3k*=3;

  unsigned long long scanned=0,sieve_killed=0,fastblocks=0,slowblocks=0,overflows=0;
  bool any_survivor=false;u128 witness=0;
  int global_best=0;u128 global_best_seed=0;

  uint64_t live_residues=0;
  for(uint8_t x:STRONG_LIVE)live_residues+=x;
  std::cout<<"EXACT_V2_STRONG_SCAN"
           <<" strong_bits="<<S
           <<" strong_live_residues="<<live_residues
           <<" k="<<k<<" full_count="<<total
           <<" horizon="<<H<<" shard="<<I<<"/"<<NS
           <<" lower="<<str128(L)<<" upper="<<str128(U)<<"\n";

#pragma omp parallel
  {
    unsigned long long lscan=0,lkill=0,lfb=0,lsb=0,lov=0;
    bool lsurv=false;u128 lwit=0;
    int lbest=0;u128 lbestseed=0;
#pragma omp for schedule(static)
    for(uint64_t m=smlo;m<=smhi;m+=2){
      u128 seed=(u128(m)<<k)-1;
      uint32_t low=uint32_t(seed)&SMASK;
      if(!STRONG_LIVE[low]){++lkill;continue;}
      ++lscan;

      u128 x=seed;
      int t=0,descent=H+1;
      bool overflow=false;
      while(descent==H+1&&t<H){
        if(t+B<=H){
          const Block&bl=TAB[uint32_t(x)&BMASK];
          u128 lim=LIMIT[bl.qfinal];
          bool safe=(x<lim)||(x==lim&&bl.A<=REM[bl.qfinal]);
          u128 num=seed<<bl.tmin,den=P3[bl.qmin];
          if(safe&&x*den>=num){
            x=(u128(bl.p3)*x+bl.A)>>B;t+=B;++lfb;continue;
          }
          ++lsb;
          for(int j=0;j<B&&t<H;++j){
            if(!step_u128(x)){overflow=true;break;}
            ++t;if(x<seed){descent=t;break;}
          }
        }else{
          if(!step_u128(x)){overflow=true;break;}
          ++t;if(x<seed){descent=t;break;}
        }
        if(overflow)break;
      }

      if(overflow){
        ++lov;
#pragma omp critical
        std::cout<<"OVERFLOW_SEED seed="<<str128(seed)<<" reached_after_t="<<t<<"\n";
        continue;
      }
      if(descent>lbest){lbest=descent;lbestseed=seed;}
      if(descent==H+1&&!lsurv){lsurv=true;lwit=seed;}
    }
#pragma omp critical
    {
      scanned+=lscan;sieve_killed+=lkill;fastblocks+=lfb;slowblocks+=lsb;overflows+=lov;
      if(lbest>global_best){global_best=lbest;global_best_seed=lbestseed;}
      if(lsurv&&!any_survivor){any_survivor=true;witness=lwit;}
    }
  }

  std::cout<<"SIEVE_KILLED "<<sieve_killed<<" EXPLICIT "<<scanned<<"\n";
  std::cout<<"SCANNED "<<scanned<<" fast_blocks="<<fastblocks<<" slow_blocks="<<slowblocks<<" overflows="<<overflows<<"\n";
  std::cout<<"BEST first_descent_or_survival="<<global_best<<" seed="<<str128(global_best_seed)<<"\n";
  if(any_survivor){
    std::cout<<"SURVIVOR seed="<<str128(witness)<<" horizon="<<H<<"\nSTATUS SURVIVOR_FOUND\n";
  }else if(overflows){
    std::cout<<"STATUS OVERFLOW_REPLAY_REQUIRED\n";
  }else{
    std::cout<<"STATUS STRONG_SIEVE_AND_SCAN_CLOSED\n";
  }
  return 0;
}
