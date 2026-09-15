// Exact valuation-slice scanner with two verifier-gated sieves:
//
// 1. Lower-predecessor merge:
//    n=2^K m-1, killed m mod4 class satisfies
//    T^(K+2)(n)=T^(K+1)((n-1)/2), and U<2L+1 puts that predecessor below L.
//
// 2. Transfer-prefix contraction:
//    the first W=K+S parity decisions depend only on n mod 2^W,
//    equivalently m mod 2^S. If 3^q < 2^t at any prefix t<=W,
//    the certified transfer theorem says every live n>=L descends there
//    because W << 114208327604.
//
// Only residue classes surviving both exact sieves are seedwise scanned.
// Intended for K>=8 so m fits uint64 on the current 72-bit interval.

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
#ifndef PREFIX_BITS
#define PREFIX_BITS 20
#endif
#ifndef COAL_BITS
#define COAL_BITS 16
#endif
static constexpr int B=BLOCK_BITS;
static constexpr int S=PREFIX_BITS;
static constexpr int C=COAL_BITS;
static_assert(B>=4 && B<=20);
static_assert(S>=2 && S<=24);
static_assert(C>=2 && C<=22);
static constexpr uint32_t BMASK=(uint32_t(1)<<B)-1;
static constexpr uint32_t RMOD=(uint32_t(1)<<S);
static constexpr uint32_t RMASK=RMOD-1;
static constexpr uint32_t CMOD=(uint32_t(1)<<C);
static constexpr uint32_t CMASK=CMOD-1;
static const u128 UMAX=~u128(0);
static const u128 LIVE_L=u128(2075) << 60;
static const uint64_t FIRST_DANGEROUS=114208327604ULL;

static u128 parse128(const std::string& s){u128 x=0;for(char c:s)x=x*10+(c-'0');return x;}
static std::string str128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}

struct Block{uint32_t p3,A;uint8_t tmin,qmin,qfinal,pad;};
static std::array<uint32_t,B+1>P3;
static std::array<u128,B+1>LIMIT;
static std::array<uint32_t,B+1>REM;
static std::vector<Block>TAB;

// 0=merge killed, 1=transfer-contraction killed, 2=live explicit scan.
static std::vector<uint8_t>RTYPE;

// Exact cross-valuation coalescence table.  For m=2^C z+r,
// n=2^K m-1 and p=(n-1)/2.  While the affine z-coefficient is even,
// shortcut parity is deterministic.  A class is closed when
// T^t(n(z)) == T^(t-1)(p(z)) as affine functions.
static std::vector<uint64_t>COAL_KILLED;

static inline bool coal_get(uint32_t r){
  return (COAL_KILLED[r>>6] >> (r&63)) & uint64_t(1);
}
static inline void coal_set(uint32_t r){
  COAL_KILLED[r>>6] |= uint64_t(1) << (r&63);
}

static inline void affine_step(u128 &A,u128 &B){
  if(A&1){std::cerr<<"AFFINE_PARITY_NOT_FIXED\n";std::exit(8);}
  if(B&1){A=(3*A)>>1;B=(3*B+1)>>1;}
  else{A>>=1;B>>=1;}
}

static void init_coalescence_sieve(int k){
  COAL_KILLED.assign((CMOD+63)/64,0);
  uint64_t killed=0;
  for(uint32_t r=1;r<CMOD;r+=2){
    u128 nA=u128(1)<<(k+C);
    u128 nB=(u128(1)<<k)*r-1;
    u128 pA=nA>>1;
    u128 pB=(nB-1)>>1;
    bool merged=false;

    while(!(nA&1)){
      affine_step(nA,nB); // n is now one deterministic step ahead of p.
      if(nA==pA && nB==pB){merged=true;break;}
      if(pA&1)break;
      affine_step(pA,pB);
    }
    if(merged){coal_set(r);++killed;}
  }

  // Exact reference census independently checked in
  // experiments/collatz_predecessor_coalescence.py.
  if(C==16 && killed!=17917){
    std::cerr<<"COALESCENCE_CENSUS_MISMATCH got="<<killed<<"\n";std::exit(9);
  }
  std::cout<<"COALESCENCE_BITSET_TABLE"
           <<" K="<<k<<" C="<<C
           <<" killed_classes="<<killed
           <<" odd_classes="<<(CMOD/2)
           <<" fraction="<<(double(killed)/double(CMOD/2))
           <<" table_bytes="<<(COAL_KILLED.size()*sizeof(uint64_t))<<"\n";
}

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
      const bool odd=y&1u;
      if(odd){y=(3u*y+1u)>>1;A=3u*A+(1u<<t);p3*=3u;++q;}else y>>=1;
      const int tt=t+1;
      if(!have){best_t=tt;best_q=q;have=true;}
      else{
        const uint64_t lhs=uint64_t(P3[q])<<best_t;
        const uint64_t rhs=uint64_t(P3[best_q])<<tt;
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

static void init_residue_sieve(int k,
  uint64_t &merge_classes,uint64_t &contract_classes,uint64_t &live_classes){
  const int W=k+S;
  if(!(k>=8 && W<127 && uint64_t(W)<FIRST_DANGEROUS)){
    std::cerr<<"PREFIX_SIEVE_PRECONDITION_FAILED\n";std::exit(4);
  }
  std::vector<u128> pow3(W+1);
  pow3[0]=1;
  for(int i=1;i<=W;++i)pow3[i]=pow3[i-1]*3;

  RTYPE.assign(RMOD,0);
  merge_classes=contract_classes=live_classes=0;
  const int merge_mod=(k&1)?3:1;

  for(uint32_t m=1;m<RMOD;m+=2){
    if(int(m&3u)==merge_mod){
      RTYPE[m]=0;++merge_classes;continue;
    }

    u128 x=(u128(m)<<k)-1;
    int q=0;
    bool contracted=false;
    for(int t=1;t<=W;++t){
      if(x&1){++q;x=(3*x+1)>>1;}else x>>=1;
      if(pow3[q] < (u128(1)<<t)){
        RTYPE[m]=1;++contract_classes;contracted=true;break;
      }
    }
    if(!contracted){RTYPE[m]=2;++live_classes;}
  }
}

static uint64_t count_residue(uint64_t lo,uint64_t hi,uint32_t r){
  if(lo>hi)return 0;
  const uint64_t delta=(uint64_t(r)-(lo&RMASK))&RMASK;
  const uint64_t first=lo+delta;
  if(first<lo || first>hi)return 0;
  return (hi-first)/RMOD+1;
}

int main(int argc,char**argv){
  if(argc!=7){std::cerr<<"usage: prog K H SHARDS IDX LOWER UPPER\n";return 2;}
  const int k=std::stoi(argv[1]),H=std::stoi(argv[2]),NS=std::stoi(argv[3]),I=std::stoi(argv[4]);
  const u128 L=parse128(argv[5]),U=parse128(argv[6]);
  if(!(8<=k && 0<=I&&I<NS&&L<=U&&L>=LIVE_L&&U<2*L+1)){std::cerr<<"BAD_ARGS_OR_DOMAIN\n";return 2;}

  init_blocks();
  init_coalescence_sieve(k);
  uint64_t merge_classes,contract_classes,live_classes;
  init_residue_sieve(k,merge_classes,contract_classes,live_classes);

  const u128 M=u128(1)<<k;
  const u128 qmlo=(L+1+M-1)/M, qmhi=(U+1)/M;
  if(qmhi>u128(UINT64_MAX)){std::cerr<<"M_SPACE_EXCEEDS_U64\n";return 5;}
  uint64_t mlo=uint64_t(qmlo),mhi=uint64_t(qmhi);
  if((mlo&1)==0)++mlo;if((mhi&1)==0)--mhi;
  if(mhi<mlo){std::cout<<"STATUS PREFIX_COAL_MOD9_SIEVE_AND_SCAN_CLOSED\n";return 0;}

  const uint64_t full_total=(mhi-mlo)/2+1;
  const uint64_t ia=full_total*I/NS, ib=full_total*(I+1)/NS;
  const uint64_t smlo=mlo+2*ia, smhi=(ib?mlo+2*(ib-1):mlo-2);

  // Exact whole-interval counts by residue type.
  uint64_t merge_seeds=0,contract_seeds=0,live_seeds=0;
  for(uint32_t r=1;r<RMOD;r+=2){
    const uint64_t c=count_residue(mlo,mhi,r);
    if(RTYPE[r]==0)merge_seeds+=c;
    else if(RTYPE[r]==1)contract_seeds+=c;
    else live_seeds+=c;
  }
  if(merge_seeds+contract_seeds+live_seeds!=full_total){
    std::cerr<<"SIEVE_COUNT_MISMATCH\n";return 6;
  }

  u128 p3k=1;for(int i=0;i<k;++i)p3k*=3;
  bool any_survivor=false;u128 witness=0;
  unsigned long long scanned=0,coal_killed=0,mod9_killed=0,fastblocks=0,slowblocks=0,overflows=0;
  int global_best=0;u128 global_best_seed=0;

  std::cout<<"EXACT_V2_PREFIX_COAL_MOD9_SCAN B="<<B<<" S="<<S<<" k="<<k
           <<" full_count="<<full_total
           <<" merge_killed="<<merge_seeds
           <<" transfer_killed="<<contract_seeds
           <<" explicit_count="<<live_seeds
           <<" residue_merge_classes="<<merge_classes
           <<" residue_transfer_classes="<<contract_classes
           <<" residue_live_classes="<<live_classes
           <<" horizon="<<H<<" shard="<<I<<"/"<<NS
           <<" lower="<<str128(L)<<" upper="<<str128(U)<<"\n";

#pragma omp parallel
  {
    unsigned long long lscan=0,lcoal=0,lmod9=0,lfb=0,lsb=0,lov=0;
    int lbest=0;u128 lbestseed=0,lwitness=0;bool lsurvivor=false;
#pragma omp for schedule(dynamic,64)
    for(uint32_t r=1;r<RMOD;r+=2){
      if(RTYPE[r]!=2)continue;
      const uint64_t delta=(uint64_t(r)-(smlo&RMASK))&RMASK;
      uint64_t m=smlo+delta;
      if(m<smlo||m>smhi)continue;
      for(;;){
        const u128 seed=(u128(m)<<k)-1;
        if(coal_get(uint32_t(m)&CMASK)){
          ++lcoal;
          if(smhi-m<RMOD)break;
          m+=RMOD;
          continue;
        }
        const unsigned r9=(unsigned)(seed%9);
        if(r9==2||r9==4||r9==5||r9==8){
          ++lmod9;
          if(smhi-m<RMOD)break;
          m+=RMOD;
          continue;
        }
        ++lscan;
        u128 x=(p3k*u128(m)-1)>>1;
        int t=k+1,descent=H+1;bool overflow=false;
        if(x<seed)descent=t;

        while(descent==H+1&&!overflow&&t+B<=H){
          const Block&bl=TAB[uint32_t(x)&BMASK];
          const u128 lim=LIMIT[bl.qfinal];
          const bool safe=(x<lim)||(x==lim&&bl.A<=REM[bl.qfinal]);
          const u128 num=seed<<bl.tmin,den=P3[bl.qmin];
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

        if(smhi-m<RMOD)break;
        m+=RMOD;
      }
    }
#pragma omp critical
    {
      scanned+=lscan;coal_killed+=lcoal;mod9_killed+=lmod9;fastblocks+=lfb;slowblocks+=lsb;overflows+=lov;
      if(lbest>global_best){global_best=lbest;global_best_seed=lbestseed;}
      if(lsurvivor&&!any_survivor){any_survivor=true;witness=lwitness;}
    }
  }

  std::cout<<"COALESCENCE_EXTRA_KILLED "<<coal_killed
           <<" MOD9_KILLED_AFTER_COALESCENCE "<<mod9_killed
           <<" EXPLICIT "<<scanned<<"\n";
  std::cout<<"SCANNED "<<scanned<<" fast_blocks="<<fastblocks
           <<" slow_blocks="<<slowblocks<<" overflows="<<overflows<<"\n";
  std::cout<<"BEST first_descent_or_survival="<<global_best<<" seed="<<str128(global_best_seed)<<"\n";
  if(any_survivor){
    std::cout<<"SURVIVOR seed="<<str128(witness)<<" horizon="<<H<<"\nSTATUS SURVIVOR_FOUND\n";
  }else if(overflows){
    std::cout<<"STATUS OVERFLOW_REPLAY_REQUIRED\n";
  }else{
    std::cout<<"STATUS PREFIX_COAL_MOD9_SIEVE_AND_SCAN_CLOSED\n";
  }
  return 0;
}
