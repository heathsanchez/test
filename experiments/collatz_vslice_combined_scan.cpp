// Exact Collatz valuation scanner composing three independently verified filters:
//
//   1. lower-predecessor merge on one m mod 4 class;
//   2. transfer-theorem coefficient contraction on m mod 2^PREFIX_BITS;
//   3. strong-induction convergence sieve on n mod 2^STRONG_BITS.
//
// Only seeds surviving ALL three filters are explicitly scanned. This is the
// RealityGraph-style composition: accepted laws intersect their residuals;
// no filter receives authority from another.
//
// The strong sieve is generated from first principles at startup. A low-bit
// residue b is dead when a lower prefix is dead, when its affine family
// coalesces after S steps with a smaller b', or when its S-step affine image is
// below the starting family for every high coefficient.

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
#ifndef PREFIX_BITS
#define PREFIX_BITS 24
#endif
#ifndef STRONG_BITS
#define STRONG_BITS 22
#endif

static constexpr int B=BLOCK_BITS;
static constexpr int P=PREFIX_BITS;
static constexpr int S=STRONG_BITS;
static_assert(B>=4&&B<=20);
static_assert(P>=2&&P<=24);
static_assert(S>=4&&S<=24);
static constexpr uint32_t BMASK=(uint32_t(1)<<B)-1;
static constexpr uint32_t PMOD=(uint32_t(1)<<P);
static constexpr uint32_t PMASK=PMOD-1;
static constexpr uint32_t SMASK=(uint32_t(1)<<S)-1;
static const u128 UMAX=~u128(0);
static const u128 LIVE_L=u128(2075)<<60;
static const uint64_t FIRST_DANGEROUS=114208327604ULL;

static u128 parse128(const std::string&s){u128 x=0;for(char c:s)x=x*10+(c-'0');return x;}
static std::string str128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}
static inline u128 T(u128 n){return(n&1)?(3*n+1)/2:n/2;}

struct Block{uint32_t p3,A;uint8_t tmin,qmin,qfinal,pad;};
static std::array<uint32_t,B+1>P3;
static std::array<u128,B+1>LIMIT;
static std::array<uint32_t,B+1>REM;
static std::vector<Block>TAB;

// Prefix type: 0 merge, 1 transfer contraction, 2 live.
static std::vector<uint8_t>RTYPE;
static std::vector<uint8_t>STRONG_LIVE;

static void init_blocks(){
  P3[0]=1;
  for(int i=1;i<=B;++i)P3[i]=P3[i-1]*3u;
  for(int q=0;q<=B;++q){LIMIT[q]=UMAX/u128(P3[q]);REM[q]=uint32_t(UMAX%u128(P3[q]));}
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

static inline bool step_u128(u128&x){
  if(x&1){if(x>(UMAX-1)/3)return false;x=(3*x+1)>>1;}
  else x>>=1;
  return true;
}

static void init_prefix(int k,uint64_t&merge_classes,uint64_t&contract_classes,uint64_t&live_classes){
  int W=k+P;
  if(!(k>=8&&W<127&&uint64_t(W)<FIRST_DANGEROUS)){std::cerr<<"PREFIX_PRECONDITION\n";std::exit(4);}
  std::vector<u128> pow3(W+1);pow3[0]=1;
  for(int i=1;i<=W;++i)pow3[i]=pow3[i-1]*3;
  RTYPE.assign(PMOD,0);
  merge_classes=contract_classes=live_classes=0;
  int merge_mod=(k&1)?3:1;
  for(uint32_t m=1;m<PMOD;m+=2){
    if(int(m&3u)==merge_mod){RTYPE[m]=0;++merge_classes;continue;}
    u128 x=(u128(m)<<k)-1;int q=0;bool contracted=false;
    for(int t=1;t<=W;++t){
      if(x&1){++q;x=(3*x+1)>>1;}else x>>=1;
      if(pow3[q]<(u128(1)<<t)){RTYPE[m]=1;++contract_classes;contracted=true;break;}
    }
    if(!contracted){RTYPE[m]=2;++live_classes;}
  }
}

static uint64_t pow3u(int c){
  uint64_t x=1;
  for(int i=0;i<c;++i){if(x>UINT64_MAX/3)std::exit(7);x*=3;}
  return x;
}
struct CD{int c;uint64_t d;};
static CD Tk(uint64_t b,int k){
  u128 n=b;int c=0;
  for(int i=0;i<k;++i){if(n&1)++c;n=T(n);}
  if(n>UINT64_MAX)std::exit(8);
  return{c,(uint64_t)n};
}
static uint64_t strong_key(int c,uint64_t d){
  if(d>=(UINT64_C(1)<<56))std::exit(9);
  return(uint64_t(c)<<56)|d;
}
static void init_strong(){
  std::vector<uint8_t>prev(1,1),cur;
  for(int k=1;k<=S;++k){
    uint64_t N=UINT64_C(1)<<k;
    uint64_t pmask=(UINT64_C(1)<<(k-1))-1;
    cur.assign(N,0);
    std::unordered_set<uint64_t>seen;
    seen.reserve((size_t)(N*1.2));
    for(uint64_t b=0;b<N;++b){
      CD cd=Tk(b,k);
      uint64_t q=strong_key(cd.c,cd.d);
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

static uint64_t count_residue(uint64_t lo,uint64_t hi,uint32_t r){
  if(lo>hi)return 0;
  uint64_t delta=(uint64_t(r)-(lo&PMASK))&PMASK;
  uint64_t first=lo+delta;
  if(first<lo||first>hi)return 0;
  return(hi-first)/PMOD+1;
}

int main(int argc,char**argv){
  if(argc!=7){std::cerr<<"usage: prog K H SHARDS IDX LOWER UPPER\n";return 2;}
  int k=std::stoi(argv[1]),H=std::stoi(argv[2]),NS=std::stoi(argv[3]),I=std::stoi(argv[4]);
  u128 L=parse128(argv[5]),U=parse128(argv[6]);
  if(!(8<=k&&0<=I&&I<NS&&L<=U&&L>=LIVE_L&&U<2*L+1)){std::cerr<<"BAD_DOMAIN\n";return 2;}

  init_blocks();
  uint64_t merge_classes,contract_classes,prefix_live_classes;
  init_prefix(k,merge_classes,contract_classes,prefix_live_classes);
  init_strong();

  u128 M=u128(1)<<k;
  u128 qmlo=(L+1+M-1)/M,qmhi=(U+1)/M;
  if(qmhi>u128(UINT64_MAX)){std::cerr<<"M_SPACE_EXCEEDS_U64\n";return 5;}
  uint64_t mlo=uint64_t(qmlo),mhi=uint64_t(qmhi);
  if((mlo&1)==0)++mlo;if((mhi&1)==0)--mhi;
  if(mhi<mlo){std::cout<<"STATUS COMBINED_SIEVES_AND_SCAN_CLOSED\n";return 0;}

  uint64_t full_total=(mhi-mlo)/2+1;
  uint64_t ia=full_total*I/NS,ib=full_total*(I+1)/NS;
  uint64_t smlo=mlo+2*ia,smhi=(ib?mlo+2*(ib-1):mlo-2);

  uint64_t merge_seeds=0,contract_seeds=0,prefix_live_seeds=0;
  for(uint32_t r=1;r<PMOD;r+=2){
    uint64_t c=count_residue(mlo,mhi,r);
    if(RTYPE[r]==0)merge_seeds+=c;
    else if(RTYPE[r]==1)contract_seeds+=c;
    else prefix_live_seeds+=c;
  }
  if(merge_seeds+contract_seeds+prefix_live_seeds!=full_total){std::cerr<<"PREFIX_COUNT_MISMATCH\n";return 6;}

  u128 p3k=1;for(int i=0;i<k;++i)p3k*=3;
  unsigned long long scanned=0,strong_killed=0,fastblocks=0,slowblocks=0,overflows=0;
  bool any_survivor=false;u128 witness=0;
  int global_best=0;u128 global_best_seed=0;

  uint64_t strong_live_residues=0;
  for(uint8_t x:STRONG_LIVE)strong_live_residues+=x;

  std::cout<<"EXACT_V2_COMBINED_SCAN"
           <<" B="<<B<<" P="<<P<<" S="<<S<<" k="<<k
           <<" full_count="<<full_total
           <<" merge_killed="<<merge_seeds
           <<" transfer_killed="<<contract_seeds
           <<" prefix_live="<<prefix_live_seeds
           <<" strong_live_residues="<<strong_live_residues
           <<" horizon="<<H<<" shard="<<I<<"/"<<NS
           <<" lower="<<str128(L)<<" upper="<<str128(U)<<"\n";

#pragma omp parallel
  {
    unsigned long long lscan=0,lstrong=0,lfb=0,lsb=0,lov=0;
    int lbest=0;u128 lbestseed=0,lwitness=0;bool lsurvivor=false;
#pragma omp for schedule(dynamic,64)
    for(uint32_t r=1;r<PMOD;r+=2){
      if(RTYPE[r]!=2)continue;
      uint64_t delta=(uint64_t(r)-(smlo&PMASK))&PMASK;
      uint64_t m=smlo+delta;
      if(m<smlo||m>smhi)continue;
      for(;;){
        u128 seed=(u128(m)<<k)-1;
        if(!STRONG_LIVE[uint32_t(seed)&SMASK]){
          ++lstrong;
        }else{
          ++lscan;
          u128 x=(p3k*u128(m)-1)>>1;
          int t=k+1,descent=H+1;bool overflow=false;
          if(x<seed)descent=t;
          while(descent==H+1&&!overflow&&t+B<=H){
            const Block&bl=TAB[uint32_t(x)&BMASK];
            u128 lim=LIMIT[bl.qfinal];
            bool safe=(x<lim)||(x==lim&&bl.A<=REM[bl.qfinal]);
            u128 num=seed<<bl.tmin,den=P3[bl.qmin];
            if(safe&&x*den>=num){x=(u128(bl.p3)*x+bl.A)>>B;t+=B;++lfb;continue;}
            ++lsb;
            for(int j=0;j<B&&t<H;++j){
              if(!step_u128(x)){overflow=true;break;}
              ++t;if(x<seed){descent=t;break;}
            }
          }
          while(descent==H+1&&!overflow&&t<H){
            if(!step_u128(x)){overflow=true;break;}
            ++t;if(x<seed){descent=t;break;}
          }
          if(overflow){
            ++lov;
#pragma omp critical
            std::cout<<"OVERFLOW_SEED seed="<<str128(seed)<<" reached_after_t="<<t<<"\n";
          }else{
            if(descent>lbest){lbest=descent;lbestseed=seed;}
            if(descent==H+1&&!lsurvivor){lsurvivor=true;lwitness=seed;}
          }
        }
        if(smhi-m<PMOD)break;
        m+=PMOD;
      }
    }
#pragma omp critical
    {
      scanned+=lscan;strong_killed+=lstrong;fastblocks+=lfb;slowblocks+=lsb;overflows+=lov;
      if(lbest>global_best){global_best=lbest;global_best_seed=lbestseed;}
      if(lsurvivor&&!any_survivor){any_survivor=true;witness=lwitness;}
    }
  }

  std::cout<<"COMBINED_COUNTS prefix_live="<<prefix_live_seeds
           <<" strong_killed_after_prefix="<<strong_killed
           <<" explicit="<<scanned<<"\n";
  std::cout<<"SCANNED "<<scanned<<" fast_blocks="<<fastblocks<<" slow_blocks="<<slowblocks<<" overflows="<<overflows<<"\n";
  std::cout<<"BEST first_descent_or_survival="<<global_best<<" seed="<<str128(global_best_seed)<<"\n";
  if(any_survivor){
    std::cout<<"SURVIVOR seed="<<str128(witness)<<" horizon="<<H<<"\nSTATUS SURVIVOR_FOUND\n";
  }else if(overflows){
    std::cout<<"STATUS OVERFLOW_REPLAY_REQUIRED\n";
  }else{
    std::cout<<"STATUS COMBINED_SIEVES_AND_SCAN_CLOSED\n";
  }
  return 0;
}
