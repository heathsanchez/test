// Exact staged p24 -> p28 -> p40 Collatz transfer veto.
//
// Retain the fast production scheduler:
//   p24 transfer -> whole-class coalescence -> q7 jumps.
//
// For each live non-coalesced p24 class, compile the 16 possible p28 suffix
// states once.  At each q7-live concrete candidate:
//   1) reject with one p28 state lookup if its four-bit suffix contracts;
//   2) otherwise extend only that exact state through bits 28..39 (12 cheap
//      transfer steps), rejecting if coefficient contraction appears;
//   3) only p40 survivors enter the expensive H5000 trajectory verifier.
//
// This is an exact theorem-guided veto, not a heuristic.

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
#ifndef COAL_BITS
#define COAL_BITS 16
#endif
static constexpr int B=BLOCK_BITS,S=PREFIX_BITS,C=COAL_BITS;
static constexpr int D28=28,D40=40;
static_assert(B>=4&&B<=20);
static_assert(S==24);
static_assert(C>=2&&C<=22);
static constexpr uint32_t BMASK=(uint32_t(1)<<B)-1;
static constexpr uint32_t RMOD=(uint32_t(1)<<S);
static constexpr uint32_t RMASK=RMOD-1;
static constexpr uint32_t CMOD=(uint32_t(1)<<C);
static constexpr uint32_t CMASK=CMOD-1;
static constexpr uint32_t PHASES28=1u<<(D28-S);
static const u128 UMAX=~u128(0);
static const u128 LIVE_L=u128(2075)<<60;
static const uint64_t FIRST_DANGEROUS=114208327604ULL;

static u128 parse128(const std::string&s){u128 x=0;for(char c:s)x=x*10+(c-'0');return x;}
static std::string str128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}

struct Block{uint32_t p3,A;uint8_t tmin,qmin,qfinal,pad;};
static std::array<uint32_t,B+1>P3;
static std::array<u128,B+1>LIMIT;
static std::array<uint32_t,B+1>REM;
static std::vector<Block>TAB;
static std::vector<uint8_t>RTYPE;
static std::vector<uint8_t>COAL_KILLED;
static std::array<u128,128>P3FULL{};

static constexpr uint32_t PRED_MOD=2187;
static std::array<uint8_t,PRED_MOD>PRED_KILLED{};
static std::array<uint16_t,PRED_MOD>PRED_JUMP0{},PRED_JUMP1{},PRED_LIVE0{},PRED_NEXTLIVE{};
static uint16_t PRED_STEP=0;

struct PrefixState{u128 d;uint8_t q;uint8_t live;};

static inline bool step_u128(u128&x){
  if(x&1){if(x>(UMAX-1)/3)return false;x=(3*x+1)>>1;}
  else x>>=1;
  return true;
}

static void init_powers(){
  P3FULL[0]=1;
  for(int i=1;i<128;++i){
    if(P3FULL[i-1]>UMAX/3)break;
    P3FULL[i]=P3FULL[i-1]*3;
  }
}

static void init_pred_q7(int k){
  auto mark=[](uint32_t mod,uint32_t residue){
    for(uint32_t r=residue;r<PRED_MOD;r+=mod)PRED_KILLED[r]=1;
  };
  mark(3,2);mark(9,4);mark(81,10);mark(729,433);mark(729,604);
  for(uint32_t r:{205u,325u,919u,991u,1000u,1090u,1171u,2170u})mark(2187,r);
  uint32_t n=0;for(uint8_t x:PRED_KILLED)n+=x;
  if(n!=1013){std::cerr<<"PRED_Q7_CENSUS_MISMATCH\n";std::exit(10);}
  uint32_t step=1;
  for(int i=0;i<k+S;++i)step=(step*2u)%PRED_MOD;
  PRED_STEP=(uint16_t)step;
  for(uint32_t r=0;r<PRED_MOD;++r){
    uint32_t x=r,d=0;
    while(PRED_KILLED[x]){
      x+=step;if(x>=PRED_MOD)x-=PRED_MOD;++d;
      if(d>PRED_MOD)std::exit(11);
    }
    PRED_JUMP0[r]=(uint16_t)d;PRED_LIVE0[r]=(uint16_t)x;
    x=r+step;if(x>=PRED_MOD)x-=PRED_MOD;d=1;
    while(PRED_KILLED[x]){
      x+=step;if(x>=PRED_MOD)x-=PRED_MOD;++d;
      if(d>PRED_MOD)std::exit(12);
    }
    PRED_JUMP1[r]=(uint16_t)d;PRED_NEXTLIVE[r]=(uint16_t)x;
  }
}

static inline void affine_step(u128&A,u128&Bv){
  if(A&1){std::cerr<<"AFFINE_PARITY_NOT_FIXED\n";std::exit(8);}
  if(Bv&1){A=(3*A)>>1;Bv=(3*Bv+1)>>1;}
  else{A>>=1;Bv>>=1;}
}
static void init_coalescence(int k){
  COAL_KILLED.assign(CMOD,0);
  uint64_t killed=0;
  for(uint32_t r=1;r<CMOD;r+=2){
    u128 nA=u128(1)<<(k+C),nB=(u128(1)<<k)*r-1;
    u128 pA=nA>>1,pB=(nB-1)>>1;
    bool merged=false;
    while(!(nA&1)){
      affine_step(nA,nB);
      if(nA==pA&&nB==pB){merged=true;break;}
      if(pA&1)break;
      affine_step(pA,pB);
    }
    if(merged){COAL_KILLED[r]=1;++killed;}
  }
  if(C==16&&killed!=17917){std::cerr<<"COALESCENCE_CENSUS_MISMATCH\n";std::exit(9);}
}

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

static void init_residue_sieve(int k,uint64_t&merge_classes,uint64_t&contract_classes,uint64_t&live_classes){
  const int W=k+S;
  if(!(k>=8&&k+D40<127&&uint64_t(k+D40)<FIRST_DANGEROUS)){
    std::cerr<<"PREFIX_SIEVE_PRECONDITION_FAILED\n";std::exit(4);
  }
  RTYPE.assign(RMOD,0);
  merge_classes=contract_classes=live_classes=0;
  const int merge_mod=(k&1)?3:1;
  for(uint32_t m=1;m<RMOD;m+=2){
    if(int(m&3u)==merge_mod){RTYPE[m]=0;++merge_classes;continue;}
    u128 x=(u128(m)<<k)-1;
    int q=0;bool contracted=false;
    for(int t=1;t<=W;++t){
      if(x&1){++q;x=(3*x+1)>>1;}else x>>=1;
      if(P3FULL[q]<(u128(1)<<t)){RTYPE[m]=1;++contract_classes;contracted=true;break;}
    }
    if(!contracted){RTYPE[m]=2;++live_classes;}
  }
}

// Compile all four-bit continuations from p24 to p28.  For a p24-live class,
// each returned state is exact for every concrete m having that 4-bit suffix.
static inline void build_p28_states(int k,uint32_t r,std::array<PrefixState,PHASES28>&out){
  const int W0=k+S;
  u128 x=(u128(r)<<k)-1;
  uint8_t q=0;
  for(int t=1;t<=W0;++t){
    if(x&1){++q;x=(3*x+1)>>1;}else x>>=1;
  }
  for(uint32_t suf=0;suf<PHASES28;++suf){
    u128 d=x;uint8_t q2=q;bool ok=true;
    for(int j=0;j<D28-S;++j){
      const int t=W0+j+1;
      const int bit=(suf>>j)&1u;
      u128 y=d+u128(bit)*P3FULL[q2];
      if(y&1){++q2;d=(3*y+1)>>1;}else d=y>>1;
      if(P3FULL[q2]<(u128(1)<<t)){ok=false;break;}
    }
    out[suf]={d,q2,uint8_t(ok)};
  }
}

// Continue one exact p28 state through the concrete bits 28..39.
static inline bool survives_to_p40(int k,const PrefixState&st,uint64_t m){
  u128 d=st.d;uint8_t q=st.q;
  const uint32_t suf=uint32_t((m>>D28)&((uint64_t(1)<<(D40-D28))-1));
  for(int j=0;j<D40-D28;++j){
    const int t=k+D28+j+1;
    const int bit=(suf>>j)&1u;
    u128 y=d+u128(bit)*P3FULL[q];
    if(y&1){++q;d=(3*y+1)>>1;}else d=y>>1;
    if(P3FULL[q]<(u128(1)<<t))return false;
  }
  return true;
}

static uint64_t count_residue(uint64_t lo,uint64_t hi,uint32_t r){
  if(lo>hi)return 0;
  uint64_t delta=(uint64_t(r)-(lo&RMASK))&RMASK;
  uint64_t first=lo+delta;
  if(first<lo||first>hi)return 0;
  return (hi-first)/RMOD+1;
}

int main(int argc,char**argv){
  if(argc!=7){std::cerr<<"usage: prog K H SHARDS IDX LOWER UPPER\n";return 2;}
  int k=std::stoi(argv[1]),H=std::stoi(argv[2]),NS=std::stoi(argv[3]),I=std::stoi(argv[4]);
  u128 L=parse128(argv[5]),U=parse128(argv[6]);
  if(!(8<=k&&0<=I&&I<NS&&L<=U&&L>=LIVE_L&&U<2*L+1)){std::cerr<<"BAD_ARGS_OR_DOMAIN\n";return 2;}

  init_powers();init_blocks();init_coalescence(k);init_pred_q7(k);
  uint64_t merge_classes,contract_classes,live_classes;
  init_residue_sieve(k,merge_classes,contract_classes,live_classes);

  u128 M=u128(1)<<k;
  u128 qmlo=(L+1+M-1)/M,qmhi=(U+1)/M;
  if(qmhi>u128(UINT64_MAX)){std::cerr<<"M_SPACE_EXCEEDS_U64\n";return 5;}
  uint64_t mlo=uint64_t(qmlo),mhi=uint64_t(qmhi);
  if((mlo&1)==0)++mlo;if((mhi&1)==0)--mhi;
  if(mhi<mlo){std::cout<<"STATUS LAZY_P40_VETO_SCAN_CLOSED\n";return 0;}

  uint64_t full_total=(mhi-mlo)/2+1;
  uint64_t ia=full_total*I/NS,ib=full_total*(I+1)/NS;
  uint64_t smlo=mlo+2*ia,smhi=(ib?mlo+2*(ib-1):mlo-2);

  uint64_t merge_seeds=0,contract_seeds=0,live_seeds=0;
  for(uint32_t r=1;r<RMOD;r+=2){
    uint64_t c=count_residue(mlo,mhi,r);
    if(RTYPE[r]==0)merge_seeds+=c;
    else if(RTYPE[r]==1)contract_seeds+=c;
    else live_seeds+=c;
  }
  if(merge_seeds+contract_seeds+live_seeds!=full_total){std::cerr<<"SIEVE_COUNT_MISMATCH\n";return 6;}

  u128 p3k=1;for(int i=0;i<k;++i)p3k*=3;
  bool any_survivor=false;u128 witness=0;
  unsigned long long scanned=0,coal_killed=0,pred_killed=0,p28_vetoed=0,p40_vetoed=0,fastblocks=0,slowblocks=0,overflows=0;
  int global_best=0;u128 global_best_seed=0;

  std::cout<<"EXACT_V2_LAZY_P40_VETO_SCAN B="<<B<<" S="<<S<<" D28="<<D28<<" D40="<<D40<<" C="<<C<<" k="<<k
           <<" full_count="<<full_total<<" merge_killed="<<merge_seeds
           <<" transfer_killed="<<contract_seeds<<" p24_live="<<live_seeds
           <<" residue_live_classes="<<live_classes
           <<" horizon="<<H<<" shard="<<I<<"/"<<NS
           <<" lower="<<str128(L)<<" upper="<<str128(U)<<"\n";

#pragma omp parallel
  {
    unsigned long long lscan=0,lcoal=0,lpred=0,lv28=0,lv40=0,lfb=0,lsb=0,lov=0;
    int lbest=0;u128 lbestseed=0,lwitness=0;bool lsurvivor=false;
#pragma omp for schedule(dynamic,64)
    for(uint32_t r=1;r<RMOD;r+=2){
      if(RTYPE[r]!=2)continue;
      uint64_t delta=(uint64_t(r)-(smlo&RMASK))&RMASK;
      uint64_t m=smlo+delta;
      if(m<smlo||m>smhi)continue;
      uint64_t class_count=(smhi-m)/RMOD+1;

      if(COAL_KILLED[r&CMASK]){lcoal+=class_count;continue;}

      std::array<PrefixState,PHASES28>states;
      build_p28_states(k,r,states);

      u128 seed0=(u128(m)<<k)-1;
      uint32_t rp=uint32_t(seed0%PRED_MOD);
      uint64_t positions=class_count;
      uint32_t d0=PRED_JUMP0[rp];
      if(uint64_t(d0)>=positions){lpred+=positions;continue;}
      lpred+=d0;positions-=d0;m+=uint64_t(d0)*RMOD;rp=PRED_LIVE0[rp];

      while(positions){
        const uint32_t phase=uint32_t((m>>S)&(PHASES28-1));
        const PrefixState&st=states[phase];
        if(!st.live){
          ++lv28;
        }else if(!survives_to_p40(k,st,m)){
          ++lv40;
        }else{
          const u128 seed=(u128(m)<<k)-1;
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
        }

        --positions;if(!positions)break;
        uint32_t d=PRED_JUMP1[rp];
        uint64_t killed_between=uint64_t(d)-1;
        if(killed_between>=positions){lpred+=positions;break;}
        lpred+=killed_between;positions-=killed_between;
        m+=uint64_t(d)*RMOD;rp=PRED_NEXTLIVE[rp];
      }
    }
#pragma omp critical
    {
      scanned+=lscan;coal_killed+=lcoal;pred_killed+=lpred;
      p28_vetoed+=lv28;p40_vetoed+=lv40;
      fastblocks+=lfb;slowblocks+=lsb;overflows+=lov;
      if(lbest>global_best){global_best=lbest;global_best_seed=lbestseed;}
      if(lsurvivor&&!any_survivor){any_survivor=true;witness=lwitness;}
    }
  }

  std::cout<<"LAZY_P40_COUNTS COALESCENCE_KILLED "<<coal_killed
           <<" PREDQ7_KILLED "<<pred_killed
           <<" P28_VETOED_AFTER_Q7 "<<p28_vetoed
           <<" P40_VETOED_AFTER_P28 "<<p40_vetoed
           <<" EXPLICIT "<<scanned<<"\n";
  std::cout<<"SCANNED "<<scanned<<" fast_blocks="<<fastblocks<<" slow_blocks="<<slowblocks<<" overflows="<<overflows<<"\n";
  std::cout<<"BEST first_descent_or_survival="<<global_best<<" seed="<<str128(global_best_seed)<<"\n";
  if(any_survivor){
    std::cout<<"SURVIVOR seed="<<str128(witness)<<" horizon="<<H<<"\nSTATUS SURVIVOR_FOUND\n";
  }else if(overflows){
    std::cout<<"STATUS OVERFLOW_REPLAY_REQUIRED\n";
  }else{
    std::cout<<"STATUS LAZY_P40_VETO_SCAN_CLOSED\n";
  }
  return 0;
}
