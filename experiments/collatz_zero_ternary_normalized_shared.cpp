// Shared normalized exact zero-ternary closure.
//
// For fixed (K,r), the normalized transition graph is independent of the
// boundary b.  The reference solver asks whether any reachable normalized
// state has lower slope and D < b.  This file computes the stronger exact
// value function
//
//   bestD(state) = minimum positive reachable D' at a state satisfying
//                  coef_le(...), if one exists.
//
// Hence a boundary closes iff bestD(root) < b.  One memo table can therefore
// serve every residual boundary at the same (K,r).  The original boolean DFS
// is retained as a differential oracle in --verify mode.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

using i128=__int128;
using u128=unsigned __int128;

static std::string s128(u128 x){
  if(!x)return "0";
  std::string s;
  while(x){s.push_back(char('0'+x%10));x/=10;}
  std::reverse(s.begin(),s.end());
  return s;
}

static u128 pow3u(int n){
  u128 x=1,M=~u128(0);
  for(int i=0;i<n;++i){
    if(x>M/3){std::cerr<<"POW3_RANGE\n";std::exit(7);}
    x*=3;
  }
  return x;
}

static bool coef_le(int u,int v,int k,int r){
  const int z=v-r;
  if(z>=0){
    if(u>k)return false;
    const int gap=k-u;
    if(z==0)return true;
    if(z>40)return false;
    return pow3u(z) <= (u128(1)<<gap);
  }
  const int q=-z;
  if(u<=k)return true;
  const int d=u-k;
  if(d>=128)return false;
  const u128 lhs=u128(1)<<d;
  return lhs<=pow3u(q);
}

static bool future_coef_possible(int u,int v,int k,int r){
  return coef_le(u+v,0,k,r);
}

struct NKey{
  int u,v;
  u128 D;
  bool operator==(const NKey&o)const{return u==o.u&&v==o.v&&D==o.D;}
  bool operator<(const NKey&o)const{
    if(u!=o.u)return u<o.u;
    if(v!=o.v)return v<o.v;
    return D<o.D;
  }
};

static uint64_t mix64(uint64_t x) noexcept{
  x+=UINT64_C(0x9e3779b97f4a7c15);
  x=(x^(x>>30))*UINT64_C(0xbf58476d1ce4e5b9);
  x=(x^(x>>27))*UINT64_C(0x94d049bb133111eb);
  return x^(x>>31);
}

struct NKeyHash{
  std::size_t operator()(const NKey&x)const noexcept{
    const uint64_t lo=static_cast<uint64_t>(x.D);
    const uint64_t hi=static_cast<uint64_t>(x.D>>64);
    uint64_t h=mix64(lo)^mix64(hi+UINT64_C(0x517cc1b727220a95));
    h^=mix64((uint64_t(uint32_t(x.u))<<32)|uint32_t(x.v));
    return static_cast<std::size_t>(h);
  }
};

struct RefStats{
  uint64_t nodes=0,memo=0,e=0,o=0,prunes=0,maxNodes=0;
  int maxU=0,maxV=0;
};

struct SharedStats{
  uint64_t calls=0,unique=0,memo=0,e=0,o=0,prunes=0,peakMemo=0;
  int maxU=0,maxV=0;
};

struct BestResult{
  bool reachable=false;
  u128 best=0;
};

using BestMemo=std::unordered_map<NKey,BestResult,NKeyHash>;

static int v3u(u128 x,int cap=200){
  int z=0;
  while(z<cap&&x%3==0){x/=3;++z;}
  return z;
}

// Reference implementation: intentionally kept semantically identical to the
// corrected normalized DFS used in run 35056988382.
static bool reference_ndfs(int u,int v,u128 D,int k,int r,uint64_t b,
                           std::set<NKey>&seen,uint64_t&local,RefStats&st){
  ++local;++st.nodes;
  st.maxU=std::max(st.maxU,u);st.maxV=std::max(st.maxV,v);
  if(D==0)return false;
  if(!seen.emplace(NKey{u,v,D}).second){++st.memo;return false;}

  if(coef_le(u,v,k,r)&&D<u128(b))return true;
  if(v<=0)return false;

  int ue=u;
  u128 De=D;
  const u128 MAX=~u128(0);
  for(int e=0;;++e){
    (void)e;
    if(!future_coef_possible(ue,v,k,r)){++st.prunes;break;}
    ++st.e;

    const int mmax=(De==MAX)?0:std::min(v,v3u(De+1));
    u128 den=1,tw=1;
    for(int m=1;m<=mmax;++m){
      den*=3;tw*=2;++st.o;
      const u128 q=(De+1)/den;
      if(q&&tw>MAX/q){std::cerr<<"D_MUL_RANGE\n";std::exit(8);}
      const u128 D2=tw*q-1;
      if(reference_ndfs(ue+m,v-m,D2,k,r,b,seen,local,st))return true;
    }

    if(De>MAX/2){std::cerr<<"D_E_RANGE\n";std::exit(9);}
    De*=2;++ue;
  }
  return false;
}

static bool reference_closes(int c,uint64_t d,int k,int r,uint64_t b,RefStats&st){
  std::set<NKey>seen;
  uint64_t local=0;
  const bool ok=reference_ndfs(0,c+r,u128(d),k,r,b,seen,local,st);
  st.maxNodes=std::max(st.maxNodes,local);
  return ok;
}

static void consider(BestResult&dst,const BestResult&src){
  if(!src.reachable)return;
  if(!dst.reachable||src.best<dst.best){dst=src;}
}

static BestResult bestD(int u,int v,u128 D,int k,int r,
                        BestMemo&memo,SharedStats&st){
  ++st.calls;
  st.maxU=std::max(st.maxU,u);st.maxV=std::max(st.maxV,v);
  if(D==0)return {};

  const NKey key{u,v,D};
  if(const auto it=memo.find(key);it!=memo.end()){
    ++st.memo;
    return it->second;
  }
  ++st.unique;

  BestResult ans;
  if(coef_le(u,v,k,r))ans={true,D};

  if(v>0&&(!ans.reachable||ans.best!=1)){
    int ue=u;
    u128 De=D;
    const u128 MAX=~u128(0);
    for(int e=0;;++e){
      (void)e;
      if(!future_coef_possible(ue,v,k,r)){++st.prunes;break;}
      ++st.e;

      const int mmax=(De==MAX)?0:std::min(v,v3u(De+1));
      u128 den=1,tw=1;
      for(int m=1;m<=mmax;++m){
        den*=3;tw*=2;++st.o;
        const u128 q=(De+1)/den;
        if(q&&tw>MAX/q){std::cerr<<"D_MUL_RANGE\n";std::exit(8);}
        const u128 D2=tw*q-1;
        const BestResult child=bestD(ue+m,v-m,D2,k,r,memo,st);
        consider(ans,child);
        if(ans.reachable&&ans.best==1)break;
      }
      if(ans.reachable&&ans.best==1)break;

      if(De>MAX/2){std::cerr<<"D_E_RANGE\n";std::exit(9);}
      De*=2;++ue;
    }
  }

  memo.emplace(key,ans);
  st.peakMemo=std::max<uint64_t>(st.peakMemo,memo.size());
  return ans;
}

static bool shared_closes(int c,uint64_t d,int k,int r,uint64_t b,
                          BestMemo&memo,SharedStats&st,BestResult*root=nullptr){
  const BestResult ans=bestD(0,c+r,u128(d),k,r,memo,st);
  if(root)*root=ans;
  return ans.reachable&&ans.best<u128(b);
}

// Qualified baseline residual builder (r=0 complete affine language).
static int v3i(i128 x,int cap=80){
  if(x<0)x=-x;
  int z=0;
  while(z<cap&&x%3==0){x/=3;++z;}
  return z;
}
static i128 mulc(i128 a,i128 b){
  if(a<0||b<0||(a&&b>(i128(1)<<120)/a)){
    std::cerr<<"I128_RANGE\n";std::exit(10);
  }
  return a*b;
}
static i128 powi(i128 b,int e){
  i128 x=1;
  for(int i=0;i<e;++i)x=mulc(x,b);
  return x;
}
static uint64_t child_lower(uint64_t L,int bit){
  if(L<=uint64_t(bit))return 0;
  return (L-uint64_t(bit)+1)/2;
}
static bool lower_family(i128 A,i128 D,i128 M,i128 b,uint64_t L){
  i128 q=L,s=A-M;
  return A>0&&A*q+D>0&&s<=0&&s*q+D-b<0;
}
struct AKey{
  i128 A,D;
  bool operator<(const AKey&o)const{return A<o.A||(A==o.A&&D<o.D);}
};
static bool adfs(i128 A,i128 D,i128 M,i128 b,uint64_t L,std::set<AKey>&seen){
  if(A*i128(L)+D<=0)return false;
  if(!seen.emplace(AKey{A,D}).second)return false;
  int rem=v3i(A);
  if(rem<=0)return false;
  i128 denAll=powi(3,rem),twAll=powi(2,rem),Ae=A,De=D;
  for(int e=0;;++e){
    if(e){
      Ae=mulc(Ae,2);De*=2;
      if(De>(i128(1)<<120)){std::cerr<<"BASE_D_RANGE\n";std::exit(11);}
    }
    if(mulc(Ae/denAll,twAll)>M)break;
    int mm=std::min(rem,v3i(De+1));
    i128 den=1,tw=1;
    for(int m=1;m<=mm;++m){
      den*=3;tw*=2;
      i128 A2=mulc(Ae/den,tw),D2=mulc((De+1)/den,tw)-1;
      if(lower_family(A2,D2,M,b,L)||adfs(A2,D2,M,b,L,seen))return true;
    }
  }
  return false;
}
static bool acloses(i128 A,i128 D,i128 M,i128 b,uint64_t L){
  if(lower_family(A,D,M,b,L))return true;
  std::set<AKey>seen;
  return adfs(A,D,M,b,L,seen);
}

struct State{uint64_t b,d;uint32_t c;uint64_t L;};
static std::vector<State> build(int K,const std::vector<i128>&p3){
  std::vector<State>cur{{0,0,0,2}},next;
  for(int k=1;k<=K;++k){
    uint64_t half=UINT64_C(1)<<(k-1);
    i128 M=i128(1)<<k;
    next.clear();
    for(auto&s:cur)for(int bit=0;bit<2;++bit){
      uint64_t L=child_lower(s.L,bit),b=s.b+(bit?half:0);
      i128 raw=i128(s.d)+(bit?p3[s.c]:0);
      uint32_t c=s.c;
      i128 d;
      if(raw&1){++c;d=(3*raw+1)/2;}else d=raw/2;
      if(acloses(p3[c],d,M,b,L))continue;
      next.push_back({b,uint64_t(d),c,L});
    }
    cur.swap(next);
  }
  return cur;
}

static std::vector<i128> powers3_for(int K){
  std::vector<i128>p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i)p3[i]=mulc(p3[i-1],3);
  return p3;
}

static bool check_frozen(int K,std::size_t n){
  const std::map<int,uint64_t>frozen{{12,144},{16,1363},{20,15870},{24,172868}};
  if(const auto it=frozen.find(K);it!=frozen.end()&&n!=it->second){
    std::cerr<<"BASELINE_DRIFT K="<<K<<" expected="<<it->second<<" actual="<<n<<"\n";
    return false;
  }
  return true;
}

static int verify_mode(int K,int R,const std::vector<State>&residual){
  RefStats refStats;
  SharedStats sharedStats;
  uint64_t comparisons=0;

  for(int r=0;r<=R;++r){
    BestMemo memo;
    memo.reserve(std::max<std::size_t>(1024,residual.size()*8));
    for(std::size_t i=0;i<residual.size();++i){
      const State&s=residual[i];
      if(s.L!=0){std::cerr<<"EXPECTED_L0\n";return 13;}
      const bool ref=reference_closes((int)s.c,s.d,K,r,s.b,refStats);
      BestResult root;
      const bool got=shared_closes((int)s.c,s.d,K,r,s.b,memo,sharedStats,&root);
      ++comparisons;
      if(ref!=got){
        std::cerr<<"SHARED_MISMATCH K="<<K<<" R="<<R<<" r="<<r
                 <<" index="<<i<<" b="<<s.b<<" c="<<s.c<<" d="<<s.d
                 <<" reference="<<ref<<" shared="<<got
                 <<" best_reachable="<<root.reachable
                 <<" bestD="<<(root.reachable?s128(root.best):std::string("NA"))<<"\n";
        return 20;
      }
    }
    sharedStats.peakMemo=std::max<uint64_t>(sharedStats.peakMemo,memo.size());
    std::cout<<"VERIFY_R r="<<r<<" memo_states="<<memo.size()<<" comparisons="<<comparisons<<"\n";
  }

  std::cout<<"VERIFY_RESULT K="<<K<<" R="<<R
           <<" residual="<<residual.size()<<" comparisons="<<comparisons
           <<" reference_nodes="<<refStats.nodes<<" reference_memo_hits="<<refStats.memo
           <<" shared_calls="<<sharedStats.calls<<" shared_unique_states="<<sharedStats.unique
           <<" shared_memo_hits="<<sharedStats.memo<<" shared_peak_memo="<<sharedStats.peakMemo
           <<" shared_e_cases="<<sharedStats.e<<" shared_o_run_cases="<<sharedStats.o
           <<" shared_prunes="<<sharedStats.prunes
           <<" max_u="<<sharedStats.maxU<<" max_v="<<sharedStats.maxV<<"\n";
  std::cout<<"VERIFIED_SHARED_EQUIVALENCE\n";
  return 0;
}

static int shared_mode(int K,int R,const std::vector<State>&residual){
  SharedStats st;
  std::vector<unsigned char>done(residual.size(),0);
  std::map<int,uint64_t>hist;
  uint64_t unresolved=residual.size(),closed=0;
  int maxR=-1;
  uint64_t maxB=0;

  for(const State&s:residual){
    if(s.L!=0){std::cerr<<"EXPECTED_L0\n";return 13;}
  }

  for(int r=0;r<=R&&unresolved;++r){
    BestMemo memo;
    memo.reserve(std::max<std::size_t>(1024,unresolved*8));
    const uint64_t calls0=st.calls,memo0=st.memo,unique0=st.unique;
    uint64_t newly=0;
    for(std::size_t i=0;i<residual.size();++i){
      if(done[i])continue;
      const State&s=residual[i];
      if(shared_closes((int)s.c,s.d,K,r,s.b,memo,st)){
        done[i]=1;
        ++newly;++closed;--unresolved;
        if(r>maxR){maxR=r;maxB=s.b;}
      }
    }
    hist[r]=newly;
    st.peakMemo=std::max<uint64_t>(st.peakMemo,memo.size());
    std::cout<<"SHARED_R r="<<r<<" newly="<<newly<<" cumulative="<<closed
             <<" remaining="<<unresolved<<" memo_states="<<memo.size()
             <<" calls_delta="<<(st.calls-calls0)
             <<" unique_delta="<<(st.unique-unique0)
             <<" memo_hits_delta="<<(st.memo-memo0)<<"\n";
  }

  std::cout<<"SHARED_RESULT K="<<K<<" R="<<R<<" residual="<<residual.size()
           <<" closed="<<closed<<" unresolved="<<unresolved
           <<" max_required_r="<<maxR<<" max_witness_b="<<maxB
           <<" calls="<<st.calls<<" unique_states="<<st.unique
           <<" memo_hits="<<st.memo<<" e_cases="<<st.e
           <<" o_run_cases="<<st.o<<" prunes="<<st.prunes
           <<" peak_memo="<<st.peakMemo<<" max_u="<<st.maxU<<" max_v="<<st.maxV<<"\n";
  if(!unresolved)std::cout<<"ALL_BOUNDARIES_HAVE_SHARED_NORMALIZED_ZERO_TERNARY_NEIGHBORHOOD\n";
  else std::cout<<"SHARED_NORMALIZED_ZERO_TERNARY_RESIDUAL_REMAINS\n";
  std::cout<<"VERIFIED_SHARED_NORMALIZED_SCOUT\n";
  return 0;
}

int main(int argc,char**argv){
  bool verify=false;
  int K=0,R=0;
  if(argc==4&&std::string(argv[1])=="--verify"){
    verify=true;K=std::stoi(argv[2]);R=std::stoi(argv[3]);
  }else if(argc==3){
    K=std::stoi(argv[1]);R=std::stoi(argv[2]);
  }else{
    std::cerr<<"usage: shared_normalized_zero_ternary [--verify] K R\n";
    return 2;
  }
  if(K<1||K>24||R<0||R>80)return 2;

  const auto p3=powers3_for(K);
  const auto residual=build(K,p3);
  if(!check_frozen(K,residual.size()))return 12;

  return verify?verify_mode(K,R,residual):shared_mode(K,R,residual);
}
