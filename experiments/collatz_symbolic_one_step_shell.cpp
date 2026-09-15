// Exact symbolic shell closure for the one-step Collatz cone.
//
// Goal: certify all odd n in the bit shell [2^K,2^(K+1)) without enumerating
// each n.
//
// At depth t, a state (b,c,d) represents every shell integer
//
//   n = A*2^t + b
//
// in its current residue family, with the exact affine identity
//
//   T^t(n) = A*3^c + d.
//
// For t<=K, the shell induces the A interval
//
//   2^(K-t) <= A <= 2^(K+1-t)-1.
//
// We close the whole state if every A in that interval satisfies either
//
//   y < n
//
// or, uniformly when y == 2 (mod 3),
//
//   p=(2y-1)/3 < n.
//
// Both are linear inequalities in A, so endpoint checking is exact.
// Otherwise the state splits by the next binary residue bit.
//
// At t=K the shell parameter is exactly A=1.  The K->K+1 transition therefore
// has only high bit e=1, and thereafter A=0 forever: each remaining state is
// one concrete shell integer and follows one deterministic trajectory.
//
// This is an exact symbolic verifier, not a probabilistic or asymptotic test.
// cpp_int is used for trajectory/intercept arithmetic.

#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using Big=boost::multiprecision::cpp_int;

struct State{
  uint64_t b;
  Big d;
  uint32_t c;
};

static inline Big Tbig(Big n){
  if((n&1)!=0){n=3*n+1;n/=2;return n;}
  n/=2;return n;
}

static Big pow2(int e){ return Big(1)<<e; }

static bool max_negative_linear(
    const Big& coef,const Big& constant,
    const Big& amin,const Big& amax){
  const Big& a = (coef>=0)?amax:amin;
  return coef*a+constant < 0;
}

static bool uniform_closed(
    const State& s,int t,int K,
    const std::vector<Big>& p3){
  Big amin,amax;
  if(t<=K){
    amin=pow2(K-t);
    amax=pow2(K+1-t)-1;
  }else{
    amin=0;amax=0;
  }

  const Big M=pow2(t);
  const Big B=s.b;
  const Big P=p3[s.c];

  // y-n = A(3^c-2^t)+(d-b)
  if(max_negative_linear(P-M,s.d-B,amin,amax))
    return true;

  // One-step inverse-odd cone requires y == 2 mod 3 for every represented A.
  bool mod2=false;
  if(s.c>0){
    Big r=s.d%3;
    if(r<0)r+=3;
    mod2=(r==2);
  }else if(amin==amax){
    Big r=(amin+s.d)%3;
    if(r<0)r+=3;
    mod2=(r==2);
  }

  if(mod2){
    // 2y-1-3n < 0  <=>  (2y-1)/3 < n.
    const Big coef=2*P-3*M;
    const Big constant=2*s.d-1-3*B;
    if(max_negative_linear(coef,constant,amin,amax))
      return true;
  }

  return false;
}

static State child(
    const State& s,int t,int e,
    const std::vector<Big>& p3){
  uint64_t b=s.b;
  if(e){
    if(t>=63){
      std::cerr<<"B_RESIDUE_RANGE_EXCEEDED\n";
      std::exit(4);
    }
    b += (UINT64_C(1)<<t);
  }
  Big y=s.d;
  if(e)y+=p3[s.c];

  uint32_t c=s.c;
  Big d;
  if((y&1)!=0){
    ++c;
    d=(3*y+1)/2;
  }else{
    d=y/2;
  }
  return {b,d,c};
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: symbolic_shell K EXTRA\n";return 2;}
  const int K=std::stoi(argv[1]);
  const int EXTRA=std::stoi(argv[2]);
  if(K<2||K>60||EXTRA<0||EXTRA>8192)return 2;

  const int TMAX=K+EXTRA;
  std::vector<Big> p3(TMAX+3);
  p3[0]=1;
  for(int i=1;i<(int)p3.size();++i)p3[i]=3*p3[i-1];

  std::vector<State> cur,next;
  cur.push_back({0,Big(0),0});

  uint64_t total_closed=0;
  uint64_t peak_states=1;
  int peak_t=0;

  for(int t=0;t<=TMAX;++t){
    uint64_t closed_here=0;

    // Test the current exact families before generating another step.
    if(t>0){
      next.clear();
      next.reserve(cur.size());
      for(auto& s:cur){
        if(uniform_closed(s,t,K,p3)){
          ++closed_here;
          ++total_closed;
        }else{
          next.push_back(std::move(s));
        }
      }
      cur.swap(next);
    }

    if(cur.size()>peak_states){peak_states=cur.size();peak_t=t;}

    std::cout<<"SYMBOLIC_CONE_LEVEL"
             <<" t="<<t
             <<" live_states="<<cur.size()
             <<" closed_here="<<closed_here
             <<" total_closed_states="<<total_closed<<"\n";

    if(cur.empty()){
      std::cout<<"SYMBOLIC_CONE_DONE"
               <<" K="<<K
               <<" extra="<<EXTRA
               <<" final_t="<<t
               <<" live_states=0"
               <<" peak_states="<<peak_states
               <<" peak_t="<<peak_t<<"\n";
      std::cout<<"VERIFIED_SYMBOLIC_ONE_STEP_SHELL_CLOSURE\n";
      return 0;
    }

    if(t==TMAX)break;

    next.clear();

    if(t<K){
      // Both A parities occur in the shell interval.
      if(cur.size()>SIZE_MAX/2){std::cerr<<"STATE_COUNT_OVERFLOW\n";return 5;}
      next.reserve(cur.size()*2);
      for(const auto& s:cur){
        next.push_back(child(s,t,0,p3));
        next.push_back(child(s,t,1,p3));
      }
    }else if(t==K){
      // A=1 at depth K, so only e=1 is the shell-consistent next bit.
      next.reserve(cur.size());
      for(const auto& s:cur)next.push_back(child(s,t,1,p3));
    }else{
      // A=0 thereafter; the concrete integer has no higher residue bits.
      next.reserve(cur.size());
      for(const auto& s:cur)next.push_back(child(s,t,0,p3));
    }

    cur.swap(next);
  }

  std::cout<<"SYMBOLIC_CONE_DONE"
           <<" K="<<K
           <<" extra="<<EXTRA
           <<" final_t="<<TMAX
           <<" live_states="<<cur.size()
           <<" peak_states="<<peak_states
           <<" peak_t="<<peak_t<<"\n";
  std::cout<<"SYMBOLIC_ONE_STEP_RESIDUAL_REMAINS\n";
  return 0;
}
