// Exact strong-induction base for the shortcut Collatz map.
// For every 2 <= n < 2^20, find an exact positive forward iterate < n.
// Since 1 is the base case, this is a self-contained strong-induction proof
// that every n < 2^20 reaches 1.
//
// This deliberately proves the same consequence used by the shell
// certificates rather than relying on a published verification bound.

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>

using u128=unsigned __int128;

static inline u128 T(u128 n){
  return (n&1)?(3*n+1)/2:n/2;
}

int main(){
  const uint64_t LIMIT=UINT64_C(1)<<20;
  uint64_t max_steps=0,max_seed=0;
  u128 max_value=0;
  uint64_t controls=0;

  for(uint64_t n=2;n<LIMIT;++n){
    u128 x=n;
    u128 peak=x;
    uint64_t steps=0;
    bool closed=false;

    for(;steps<10000;++steps){
      x=T(x);
      peak=std::max(peak,x);
      if(x>0 && x<n){
        ++steps;
        closed=true;
        break;
      }
    }

    if(!closed){
      std::cerr<<"BASE_NO_LOWER_ITERATE n="<<n<<" steps="<<steps<<"\n";
      return 2;
    }
    if(steps>max_steps){
      max_steps=steps;
      max_seed=n;
    }
    max_value=std::max(max_value,peak);
    ++controls;
  }

  auto s128=[](u128 x){
    if(!x)return std::string("0");
    std::string s;
    while(x){s.push_back(char('0'+x%10));x/=10;}
    std::reverse(s.begin(),s.end());
    return s;
  };

  std::cout<<"COLLATZ_STRONG_INDUCTION_BASE"
           <<" limit="<<LIMIT
           <<" checked="<<controls
           <<" max_steps_to_lower="<<max_steps
           <<" max_steps_seed="<<max_seed
           <<" max_intermediate="<<s128(max_value)<<"\n";
  std::cout<<"VERIFIED_COLLATZ_STRONG_INDUCTION_BASE_BELOW_2_20\n";
  return 0;
}
