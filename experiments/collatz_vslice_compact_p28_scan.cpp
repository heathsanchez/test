// Compact exact p28 Collatz production scanner.
//
// Instead of materializing every live p28 residue, retain each live p24 base
// residue together with its exact 16-bit future-consequence mask for the four
// added suffix bits.  Equal suffix masks are shared consequence languages.
//
// For concrete m values in one p24 class, the four high suffix bits cycle with
// period 16.  q7 predecessor membership cycles with period 2187.  Because the
// periods are coprime, compile their conjunction into a tiny exact jump
// schedule of period 16*2187 for each distinct consequence mask.
//
// Result: same p28 theorem, same q7 theorem, same exact trajectory verifier,
// but no 19M-47M live-p28 residue vector and no seedwise visits to rejected
// p28/q7 phases.

#include <omp.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

using u128=unsigned __int128;
#ifndef BLOCK_BITS
#define BLOCK_BITS 10
#endif
#ifndef BASE_BITS
#define BASE_BITS 24
#endif
#ifndef DEEP_BITS
#define DEEP_BITS 28
#endif
#ifndef COAL_BITS
#define COAL_BITS 16
#endif

static constexpr int B=BLOCK_BITS,S=BASE_BITS,D=DEEP_BITS,C=COAL_BITS;
static_assert(B>=4&&B<=20);
static_assert(S==24);
static_assert(D==28);
static_assert(C>=2&&C<=22);
static constexpr uint32_t BMASK=(uint32_t(1)<<B)-1;
static constexpr uint32_t SMOD=(uint32_t(1)<<S);
static constexpr uint32_t SMASK=SMOD-1;
static constexpr uint32_t CMOD=(uint32_t(1)<<C);
static constexpr uint32_t CMASK=CMOD-1;
static constexpr uint32_t PRED_MOD=2187;
static constexpr uint32_t PHASES=1u<<(D-S);
static constexpr uint32_t COMBINED_PERIOD=PHASES*PRED_MOD;
static const u128 UMAX=~u128(0);
static const u128 LIVE_L=u128(2075)<<60;
static const uint64_t FIRST_DANGEROUS=114208327604ULL;

static u128 parse128(const std::string&s){u128 x=0;for(char c:s)x=x*10+(c-'0');return x;}
static std::string str128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}

struct Block{uint32_t p3,A;uint8_t tmin,qmin,qfinal,pad;};
static std::array<uint32_t,B+1>P3B;
static std::array<u128,B+1>LIMIT;
static std::array<uint32_t,B+1>REM;
static std::vector<Block>TAB;
static std::vector<uint8_t>COAL_KILLED;
static std::array<uint8_t,PRED_MOD>PRED_KILLED{};

struct BaseClass{uint32_t r;uint16_t sid;};
struct Schedule{uint16_t mask;std::vector<uint16_t>jump0;};
static std::vector<BaseClass>BASES;
static std::vector<Schedule>SCHEDULES;
static uint64_t DEEP_CLASS_CENSUS=0;
static uint32_t QSTEP=0;

static inline bool step_u128(u128&x){
  if(x&1){if(x>(UMAX-1)/3)return false;x=(3*x+1)>>1;}
  else x>>=1;
  return true;
}

static void init_blocks(){
  P3B[0]=1;
  for(int i=1;i<=B;++i)P3B[i]=P3B[i-1]*3u;
  for(int q=0;q<=B;++q){LIMIT[q]=UMAX/u128(P3B[q]);REM[q]=uint32_t(UMAX%u128(P3B[q]));}
  TAB.resize(uint32_t(1)<<B);
  for(uint32_t r=0;r<(uint32_t(1)<<B);++r){
    uint32_t y=r,A=0,p3=1;int q=0,best_t=1,best_q=0;bool have=false;
    for(int t=0;t<B;++t){
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
  if(C==16&&killed!=17917){std::cerr<<"COALESCENCE_CENSUS_MISMATCH got="<<killed<<"\n";std::exit(9);}
}

static void init_q7(int k){
  auto mark=[](uint32_t mod,uint32_t residue){
    for(uint32_t r=residue;r<PRED_MOD;r+=mod)PRED_KILLED[r]=1;
  };
  mark(3,2);mark(9,4);mark(81,10);mark(729,433);mark(729,604);
  for(uint32_t r:{205u,325u,919u,991u,1000u,1090u,1171u,2170u})mark(2187,r);
  uint32_t n=0;for(uint8_t x:PRED_KILLED)n+=x;
  if(n!=1013){std::cerr<<"PRED_Q7_CENSUS_MISMATCH\n";std::exit(10);}
  QSTEP=1;
  for(int i=0;i<k+S;++i)QSTEP=(QSTEP*2u)%PRED_MOD;
}

static uint64_t count_mask_positions(uint32_t phase,uint64_t n,uint16_t mask){
  uint64_t ans=(n/PHASES)*uint64_t(__builtin_popcount(unsigned(mask)));
  uint32_t rem=uint32_t(n%PHASES);
  for(uint32_t j=0;j<rem;++j)ans+=(mask>>((phase+j)&(PHASES-1)))&1u;
  return ans;
}

static void build_schedule(uint16_t mask,Schedule&out){
  out.mask=mask;
  out.jump0.assign(COMBINED_PERIOD,0);

  std::vector<uint32_t> keys(COMBINED_PERIOD);
  std::vector<uint8_t> accepted(COMBINED_PERIOD);
  uint32_t phase=0,rp=0;
  for(uint32_t i=0;i<COMBINED_PERIOD;++i){
    uint32_t key=phase*PRED_MOD+rp;
    keys[i]=key;
    accepted[i]=uint8_t(((mask>>phase)&1u) && !PRED_KILLED[rp]);
    phase=(phase+1)&(PHASES-1);
    rp+=QSTEP;if(rp>=PRED_MOD)rp-=PRED_MOD;
  }
  std::vector<uint32_t>A;
  A.reserve(COMBINED_PERIOD);
  for(uint32_t i=0;i<COMBINED_PERIOD;++i)if(accepted[i])A.push_back(i);
  if(A.empty()){std::cerr<<"EMPTY_COMBINED_SCHEDULE mask="<<mask<<"\n";std::exit(14);}

  size_t j=0;
  for(uint32_t i=0;i<COMBINED_PERIOD;++i){
    while(j<A.size()&&A[j]<i)++j;
    uint32_t d=(j<A.size())?(A[j]-i):(COMBINED_PERIOD-i+A[0]);
    if(d>=65536){std::cerr<<"JUMP_OVERFLOW\n";std::exit(15);}
    out.jump0[keys[i]]=uint16_t(d);
  }
}

static void init_compact_prefix(int k){
  const int W0=k+S,W1=k+D;
  if(!(k>=8&&W1<127&&uint64_t(W1)<FIRST_DANGEROUS)){std::cerr<<"COMPACT_PREFIX_PRECONDITION\n";std::exit(4);}
  std::array<u128,128>P3{};
  P3[0]=1;for(int i=1;i<128;++i){if(P3[i-1]>UMAX/3)break;P3[i]=P3[i-1]*3;}

  struct Raw{uint32_t r;uint16_t mask;};
  std::vector<Raw>raw;
  const int killed_mod4=(k&1)?3:1;
  uint64_t base_live=0,deep_census=0;

  for(uint32_t r=1;r<SMOD;r+=2){
    if(int(r&3u)==killed_mod4)continue;
    u128 x=(u128(r)<<k)-1;
    uint8_t q=0;bool alive=true;
    for(int t=1;t<=W0;++t){
      if(x&1){++q;x=(3*x+1)>>1;}else x>>=1;
      if(P3[q]<(u128(1)<<t)){alive=false;break;}
    }
    if(!alive)continue;
    ++base_live;

    uint16_t mask=0;
    for(uint32_t suf=0;suf<PHASES;++suf){
      u128 d=x;uint8_t q2=q;bool ok=true;
      for(int j=0;j<D-S;++j){
        int t=W0+j+1;
        int bit=(suf>>j)&1u;
        u128 y=d+u128(bit)*P3[q2];
        if(y&1){++q2;d=(3*y+1)>>1;}else d=y>>1;
        if(P3[q2]<(u128(1)<<t)){ok=false;break;}
      }
      if(ok)mask|=uint16_t(1u<<suf);
    }
    if(mask){raw.push_back({r,mask});deep_census+=__builtin_popcount(unsigned(mask));}
  }

  uint64_t expect=0;
  if(k==15)expect=46777401ULL;
  if(k==10)expect=28311176ULL;
  if(k==8)expect=19085390ULL;
  if(expect&&deep_census!=expect){
    std::cerr<<"COMPACT_P28_CENSUS_MISMATCH got="<<deep_census<<" expected="<<expect<<"\n";std::exit(13);
  }
  DEEP_CLASS_CENSUS=deep_census;

  std::unordered_map<uint16_t,uint16_t>sid;
  BASES.clear();SCHEDULES.clear();
  BASES.reserve(raw.size());
  for(const auto&z:raw){
    auto it=sid.find(z.mask);
    uint16_t id;
    if(it==sid.end()){
      id=uint16_t(SCHEDULES.size());
      sid.emplace(z.mask,id);
      SCHEDULES.push_back(Schedule{});
      build_schedule(z.mask,SCHEDULES.back());
    }else id=it->second;
    BASES.push_back({z.r,id});
  }

  std::cout<<"COMPACT_P28_LANGUAGE K="<<k
           <<" p24_live_classes="<<base_live
           <<" p24_bases_with_p28_future="<<BASES.size()
           <<" p28_live_classes="<<DEEP_CLASS_CENSUS
           <<" distinct_future_masks="<<SCHEDULES.size()
           <<" combined_period="<<COMBINED_PERIOD<<"\n";
}

int main(int argc,char**argv){
  if(argc!=7){std::cerr<<"usage: prog K H SHARDS IDX LOWER UPPER\n";return 2;}
  int k=std::stoi(argv[1]),H=std::stoi(argv[2]),NS=std::stoi(argv[3]),I=std::stoi(argv[4]);
  u128 L=parse128(argv[5]),U=parse128(argv[6]);
  if(!(8<=k&&0<=I&&I<NS&&L<=U&&L>=LIVE_L&&U<2*L+1)){std::cerr<<"BAD_ARGS_OR_DOMAIN\n";return 2;}

  init_blocks();init_coalescence(k);init_q7(k);init_compact_prefix(k);

  u128 M=u128(1)<<k;
  u128 qmlo=(L+1+M-1)/M,qmhi=(U+1)/M;
  if(qmhi>u128(UINT64_MAX)){std::cerr<<"M_SPACE_EXCEEDS_U64\n";return 5;}
  uint64_t mlo=uint64_t(qmlo),mhi=uint64_t(qmhi);
  if((mlo&1)==0)++mlo;if((mhi&1)==0)--mhi;
  if(mhi<mlo){std::cout<<"STATUS COMPACT_P28_COAL_PREDQ7_SCAN_CLOSED\n";return 0;}

  uint64_t full_total=(mhi-mlo)/2+1;
  uint64_t ia=full_total*I/NS,ib=full_total*(I+1)/NS;
  uint64_t smlo=mlo+2*ia,smhi=(ib?mlo+2*(ib-1):mlo-2);

  u128 p3k=1;for(int i=0;i<k;++i)p3k*=3;
  bool any_survivor=false;u128 witness=0;
  unsigned long long deep_live=0,scanned=0,coal_killed=0,pred_killed=0,fastblocks=0,slowblocks=0,overflows=0;
  int global_best=0;u128 global_best_seed=0;

  std::cout<<"EXACT_V2_COMPACT_P28_SCAN B="<<B<<" S="<<S<<" D="<<D<<" C="<<C<<" k="<<k
           <<" full_count="<<full_total<<" live_residue_classes="<<DEEP_CLASS_CENSUS
           <<" future_masks="<<SCHEDULES.size()
           <<" horizon="<<H<<" shard="<<I<<"/"<<NS
           <<" lower="<<str128(L)<<" upper="<<str128(U)<<"\n";

#pragma omp parallel
  {
    unsigned long long ldeep=0,lscan=0,lcoal=0,lpred=0,lfb=0,lsb=0,lov=0;
    int lbest=0;u128 lbestseed=0,lwitness=0;bool lsurvivor=false;
#pragma omp for schedule(dynamic,64)
    for(size_t bi=0;bi<BASES.size();++bi){
      const BaseClass&bc=BASES[bi];
      const uint32_t r=bc.r;
      const Schedule&sch=SCHEDULES[bc.sid];
      uint64_t delta=(uint64_t(r)-(smlo&SMASK))&SMASK;
      uint64_t m=smlo+delta;
      if(m<smlo||m>smhi)continue;
      uint64_t positions=(smhi-m)/SMOD+1;
      const uint32_t phase0=uint32_t((m>>S)&(PHASES-1));
      const uint64_t dlive=count_mask_positions(phase0,positions,sch.mask);
      ldeep+=dlive;
      if(!dlive)continue;

      if(COAL_KILLED[r&CMASK]){lcoal+=dlive;continue;}

      uint32_t phase=phase0;
      uint32_t rp=uint32_t(((u128(m)<<k)-1)%PRED_MOD);
      uint64_t explicit_here=0;

      while(positions){
        uint32_t key=phase*PRED_MOD+rp;
        uint32_t d=sch.jump0[key];
        if(uint64_t(d)>=positions)break;
        if(d){
          m+=uint64_t(d)*SMOD;
          positions-=d;
          phase=(phase+d)&(PHASES-1);
          rp=(rp+(uint64_t(d)*QSTEP)%PRED_MOD)%PRED_MOD;
        }

        // By construction this position is p28-live and q7-live.
        const u128 seed=(u128(m)<<k)-1;
        ++lscan;++explicit_here;
        u128 x=(p3k*u128(m)-1)>>1;
        int t=k+1,descent=H+1;bool overflow=false;
        if(x<seed)descent=t;

        while(descent==H+1&&!overflow&&t+B<=H){
          const Block&bl=TAB[uint32_t(x)&BMASK];
          u128 lim=LIMIT[bl.qfinal];
          bool safe=(x<lim)||(x==lim&&bl.A<=REM[bl.qfinal]);
          u128 num=seed<<bl.tmin,den=P3B[bl.qmin];
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

        --positions;
        if(!positions)break;
        m+=SMOD;
        phase=(phase+1)&(PHASES-1);
        rp+=QSTEP;if(rp>=PRED_MOD)rp-=PRED_MOD;
      }
      lpred+=dlive-explicit_here;
    }
#pragma omp critical
    {
      deep_live+=ldeep;scanned+=lscan;coal_killed+=lcoal;pred_killed+=lpred;
      fastblocks+=lfb;slowblocks+=lsb;overflows+=lov;
      if(lbest>global_best){global_best=lbest;global_best_seed=lbestseed;}
      if(lsurvivor&&!any_survivor){any_survivor=true;witness=lwitness;}
    }
  }

  std::cout<<"COMPACT_P28_LIVE "<<deep_live
           <<" COALESCENCE_KILLED "<<coal_killed
           <<" PREDQ7_KILLED "<<pred_killed
           <<" EXPLICIT "<<scanned<<"\n";
  std::cout<<"SCANNED "<<scanned<<" fast_blocks="<<fastblocks<<" slow_blocks="<<slowblocks<<" overflows="<<overflows<<"\n";
  std::cout<<"BEST first_descent_or_survival="<<global_best<<" seed="<<str128(global_best_seed)<<"\n";
  if(any_survivor){
    std::cout<<"SURVIVOR seed="<<str128(witness)<<" horizon="<<H<<"\nSTATUS SURVIVOR_FOUND\n";
  }else if(overflows){
    std::cout<<"STATUS OVERFLOW_REPLAY_REQUIRED\n";
  }else{
    std::cout<<"STATUS COMPACT_P28_COAL_PREDQ7_SCAN_CLOSED\n";
  }
  return 0;
}
