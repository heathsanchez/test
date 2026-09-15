// Exact Collatz valuation scanner with compiled prefix transforms.
//
// For fixed K and prefix depth P, write m=A*2^P+b and
//     n=2^K*m-1 = A*2^(K+P) + B,  B=2^K*b-1.
// The first W=K+P shortcut parities depend only on B, hence exactly
//     T^W(n)=A*3^c + d,
// where c is the odd-step count and d=T^W(B).
//
// We classify each b once using the verified predecessor/transfer rules,
// compile only surviving b into (b,3^c,d), and then every concrete seed starts
// at time W from the compiled state. No seed replays the prefix.
//
// Overflow during the compiled affine start or later scan emits the original
// seed for arbitrary-precision replay.

#include <omp.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using u128=unsigned __int128;
#ifndef BLOCK_BITS
#define BLOCK_BITS 10
#endif
#ifndef PREFIX_BITS
#define PREFIX_BITS 24
#endif
static constexpr int BITS=BLOCK_BITS;
static constexpr int P=PREFIX_BITS;
static_assert(BITS>=4&&BITS<=20);
static_assert(P>=2&&P<=26);
static constexpr uint32_t BMASK=(uint32_t(1)<<BITS)-1;
static constexpr uint32_t PMOD=(uint32_t(1)<<P);
static constexpr uint32_t PMASK=PMOD-1;
static const u128 UMAX=~u128(0);
static const u128 LIVE_L=u128(2075)<<60;
static const uint64_t FIRST_DANGEROUS=114208327604ULL;

static u128 parse128(const std::string&s){u128 x=0;for(char c:s)x=x*10+(c-'0');return x;}
static std::string str128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}
static inline u128 T(u128 n){return(n&1)?(3*n+1)/2:n/2;}

struct Block{uint32_t p3,A;uint8_t tmin,qmin,qfinal,pad;};
static std::array<uint32_t,BITS+1>P3B;
static std::array<u128,BITS+1>LIMIT;
static std::array<uint32_t,BITS+1>REM;
static std::vector<Block>TAB;

struct Prefix{uint32_t b;uint8_t c;u128 p3,d;};
static std::vector<Prefix>LIVE;

static void init_blocks(){
  P3B[0]=1;
  for(int i=1;i<=BITS;++i)P3B[i]=P3B[i-1]*3u;
  for(int q=0;q<=BITS;++q){LIMIT[q]=UMAX/u128(P3B[q]);REM[q]=uint32_t(UMAX%u128(P3B[q]));}
  TAB.resize(uint32_t(1)<<BITS);
  for(uint32_t r=0;r<(uint32_t(1)<<BITS);++r){
    uint32_t y=r,A=0,p3=1;int q=0,best_t=1,best_q=0;bool have=false;
    for(int t=0;t<BITS;++t){
      bool odd=y&1u;
      if(odd){y=(3u*y+1u)>>1;A=3u*A+(1u<<t);p3*=3u;++q;}else y>>=1;
      int tt=t+1;
      if(!have){best_t=tt;best_q=q;have=true;}
      else{
        uint64_t lhs=uint64_t(P3B[q])<<best_t;
        uint64_t rhs=uint64_t(P3B[best_q])<<tt;
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

static void init_prefix(int k,uint64_t&merge_classes,uint64_t&contract_classes){
  const int W=k+P;
  if(!(k>=1&&W<80&&uint64_t(W)<FIRST_DANGEROUS)){std::cerr<<"PREFIX_PRECONDITION\n";std::exit(4);}
  std::vector<u128> pow3(W+1);pow3[0]=1;
  for(int i=1;i<=W;++i){
    if(pow3[i-1]>UMAX/3){std::cerr<<"POW3_OVERFLOW\n";std::exit(5);}
    pow3[i]=pow3[i-1]*3;
  }

  merge_classes=contract_classes=0;
  LIVE.clear();
  LIVE.reserve(PMOD/4);
  const int merge_mod=(k&1)?3:1;

  for(uint32_t b=1;b<PMOD;b+=2){
    if(int(b&3u)==merge_mod){++merge_classes;continue;}

    u128 x=(u128(b)<<k)-1;
    int q=0;bool contracted=false;
    for(int t=1;t<=W;++t){
      if(x&1){++q;x=(3*x+1)>>1;}else x>>=1;
      if(pow3[q]<(u128(1)<<t)){++contract_classes;contracted=true;break;}
    }
    if(contracted)continue;

    // Recompute full W-step residue transform (the loop may already be at W,
    // but keeping this independent makes the compiled certificate explicit).
    x=(u128(b)<<k)-1;q=0;
    for(int t=0;t<W;++t){if(x&1)++q;x=T(x);}
    LIVE.push_back(Prefix{b,(uint8_t)q,pow3[q],x});
  }
}

static uint64_t first_A(uint64_t mlo,uint32_t b){
  uint64_t r=mlo&PMASK;
  uint64_t delta=(uint64_t(b)-r)&PMASK;
  uint64_t m=mlo+delta;
  return m>>P;
}

int main(int argc,char**argv){
  if(argc!=7){std::cerr<<"usage: prog K H SHARDS IDX LOWER UPPER\n";return 2;}
  int k=std::stoi(argv[1]),H=std::stoi(argv[2]),NS=std::stoi(argv[3]),I=std::stoi(argv[4]);
  u128 L=parse128(argv[5]),U=parse128(argv[6]);
  if(!(1<=k&&0<=I&&I<NS&&L<=U&&L>=LIVE_L&&U<2*L+1)){std::cerr<<"BAD_DOMAIN\n";return 2;}
  const int W=k+P;
  if(H<W){std::cerr<<"HORIZON_BELOW_COMPILED_PREFIX\n";return 3;}

  init_blocks();
  uint64_t merge_classes,contract_classes;
  init_prefix(k,merge_classes,contract_classes);

  u128 M=u128(1)<<k;
  u128 qmlo=(L+1+M-1)/M,qmhi=(U+1)/M;
  if(qmhi>u128(UINT64_MAX)){std::cerr<<"M_SPACE_EXCEEDS_U64\n";return 6;}
  uint64_t mlo=uint64_t(qmlo),mhi=uint64_t(qmhi);
  if((mlo&1)==0)++mlo;if((mhi&1)==0)--mhi;
  if(mhi<mlo){std::cout<<"STATUS COMPILED_PREFIX_AND_SCAN_CLOSED\n";return 0;}

  uint64_t full_total=(mhi-mlo)/2+1;
  // Shard the concrete odd m interval, not prefix IDs.
  uint64_t ia=full_total*I/NS,ib=full_total*(I+1)/NS;
  uint64_t smlo=mlo+2*ia,smhi=(ib?mlo+2*(ib-1):mlo-2);

  unsigned long long scanned=0,fastblocks=0,slowblocks=0,overflows=0;
  bool any_survivor=false;u128 witness=0;
  int global_best=0;u128 global_best_seed=0;

  std::cout<<"EXACT_V2_COMPILED_PREFIX"
           <<" B="<<BITS<<" P="<<P<<" W="<<W<<" k="<<k
           <<" full_count="<<full_total
           <<" merge_classes="<<merge_classes
           <<" transfer_classes="<<contract_classes
           <<" live_classes="<<LIVE.size()
           <<" horizon="<<H<<" shard="<<I<<"/"<<NS
           <<" lower="<<str128(L)<<" upper="<<str128(U)<<"\n";

#pragma omp parallel
  {
    unsigned long long lscan=0,lfb=0,lsb=0,lov=0;
    bool lsurv=false;u128 lwit=0;
    int lbest=0;u128 lbestseed=0;
#pragma omp for schedule(dynamic,32)
    for(size_t pi=0;pi<LIVE.size();++pi){
      const Prefix&pr=LIVE[pi];
      uint64_t delta=(uint64_t(pr.b)-(smlo&PMASK))&PMASK;
      uint64_t m=smlo+delta;
      if(m<smlo||m>smhi)continue;
      for(;;){
        ++lscan;
        u128 seed=(u128(m)<<k)-1;
        uint64_t A=m>>P;
        bool overflow=false;
        u128 x=0;
        if(u128(A)>(UMAX-pr.d)/pr.p3){
          overflow=true;
        }else{
          x=u128(A)*pr.p3+pr.d;
        }
        int t=W,descent=H+1;
        if(!overflow&&x<seed)descent=t;

        while(descent==H+1&&!overflow&&t+BITS<=H){
          const Block&bl=TAB[uint32_t(x)&BMASK];
          u128 lim=LIMIT[bl.qfinal];
          bool safe=(x<lim)||(x==lim&&bl.A<=REM[bl.qfinal]);
          u128 num=seed<<bl.tmin,den=P3B[bl.qmin];
          if(safe&&x*den>=num){x=(u128(bl.p3)*x+bl.A)>>BITS;t+=BITS;++lfb;continue;}
          ++lsb;
          for(int j=0;j<BITS&&t<H;++j){
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
          if(descent==H+1&&!lsurv){lsurv=true;lwit=seed;}
        }
        if(smhi-m<PMOD)break;
        m+=PMOD;
      }
    }
#pragma omp critical
    {
      scanned+=lscan;fastblocks+=lfb;slowblocks+=lsb;overflows+=lov;
      if(lbest>global_best){global_best=lbest;global_best_seed=lbestseed;}
      if(lsurv&&!any_survivor){any_survivor=true;witness=lwit;}
    }
  }

  std::cout<<"SCANNED "<<scanned<<" fast_blocks="<<fastblocks<<" slow_blocks="<<slowblocks<<" overflows="<<overflows<<"\n";
  std::cout<<"BEST first_descent_or_survival="<<global_best<<" seed="<<str128(global_best_seed)<<"\n";
  if(any_survivor){
    std::cout<<"SURVIVOR seed="<<str128(witness)<<" horizon="<<H<<"\nSTATUS SURVIVOR_FOUND\n";
  }else if(overflows){
    std::cout<<"STATUS OVERFLOW_REPLAY_REQUIRED\n";
  }else{
    std::cout<<"STATUS COMPILED_PREFIX_AND_SCAN_CLOSED\n";
  }
  return 0;
}
