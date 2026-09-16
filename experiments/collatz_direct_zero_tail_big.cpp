// Exact direct zero-tail closure with no giant-coefficient materialization.
//
// Build the qualified complete-affine residual at binary depth K (K<=24).
// For each residual family, follow only q=0: b is fixed and d follows the
// concrete shortcut Collatz map.
//
// Uniform direct closure at future depth K+t holds exactly when
//   d_t < b  and  3^(c_t) <= 2^(K+t).
//
// The first condition concerns the boundary intercept; the second says the
// affine slope is nonexpanding.  We track d_t and 3^c with a tiny exact
// arbitrary-precision unsigned integer implementation, so H can be thousands
// without materializing powers in i128.
//
// If every residual family direct-closes on its deterministic zero-tail, then
// the reverse grammar is not needed on the ordinary boundary at all.
// This remains a finite-depth qualification until a depth-independent bound
// or rank is proved.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <vector>

using i128=__int128;
using u128=unsigned __int128;

struct Big {
  std::vector<uint64_t> a; // little endian
  Big(uint64_t x=0){if(x)a.push_back(x);}
  bool zero()const{return a.empty();}
  bool odd()const{return !a.empty()&&(a[0]&1);}
  void trim(){while(!a.empty()&&a.back()==0)a.pop_back();}
  void mul3add1(){
    unsigned __int128 carry=1;
    for(size_t i=0;i<a.size();++i){
      unsigned __int128 z=(unsigned __int128)a[i]*3+carry;
      a[i]=(uint64_t)z;carry=z>>64;
    }
    if(carry)a.push_back((uint64_t)carry);
  }
  void mul3(){
    unsigned __int128 carry=0;
    for(size_t i=0;i<a.size();++i){
      unsigned __int128 z=(unsigned __int128)a[i]*3+carry;
      a[i]=(uint64_t)z;carry=z>>64;
    }
    if(carry)a.push_back((uint64_t)carry);
  }
  void shr1(){
    uint64_t carry=0;
    for(size_t i=a.size();i-->0;){
      uint64_t nc=a[i]&1;
      a[i]=(a[i]>>1)|(carry<<63);
      carry=nc;
    }
    trim();
  }
  bool lt_u64(uint64_t x)const{
    if(a.size()>1)return false;
    uint64_t v=a.empty()?0:a[0];
    return v<x;
  }
  int bitlen()const{
    if(a.empty())return 0;
    return int((a.size()-1)*64 + 64-__builtin_clzll(a.back()));
  }
  bool le_pow2(int k)const{
    // exact compare with 2^k.
    const int bl=bitlen();
    if(bl<k+1)return true;
    if(bl>k+1)return false;
    const size_t limb=size_t(k/64);const int bit=k%64;
    if(a.size()!=limb+1)return false;
    for(size_t i=0;i<limb;++i)if(a[i]!=0)return false;
    return a[limb] <= (uint64_t(1)<<bit);
  }
};

struct State{uint64_t b,d;uint32_t c;uint64_t L;};

static int v3i(i128 x,int cap=80){if(x<0)x=-x;int v=0;while(v<cap&&x%3==0){x/=3;++v;}return v;}
static i128 mulc(i128 a,i128 b){
  if(a<0||b<0||(a&&b>(i128(1)<<120)/a)){std::cerr<<"I128_RANGE\n";std::exit(7);}
  return a*b;
}
static i128 powi(i128 b,int e){i128 x=1;for(int i=0;i<e;++i)x=mulc(x,b);return x;}
static uint64_t child_lower(uint64_t L,int bit){if(L<=uint64_t(bit))return 0;return (L-uint64_t(bit)+1)/2;}
static bool lower_family(i128 A,i128 D,i128 M,i128 b,uint64_t L){
  const i128 q=i128(L),s=A-M;
  return A>0&&A*q+D>0&&s<=0&&s*q+D-b<0;
}
struct Key{i128 A,D;bool operator<(const Key&o)const{return A<o.A||(A==o.A&&D<o.D);}};
static bool dfs(i128 A,i128 D,i128 M,i128 b,uint64_t L,std::set<Key>&seen){
  if(A*i128(L)+D<=0)return false;
  if(!seen.emplace(Key{A,D}).second)return false;
  const int rem=v3i(A);if(rem<=0)return false;
  const i128 denAll=powi(3,rem),twAll=powi(2,rem);
  i128 Ae=A,De=D;
  for(int e=0;;++e){
    if(e){Ae=mulc(Ae,2);De*=2;if(De>(i128(1)<<120)||De<-(i128(1)<<120)){std::cerr<<"D_RANGE\n";std::exit(8);}}
    const i128 amin=mulc(Ae/denAll,twAll);
    if(amin>M)break;
    const int mmax=std::min(rem,v3i(De+1));
    i128 den=1,tw=1;
    for(int m=1;m<=mmax;++m){
      den=mulc(den,3);tw=mulc(tw,2);
      const i128 A2=mulc(Ae/den,tw),D2=mulc((De+1)/den,tw)-1;
      if(lower_family(A2,D2,M,b,L))return true;
      if(dfs(A2,D2,M,b,L,seen))return true;
    }
  }
  return false;
}
static bool closes(i128 A,i128 D,i128 M,i128 b,uint64_t L){
  if(lower_family(A,D,M,b,L))return true;
  std::set<Key>seen;return dfs(A,D,M,b,L,seen);
}
static std::vector<State> build(int K,const std::vector<i128>&p3){
  std::vector<State>cur{{0,0,0,2}},next;
  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1);const i128 M=i128(1)<<k;
    next.clear();
    for(const auto&s:cur)for(int bit=0;bit<2;++bit){
      uint64_t L=child_lower(s.L,bit),b=s.b+(bit?half:0);
      i128 raw=i128(s.d)+(bit?p3[s.c]:0);uint32_t c=s.c;i128 d;
      if(raw&1){++c;d=(3*raw+1)/2;}else d=raw/2;
      if(closes(p3[c],d,M,b,L))continue;
      next.push_back({b,uint64_t(d),c,L});
    }
    cur.swap(next);
  }
  return cur;
}

static Big pow3big(uint32_t c){Big z(1);for(uint32_t i=0;i<c;++i)z.mul3();return z;}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: direct_zero_tail K H\n";return 2;}
  const int K=std::stoi(argv[1]),H=std::stoi(argv[2]);
  if(K<1||K>24||H<1||H>4096)return 2;

  std::vector<i128>p3(K+2,1);for(int i=1;i<(int)p3.size();++i)p3[i]=mulc(p3[i-1],3);
  const auto residual=build(K,p3);
  const std::map<int,uint64_t> frozen{{12,144},{16,1363},{20,15870},{24,172868}};
  auto fi=frozen.find(K);if(fi!=frozen.end()&&residual.size()!=fi->second){std::cerr<<"BASELINE_DRIFT\n";return 10;}

  std::map<int,uint64_t>hist;uint64_t unresolved=0,slopeWait=0;
  int maxT=-1;uint64_t maxB=0;int maxFirstBelow=-1;
  for(const auto&s:residual){
    if(s.L!=0){std::cerr<<"EXPECTED_L0\n";return 11;}
    Big d(s.d),p3c=pow3big(s.c);
    int firstBelow=-1;bool done=false;
    for(int t=1;t<=H;++t){
      const bool wasOdd=d.odd();
      if(wasOdd){d.mul3add1();d.shr1();p3c.mul3();}
      else d.shr1();
      if(firstBelow<0&&d.lt_u64(s.b))firstBelow=t;
      if(d.lt_u64(s.b)&&p3c.le_pow2(K+t)){
        ++hist[t];if(t>maxT){maxT=t;maxB=s.b;}
        if(firstBelow>=0&&firstBelow<t)++slopeWait;
        done=true;break;
      }
    }
    maxFirstBelow=std::max(maxFirstBelow,firstBelow);
    if(!done)++unresolved;
  }

  uint64_t cum=0;
  for(const auto&kv:hist){cum+=kv.second;if(kv.first<=64||kv.first==maxT)
    std::cout<<"DIRECT_ZERO_TAIL_CLOSURE t="<<kv.first<<" newly="<<kv.second
             <<" cumulative="<<cum<<" remaining="<<(residual.size()-cum)<<"\n";}
  std::cout<<"DIRECT_ZERO_TAIL_RESULT K="<<K<<" H="<<H
           <<" residual="<<residual.size()<<" closed="<<(residual.size()-unresolved)
           <<" unresolved="<<unresolved<<" max_extra_steps="<<maxT
           <<" max_witness_b="<<maxB<<" slope_wait_cases="<<slopeWait
           <<" max_first_boundary_descent="<<maxFirstBelow<<"\n";
  if(!unresolved)std::cout<<"ALL_RESIDUAL_ZERO_TAILS_DIRECT_CLOSE_WITHIN_H"<<H<<"\n";
  else std::cout<<"DIRECT_ZERO_TAIL_RESIDUAL_REMAINS\n";
  std::cout<<"VERIFIED_EXACT_DIRECT_ZERO_TAIL_CENSUS\n";
  return 0;
}
