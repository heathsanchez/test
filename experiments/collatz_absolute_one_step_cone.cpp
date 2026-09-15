// Exact direct test of a K-INDEPENDENT bounded Collatz cone.
//
// For odd n > 1, scan only the first H shortcut iterates from n itself.
// At each y=T^t(n), close n if either:
//
//   (A) y < n,
//
// or, when y == 2 (mod 3),
//
//   (B) p=(2y-1)/3 is positive and p<n.
//
// In case (B), p is odd and T(p)=y, so by strong induction p reaches 1,
// hence y and then n reach 1.
//
// This test has NO K-step burn-in, no q14 bank, no affine preconditioning,
// no reverse tree, and no search branching.  K is used only to enumerate a
// finite bit-length shell for falsification/certification.
//
// If one fixed H could be proved sufficient for every odd n, Collatz would
// follow immediately from strong induction.  Finite shell success is NOT that
// theorem; it is evidence about the candidate bounded operator.

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>

using u128=unsigned __int128;

static bool Tchecked(u128 n,u128& out){
  if((n&1)==0){out=n/2;return true;}
  const u128 MAX=~u128(0);
  if(n>(MAX-1)/3)return false;
  out=(3*n+1)/2;
  return true;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: absolute_cone K H\n";return 2;}
  const int K=std::stoi(argv[1]);
  const int H=std::stoi(argv[2]);
  if(K<2||K>40||H<0||H>4096)return 2;

  const uint64_t L=UINT64_C(1)<<K;
  const uint64_t U=UINT64_C(1)<<(K+1);

  uint64_t checked=0,direct=0,cone=0,hard=0,overflow=0;
  uint64_t max_t=0,max_t_seed=0;
  uint64_t cone_controls=0;

  for(uint64_t n=L|1;n<U;n+=2){
    u128 y=n;
    bool closed=false,ok=true;

    for(int t=0;t<=H;++t){
      if(t>0){
        u128 z;
        if(!Tchecked(y,z)){ok=false;break;}
        y=z;
      }

      if(y<n){
        ++direct;
        if(uint64_t(t)>max_t){max_t=t;max_t_seed=n;}
        closed=true;
        break;
      }

      if(y%3==2){
        const u128 p=(2*y-1)/3;
        if(p>0 && p<n){
          // Independent exact replay of the single reverse-odd edge.
          u128 z;
          if(!Tchecked(p,z) || z!=y){
            std::cerr<<"ABSOLUTE_CONE_REPLAY_FAIL n="<<n<<" t="<<t<<"\n";
            return 5;
          }
          ++cone;++cone_controls;
          if(uint64_t(t)>max_t){max_t=t;max_t_seed=n;}
          closed=true;
          break;
        }
      }
    }

    if(!ok){++overflow;continue;}
    if(!closed)++hard;
    ++checked;
  }

  std::cout<<"ABSOLUTE_ONE_STEP_CONE_RESULT"
           <<" K="<<K
           <<" H="<<H
           <<" checked="<<checked
           <<" direct="<<direct
           <<" cone="<<cone
           <<" hard="<<hard
           <<" overflow="<<overflow
           <<" max_t="<<max_t
           <<" max_t_seed="<<max_t_seed
           <<" cone_controls="<<cone_controls<<"\n";

  if(overflow){
    std::cerr<<"ABSOLUTE_ONE_STEP_CONE_OVERFLOW\n";
    return 7;
  }
  std::cout<<"VERIFIED_ABSOLUTE_ONE_STEP_CONE_SHELL\n";
  return 0;
}
