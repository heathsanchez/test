// Exact predecessor-sieved Collatz scanner using ctz run-length jumps.
//
// For odd x, let a=v2(x+1), x+1=2^a*m.
// Then a shortcut odd steps are exact in one jump:
//     T^a(x)=3^a*m-1.
// This quantity is even; let b=v2(T^a(x)). The following b even steps
// are pure halving. Odd steps strictly increase for x>1, so first descent
// can only occur inside the even run. We therefore inspect only those b
// halvings to locate the exact first-descent step.
//
// One m mod 4 class is closed by the independently verified lower-predecessor
// merge theorem. Rare u128 overflow emits the seed for big-int replay.

#include <omp.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>

using u128 = unsigned __int128;
static const u128 UMAX=~u128(0);
static constexpr int MAXA=80;
static std::array<u128,MAXA+1> P3;

static u128 parse128(const std::string&s){u128 x=0;for(char c:s)x=x*10+(c-'0');return x;}
static std::string str128(u128 x){if(!x)return"0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}

static void init_pow3(){
  P3[0]=1;
  for(int i=1;i<=MAXA;++i){
    if(P3[i-1]>UMAX/3){std::cerr<<"POW3_TABLE_OVERFLOW\n";std::exit(3);}
    P3[i]=P3[i-1]*3;
  }
}

static inline int ctz128(u128 x){
  if(!x)return 128;
  uint64_t lo=(uint64_t)x;
  if(lo)return __builtin_ctzll(lo);
  uint64_t hi=(uint64_t)(x>>64);
  return 64+__builtin_ctzll(hi);
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
  if(!(1<=k&&0<=I&&I<S&&L<=U&&U<2*L+1)){std::cerr<<"BAD_ARGS_OR_DOMAIN\n";return 2;}
  init_pow3();

  const u128 M=u128(1)<<k;
  uint64_t mlo=uint64_t((L+1+M-1)/M),mhi=uint64_t((U+1)/M);
  if((mlo&1)==0)++mlo;if((mhi&1)==0)--mhi;
  const int killed=(k&1)?3:1;
  const int survivor=(k&1)?1:3;

  if(mhi<mlo){
    std::cout<<"EXACT_V2_CTZ_SCAN k="<<k<<" full_count=0 survivor_count=0 horizon="<<H<<" shard="<<I<<"/"<<S<<"\n";
    std::cout<<"SCANNED 0 overflows=0\nSTATUS INDUCTIVE_HALF_CLOSED_AND_SURVIVORS_EXHAUSTED\n";
    return 0;
  }

  const uint64_t full_total=(mhi-mlo)/2+1;
  const uint64_t sfirst=first_congruent(mlo,survivor);
  const uint64_t slast=last_congruent(mhi,survivor);
  const uint64_t surv_total=sfirst<=slast?((slast-sfirst)/4+1):0;
  const uint64_t killed_total=full_total-surv_total;
  const uint64_t a=surv_total*I/S,b=surv_total*(I+1)/S;
  const uint64_t smlo=sfirst+4*a,smhi=(b?sfirst+4*(b-1):sfirst-4);

  bool any_survivor=false;u128 witness=0;
  unsigned long long scanned=0,odd_runs=0,even_steps=0,overflows=0;
  int global_best=0;u128 global_best_seed=0;

  std::cout<<"EXACT_V2_CTZ_SCAN k="<<k
           <<" full_count="<<full_total
           <<" survivor_count="<<surv_total
           <<" killed_count="<<killed_total
           <<" horizon="<<H<<" shard="<<I<<"/"<<S
           <<" threads="<<omp_get_max_threads()
           <<" lower="<<str128(L)<<" upper="<<str128(U)<<"\n";
  std::cout<<"MERGE_KILLED_MOD4 "<<killed<<" SURVIVOR_MOD4 "<<survivor<<"\n";

  if(a<b){
#pragma omp parallel
    {
      unsigned long long lscan=0,lruns=0,leven=0,lov=0;
      int lbest=0;u128 lbestseed=0,lwitness=0;bool lsurvivor=false;
#pragma omp for schedule(static)
      for(uint64_t m=smlo;m<=smhi;m+=4){
        ++lscan;
        const u128 seed=(u128(m)<<k)-1;
        u128 x=seed;
        int t=0,descent=H+1;
        bool overflow=false;

        while(descent==H+1 && t<H){
          // x may be even only at entry for degenerate controls; consume the
          // even run exactly and test each halving for the first descent.
          if(!(x&1)){
            int beta=ctz128(x);
            for(int j=0;j<beta && t<H;++j){
              x>>=1;++t;++leven;
              if(x<seed){descent=t;break;}
            }
            if(descent!=H+1||t>=H)break;
          }

          // Odd run: x+1 cannot overflow because live seeds/trajectories are
          // far below UINT128_MAX unless an earlier multiplication overflowed.
          if(x==UMAX){overflow=true;break;}
          u128 y=x+1;
          int alpha=ctz128(y);
          if(alpha<=0){std::cerr<<"CTZ_INVARIANT\n";std::abort();}
          if(alpha>MAXA){overflow=true;break;}
          if(t+alpha>H){
            // Every odd shortcut step strictly increases x>1, so no descent
            // occurs before H inside this partial odd run.
            t=H;
            break;
          }
          y>>=alpha;
          if(y>(UMAX+u128(0))/P3[alpha]){
            overflow=true;break;
          }
          // Avoid the UMAX expression corner explicitly.
          if(P3[alpha] && y>UMAX/P3[alpha]){overflow=true;break;}
          x=y*P3[alpha]-1;
          t+=alpha;++lruns;

          // x is even after a maximal odd run. Test the contraction one half
          // at a time only until first descent (beta is usually small).
          if(x==0){descent=t;break;}
          int beta=ctz128(x);
          for(int j=0;j<beta && t<H;++j){
            x>>=1;++t;++leven;
            if(x<seed){descent=t;break;}
          }
        }

        if(overflow){
          ++lov;
#pragma omp critical
          std::cout<<"OVERFLOW_SEED seed="<<str128(seed)<<" reached_after_t="<<t<<"\n";
          continue;
        }
        if(descent>lbest){lbest=descent;lbestseed=seed;}
        if(descent==H+1&&!lsurvivor){lsurvivor=true;lwitness=seed;}
      }
#pragma omp critical
      {
        scanned+=lscan;odd_runs+=lruns;even_steps+=leven;overflows+=lov;
        if(lbest>global_best){global_best=lbest;global_best_seed=lbestseed;}
        if(lsurvivor&&!any_survivor){any_survivor=true;witness=lwitness;}
      }
    }
  }

  std::cout<<"SCANNED "<<scanned<<" odd_runs="<<odd_runs<<" even_steps="<<even_steps<<" overflows="<<overflows<<"\n";
  std::cout<<"BEST first_descent_or_survival="<<global_best<<" seed="<<str128(global_best_seed)<<"\n";
  if(any_survivor){
    std::cout<<"SURVIVOR seed="<<str128(witness)<<" horizon="<<H<<"\nSTATUS SURVIVOR_FOUND\n";
  }else if(overflows){
    std::cout<<"STATUS OVERFLOW_REPLAY_REQUIRED\n";
  }else{
    std::cout<<"STATUS INDUCTIVE_HALF_CLOSED_AND_SURVIVORS_EXHAUSTED\n";
  }
  return 0;
}
