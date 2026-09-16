// Exact finite-future quotient of the canonical R0 valuation survivor tree.
//
// State:
//   n(q) = r + 2^(A+1) q
//   x(q) = x + 2*3^j q
// after j accelerated odd steps, with
//   B = 2^A x - 3^j r.
//
// Children are exact next v2 valuations a=1,2,... until the uniform direct
// descent tail begins.  A child is CLOSED if either the canonical affine
// consequence classifier or the exhaustive minimal reverse {1,2} chain gives
// a lower witness.  Otherwise it remains live.
//
// After constructing to horizon K, quotient bottom-up by COMPLETE bounded
// future consequence.  At K every live state has signature UNKNOWN=1.
// At earlier depths, a state's signature is the ordered vector of child
// signatures indexed by valuation a, with CLOSED=0.  Thus two states merge iff
// their entire bounded future CLOSED/UNKNOWN language is identical.
//
// This is exact finite-horizon minimization.  It does not assert an infinite
// quotient or prove Collatz.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <map>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using u128 = unsigned __int128;
using i128 = __int128;
static constexpr uint32_t DEAD = std::numeric_limits<uint32_t>::max();

struct State {
  u128 r,x,B;
  int j,A;
};

struct Layer {
  std::vector<uint32_t> offsets;
  std::vector<uint32_t> children;
};

static std::vector<u128> P3;

static std::string s128(u128 z){
  if(!z)return "0";
  std::string s;
  while(z){s.push_back(char('0'+z%10));z/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}
static int v2(u128 z){
  if(!z)return 128;
  const uint64_t lo=(uint64_t)z;
  return lo?__builtin_ctzll(lo):64+__builtin_ctzll((uint64_t)(z>>64));
}
static int v3(u128 z,int cap=128){
  int c=0;while(c<cap&&z%3==0){z/=3;++c;}return c;
}
static u128 pow2(int a){
  if(a<0||a>=127){std::cerr<<"POW2_RANGE\n";std::exit(20);}
  return u128(1)<<a;
}
static u128 Ncoef(const State&s){return pow2(s.A+1);}
static u128 Xcoef(const State&s){return u128(2)*P3.at(s.j);}
static uint64_t invodd(uint64_t a,int bits){
  uint64_t x=a;
  x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;
  if(bits==64)return x;
  return x&((UINT64_C(1)<<bits)-1);
}
static void verify_B(const State&s){
  const u128 lhs=pow2(s.A)*s.x;
  const u128 rhs=P3.at(s.j)*s.r;
  if(lhs<rhs||lhs-rhs!=s.B){
    std::cerr<<"B_IDENTITY_FAIL j="<<s.j<<" A="<<s.A<<"\n";
    std::exit(21);
  }
}

struct Interval {
  enum Kind{EMPTY,ALL,PREFIX,SUFFIX}kind=EMPTY;
  u128 bound=0;
};
static Interval lt_interval(i128 slope,i128 base){
  Interval z;
  if(slope==0){if(base<0)z.kind=Interval::ALL;return z;}
  if(slope>0){
    if(base>=0)return z;
    z.kind=Interval::PREFIX;z.bound=u128(-base-1)/u128(slope);return z;
  }
  const u128 S=u128(-slope);
  if(base<0){z.kind=Interval::ALL;return z;}
  z.kind=Interval::SUFFIX;z.bound=u128(base)/S+1;return z;
}
static bool covers_all(const Interval&a,const Interval&b){
  if(a.kind==Interval::ALL||b.kind==Interval::ALL)return true;
  if(a.kind==Interval::PREFIX&&b.kind==Interval::SUFFIX)return b.bound<=a.bound+1;
  if(b.kind==Interval::PREFIX&&a.kind==Interval::SUFFIX)return a.bound<=b.bound+1;
  return false;
}
static bool classify_closed(const State&s){
  const u128 N=Ncoef(s),X=Xcoef(s);
  const Interval direct=lt_interval(i128(X)-i128(N),i128(s.x)-i128(s.r));
  const int o=std::min(v3(s.x+1),v3(X));
  Interval deep;
  if(o>0){
    const u128 den=P3.at(o),tw=pow2(o);
    const u128 p0=tw*((s.x+1)/den)-1;
    const u128 P=tw*(X/den);
    if(p0!=0)deep=lt_interval(i128(P)-i128(N),i128(p0)-i128(s.r));
  }
  return covers_all(direct,deep);
}

struct RevAff{u128 a,d;};
static bool reverse_closed(const State&s){
  const u128 N=Ncoef(s);
  RevAff z{Xcoef(s),s.x};
  for(int depth=1;depth<=s.j;++depth){
    if(z.a%3!=0)break;
    int b=0;
    if(z.d%3==2)b=1;
    else if(z.d%3==1)b=2;
    else break;
    z={pow2(b)*z.a/3,(pow2(b)*z.d-1)/3};
    if(z.d>0&&z.a<=N&&z.d<s.r)return true;
  }
  return false;
}

static State extend_forward(const State&s,int a){
  if(a<1||a>=63||s.A+a+1>=126){
    std::cerr<<"FORWARD_RANGE\n";std::exit(22);
  }
  const u128 N=Ncoef(s),X=Xcoef(s);
  const uint64_t mod=UINT64_C(1)<<a,mask=mod-1;
  const u128 b0=(3*s.x+1)>>1;
  const u128 c=(3*X)>>1;
  const uint64_t cc=(uint64_t)(c&mask);
  if(!(cc&1)){std::cerr<<"COEF_NOT_ODD\n";std::exit(23);}
  const uint64_t q0=(uint64_t)((u128(
    ((UINT64_C(1)<<(a-1))-(uint64_t)(b0&mask))&mask)
    *invodd(cc,a))&mask);
  const u128 r=s.r+N*u128(q0);
  const u128 xx=s.x+X*u128(q0);
  const u128 numer=3*xx+1;
  if(v2(numer)!=a){std::cerr<<"VALUATION_FAIL\n";std::exit(24);}
  State z{r,numer>>a,3*s.B+pow2(s.A),s.j+1,s.A+a};
  verify_B(z);
  return z;
}
static int tail_start(const State&s){
  const u128 N=Ncoef(s),X=Xcoef(s);
  int a=std::max(1,v2(3*s.x+1)+1);
  for(;;++a){
    if(a>=63||s.A+a+1>=126){std::cerr<<"TAIL_RANGE\n";std::exit(25);}
    const u128 two=pow2(a);
    if(3*X<two*N && 3*s.x+1+3*X<two*(s.r+N))return a;
  }
}

static std::string key_bytes(const std::vector<uint32_t>& v){
  return std::string(reinterpret_cast<const char*>(v.data()),
                     v.size()*sizeof(uint32_t));
}

int main(int argc,char**argv){
  if(argc!=2){std::cerr<<"usage: r0_future_quotient K\n";return 2;}
  const int K=std::stoi(argv[1]);
  if(K<1||K>20){std::cerr<<"K_RANGE\n";return 2;}

  P3.resize(128);P3[0]=1;
  for(int i=1;i<(int)P3.size();++i)P3[i]=P3[i-1]*3;

  std::vector<State> live{{3,3,0,0,0}};
  verify_B(live[0]);
  std::vector<Layer> layers(K);
  std::vector<uint64_t> liveCount(K+1,0);
  liveCount[0]=1;
  uint64_t totalClosed=0,totalLiveEdges=0;

  for(int depth=1;depth<=K;++depth){
    Layer &L=layers[depth-1];
    L.offsets.reserve(live.size()+1);
    L.offsets.push_back(0);
    std::vector<State> next;

    uint64_t closed=0,generated=0;
    int maxBranch=0;
    for(const State&p:live){
      const int tail=tail_start(p);
      maxBranch=std::max(maxBranch,tail-1);
      for(int a=1;a<tail;++a){
        ++generated;
        State z=extend_forward(p,a);
        if(classify_closed(z)||reverse_closed(z)){
          L.children.push_back(DEAD);
          ++closed;
        }else{
          if(next.size()>=size_t(DEAD)){
            std::cerr<<"INDEX_RANGE\n";return 30;
          }
          L.children.push_back((uint32_t)next.size());
          next.push_back(z);
        }
      }
      L.offsets.push_back((uint32_t)L.children.size());
    }

    totalClosed+=closed;
    totalLiveEdges+=next.size();
    liveCount[depth]=next.size();

    // Frozen controls from independently established R0 census.
    if(depth==12 && next.size()!=3704){std::cerr<<"D12_COUNT_DRIFT\n";return 31;}
    if(depth==16 && next.size()!=149182){std::cerr<<"D16_COUNT_DRIFT\n";return 32;}
    if(depth==18 && next.size()!=911686){std::cerr<<"D18_COUNT_DRIFT\n";return 33;}
    if(depth==20 && next.size()!=6550204){std::cerr<<"D20_COUNT_DRIFT\n";return 34;}

    std::cout<<"R0_FUTURE_BUILD depth="<<depth
             <<" parents="<<live.size()
             <<" generated="<<generated
             <<" closed="<<closed
             <<" live="<<next.size()
             <<" max_branch="<<maxBranch
             <<"\n";
    live.swap(next);
  }

  const uint64_t frontier=live.size();
  std::vector<State>().swap(live);

  // 0=CLOSED; 1=UNKNOWN at target horizon.
  std::vector<uint32_t> nextSig(frontier,1),curSig;
  std::unordered_map<std::string,uint32_t> intern;
  intern.reserve(1<<16);
  uint32_t nextId=2;

  std::cout<<"R0_FUTURE_QUOTIENT depth="<<K
           <<" remaining=0 states="<<frontier
           <<" unique_signatures="<<(frontier?1:0)
           <<" compression="<<(frontier?double(frontier):0.0)
           <<"\n";

  uint64_t maxUnique=frontier?1:0;
  int maxUniqueDepth=K;

  for(int depth=K-1;depth>=0;--depth){
    const Layer&L=layers[depth];
    const size_t parents=L.offsets.size()-1;
    curSig.resize(parents);
    std::unordered_set<uint32_t> unique;
    unique.reserve(std::min<size_t>(parents,1<<18));
    std::map<size_t,uint64_t> arityHist;

    for(size_t i=0;i<parents;++i){
      const uint32_t lo=L.offsets[i],hi=L.offsets[i+1];
      std::vector<uint32_t> sig;
      sig.reserve(hi-lo);
      for(uint32_t p=lo;p<hi;++p){
        const uint32_t child=L.children[p];
        sig.push_back(child==DEAD?0:nextSig[child]);
      }
      ++arityHist[sig.size()];
      const std::string key=key_bytes(sig);
      auto it=intern.find(key);
      if(it==intern.end()){
        if(nextId==DEAD){std::cerr<<"SIGNATURE_RANGE\n";return 35;}
        it=intern.emplace(key,nextId++).first;
      }
      curSig[i]=it->second;
      unique.insert(it->second);
    }

    const uint64_t u=unique.size();
    if(u>maxUnique){maxUnique=u;maxUniqueDepth=depth;}
    std::cout<<"R0_FUTURE_QUOTIENT depth="<<depth
             <<" remaining="<<(K-depth)
             <<" states="<<parents
             <<" unique_signatures="<<u
             <<" compression="<<(u?double(parents)/double(u):0.0)
             <<" arities=";
    bool first=true;
    for(const auto&kv:arityHist){
      if(!first)std::cout<<",";
      first=false;
      std::cout<<kv.first<<":"<<kv.second;
    }
    std::cout<<"\n";
    nextSig.swap(curSig);
  }

  if(nextSig.size()!=1){std::cerr<<"ROOT_COUNT\n";return 36;}
  std::cout<<"R0_FUTURE_QUOTIENT_RESULT K="<<K
           <<" frontier="<<frontier
           <<" signature_types="<<nextId
           <<" max_unique="<<maxUnique
           <<" max_unique_depth="<<maxUniqueDepth
           <<" total_closed_edges="<<totalClosed
           <<" total_live_edges="<<totalLiveEdges
           <<" root_signature="<<nextSig[0]
           <<"\n";
  std::cout<<"VERIFIED_R0_EXACT_FUTURE_QUOTIENT_D"<<K<<"\n";
  std::cout<<"FINAL_GATE=R0_FUTURE_QUOTIENT_D"<<K<<"\n";
  return 0;
}
