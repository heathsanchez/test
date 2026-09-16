// Global normalized zero-ternary refinement frontier.
//
// Put w = v-r.  Then the normalized lower-slope condition is
//
//     2^u 3^w <= 2^K,
//
// independent of the zero-refinement r.  Reverse E leaves w unchanged and
// every O lowers w.  Therefore a path ending at w is available exactly when
// r >= rho := max(0,-w).  For a fixed maximum refinement R, one memoized graph
// over (u,w,D) can answer every r<=R and every boundary b.
//
// Each memo entry stores the nondominated Pareto frontier (rho,bestD):
// increasing rho can only improve the minimum reachable positive intercept.
// A boundary b closes at refinement r iff the root frontier contains a point
// with rho<=r and bestD<b.
//
// The corrected fixed-r DFS is retained as a differential oracle.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
#include <set>
#include <string>
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

// Reference fixed-r coefficient predicate.
static bool coef_le(int u,int v,int k,int r){
  const int z=v-r;
  if(z>=0){
    if(u>k)return false;
    const int gap=k-u;
    if(z==0)return true;
    if(z>40)return false;
    return pow3u(z)<=(u128(1)<<gap);
  }
  const int q=-z;
  if(u<=k)return true;
  const int d=u-k;
  if(d>=128)return false;
  return (u128(1)<<d)<=pow3u(q);
}

static bool future_coef_possible(int u,int v,int k,int r){
  return coef_le(u+v,0,k,r);
}

// Quotiented coefficient predicate: exactly coef_le(u,w+r,k,r).
static bool coef_le_w(int u,int w,int k){
  if(w>=0){
    if(u>k)return false;
    const int gap=k-u;
    if(w==0)return true;
    if(w>80)return false;
    return pow3u(w)<=(u128(1)<<gap);
  }
  const int q=-w;
  if(u<=k)return true;
  const int d=u-k;
  if(d>=128)return false;
  return (u128(1)<<d)<=pow3u(q);
}

// At maximum allowed refinement R, the current state has v=w+R O-capacity.
// Spending all of it minimizes the future coefficient.  If even that state
// cannot meet the slope bound, no r<=R continuation can close.
static bool future_coef_possible_R(int u,int w,int k,int R){
  const int vmax=w+R;
  if(vmax<0)return false;
  return coef_le_w(u+vmax,-R,k);
}

struct RKey{
  int u,v;
  u128 D;
  bool operator<(const RKey&o)const{
    if(u!=o.u)return u<o.u;
    if(v!=o.v)return v<o.v;
    return D<o.D;
  }
};

struct RefStats{
  uint64_t nodes=0,memo=0,e=0,o=0,prunes=0,maxNodes=0;
  int maxU=0,maxV=0;
};

static int v3u(u128 x,int cap=200){
  int z=0;
  while(z<cap&&x%3==0){x/=3;++z;}
  return z;
}

static bool reference_ndfs(int u,int v,u128 D,int k,int r,uint64_t b,
                           std::set<RKey>&seen,uint64_t&local,RefStats&st){
  ++local;++st.nodes;
  st.maxU=std::max(st.maxU,u);st.maxV=std::max(st.maxV,v);
  if(D==0)return false;
  if(!seen.emplace(RKey{u,v,D}).second){++st.memo;return false;}

  if(coef_le(u,v,k,r)&&D<u128(b))return true;
  if(v<=0)return false;

  int ue=u;
  u128 De=D;
  const u128 MAX=~u128(0);
  for(;;){
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
  std::set<RKey>seen;
  uint64_t local=0;
  const bool ok=reference_ndfs(0,c+r,u128(d),k,r,b,seen,local,st);
  st.maxNodes=std::max(st.maxNodes,local);
  return ok;
}

struct FKey{
  int u,w;
  u128 D;
  bool operator==(const FKey&o)const{return u==o.u&&w==o.w&&D==o.D;}
};

static uint64_t mix64(uint64_t x) noexcept{
  x+=UINT64_C(0x9e3779b97f4a7c15);
  x=(x^(x>>30))*UINT64_C(0xbf58476d1ce4e5b9);
  x=(x^(x>>27))*UINT64_C(0x94d049bb133111eb);
  return x^(x>>31);
}

struct FKeyHash{
  std::size_t operator()(const FKey&x)const noexcept{
    const uint64_t lo=static_cast<uint64_t>(x.D);
    const uint64_t hi=static_cast<uint64_t>(x.D>>64);
    uint64_t h=mix64(lo)^mix64(hi+UINT64_C(0x517cc1b727220a95));
    h^=mix64((uint64_t(uint32_t(x.u))<<32)|uint32_t(x.w));
    return static_cast<std::size_t>(h);
  }
};

struct FPoint{int req;u128 best;};
using Frontier=std::vector<FPoint>;
using FMemo=std::unordered_map<FKey,Frontier,FKeyHash>;

struct FStats{
  uint64_t calls=0,unique=0,memo=0,e=0,o=0,prunes=0;
  uint64_t frontierPoints=0,peakMemo=0;
  std::size_t maxWidth=0;
  int maxU=0,minW=0;
};

static void add_point(Frontier&f,int req,u128 d){
  auto it=std::lower_bound(f.begin(),f.end(),req,
    [](const FPoint&p,int r){return p.req<r;});

  if(it!=f.begin()){
    const FPoint&prev=*(it-1);
    if(prev.best<=d)return;
  }

  if(it!=f.end()&&it->req==req){
    if(it->best<=d)return;
    it->best=d;
    auto jt=it+1;
    while(jt!=f.end()&&jt->best>=d)jt=f.erase(jt);
    return;
  }

  it=f.insert(it,FPoint{req,d});
  auto jt=it+1;
  while(jt!=f.end()&&jt->best>=d)jt=f.erase(jt);
}

static void merge_frontier(Frontier&dst,const Frontier&src){
  for(const FPoint&p:src)add_point(dst,p.req,p.best);
}

static const Frontier& frontierD(int u,int w,u128 D,int k,int R,
                                 FMemo&memo,FStats&st){
  static const Frontier empty;
  ++st.calls;
  st.maxU=std::max(st.maxU,u);st.minW=std::min(st.minW,w);
  if(D==0)return empty;
  if(w < -R){std::cerr<<"FRONTIER_W_RANGE\n";std::exit(14);}

  const FKey key{u,w,D};
  if(const auto it=memo.find(key);it!=memo.end()){
    ++st.memo;
    return it->second;
  }
  ++st.unique;

  Frontier ans;
  if(coef_le_w(u,w,k)){
    const int req=std::max(0,-w);
    add_point(ans,req,D);
  }

  const int vmax=w+R;
  if(vmax>0){
    int ue=u;
    u128 De=D;
    const u128 MAX=~u128(0);
    for(;;){
      if(!future_coef_possible_R(ue,w,k,R)){++st.prunes;break;}
      ++st.e;

      const int mmax=(De==MAX)?0:std::min(vmax,v3u(De+1));
      u128 den=1,tw=1;
      for(int m=1;m<=mmax;++m){
        den*=3;tw*=2;++st.o;
        const u128 q=(De+1)/den;
        if(q&&tw>MAX/q){std::cerr<<"D_MUL_RANGE\n";std::exit(8);}
        const u128 D2=tw*q-1;
        const Frontier&child=frontierD(ue+m,w-m,D2,k,R,memo,st);
        merge_frontier(ans,child);
      }

      if(De>MAX/2){std::cerr<<"D_E_RANGE\n";std::exit(9);}
      De*=2;++ue;
    }
  }

  st.frontierPoints+=ans.size();
  st.maxWidth=std::max(st.maxWidth,ans.size());
  auto [it,inserted]=memo.emplace(key,std::move(ans));
  if(!inserted){std::cerr<<"FRONTIER_MEMO_RACE\n";std::exit(15);}
  st.peakMemo=std::max<uint64_t>(st.peakMemo,memo.size());
  return it->second;
}

static bool frontier_closes(const Frontier&f,int r,uint64_t b,u128*bestOut=nullptr){
  bool have=false;
  u128 best=0;
  for(const FPoint&p:f){
    if(p.req>r)break;
    best=p.best;have=true;
  }
  if(bestOut&&have)*bestOut=best;
  return have&&best<u128(b);
}

static int first_closing_r(const Frontier&f,uint64_t b){
  for(const FPoint&p:f)if(p.best<u128(b))return p.req;
  return -1;
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
  RefStats ref;
  FStats fs;
  FMemo memo;
  memo.reserve(std::max<std::size_t>(4096,residual.size()*32));
  uint64_t comparisons=0;

  for(std::size_t i=0;i<residual.size();++i){
    const State&s=residual[i];
    if(s.L!=0){std::cerr<<"EXPECTED_L0\n";return 13;}
    const Frontier&f=frontierD(0,(int)s.c,u128(s.d),K,R,memo,fs);
    for(int r=0;r<=R;++r){
      const bool expected=reference_closes((int)s.c,s.d,K,r,s.b,ref);
      u128 best=0;
      const bool got=frontier_closes(f,r,s.b,&best);
      ++comparisons;
      if(expected!=got){
        std::cerr<<"FRONTIER_MISMATCH K="<<K<<" R="<<R<<" r="<<r
                 <<" index="<<i<<" b="<<s.b<<" c="<<s.c<<" d="<<s.d
                 <<" reference="<<expected<<" frontier="<<got
                 <<" best="<<(got?s128(best):std::string("NA"))<<" points="<<f.size()<<"\n";
        for(const FPoint&p:f)std::cerr<<"  POINT req="<<p.req<<" D="<<s128(p.best)<<"\n";
        return 20;
      }
    }
  }

  std::cout<<"FRONTIER_VERIFY_RESULT K="<<K<<" R="<<R
           <<" residual="<<residual.size()<<" comparisons="<<comparisons
           <<" reference_nodes="<<ref.nodes<<" reference_memo_hits="<<ref.memo
           <<" calls="<<fs.calls<<" unique_states="<<fs.unique
           <<" memo_hits="<<fs.memo<<" e_cases="<<fs.e
           <<" o_run_cases="<<fs.o<<" prunes="<<fs.prunes
           <<" frontier_points="<<fs.frontierPoints
           <<" max_frontier_width="<<fs.maxWidth
           <<" peak_memo="<<fs.peakMemo<<" max_u="<<fs.maxU<<" min_w="<<fs.minW<<"\n";
  std::cout<<"VERIFIED_REFINEMENT_FRONTIER_EQUIVALENCE\n";
  return 0;
}

static int scout_mode(int K,int R,const std::vector<State>&residual){
  FStats fs;
  FMemo memo;
  memo.reserve(std::max<std::size_t>(4096,residual.size()*32));
  std::map<int,uint64_t>hist;
  uint64_t unresolved=0;
  int maxR=-1;
  uint64_t maxB=0;

  for(std::size_t i=0;i<residual.size();++i){
    const State&s=residual[i];
    if(s.L!=0){std::cerr<<"EXPECTED_L0\n";return 13;}
    const Frontier&f=frontierD(0,(int)s.c,u128(s.d),K,R,memo,fs);
    const int need=first_closing_r(f,s.b);
    if(need<0||need>R){
      ++unresolved;
    }else{
      ++hist[need];
      if(need>maxR){maxR=need;maxB=s.b;}
    }
  }

  uint64_t cumulative=0;
  for(const auto&kv:hist){
    cumulative+=kv.second;
    std::cout<<"FRONTIER_CLOSURE r="<<kv.first<<" newly="<<kv.second
             <<" cumulative="<<cumulative<<" remaining="<<(residual.size()-cumulative)<<"\n";
  }
  std::cout<<"FRONTIER_RESULT K="<<K<<" R="<<R<<" residual="<<residual.size()
           <<" closed="<<(residual.size()-unresolved)<<" unresolved="<<unresolved
           <<" max_required_r="<<maxR<<" max_witness_b="<<maxB
           <<" calls="<<fs.calls<<" unique_states="<<fs.unique
           <<" memo_hits="<<fs.memo<<" e_cases="<<fs.e
           <<" o_run_cases="<<fs.o<<" prunes="<<fs.prunes
           <<" frontier_points="<<fs.frontierPoints
           <<" max_frontier_width="<<fs.maxWidth
           <<" peak_memo="<<fs.peakMemo<<" max_u="<<fs.maxU<<" min_w="<<fs.minW<<"\n";
  if(!unresolved)std::cout<<"ALL_BOUNDARIES_HAVE_REFINEMENT_FRONTIER_NEIGHBORHOOD\n";
  else std::cout<<"REFINEMENT_FRONTIER_RESIDUAL_REMAINS\n";
  std::cout<<"VERIFIED_REFINEMENT_FRONTIER_SCOUT\n";
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
    std::cerr<<"usage: refinement_frontier [--verify] K R\n";
    return 2;
  }
  if(K<1||K>24||R<0||R>80)return 2;

  const auto p3=powers3_for(K);
  const auto residual=build(K,p3);
  if(!check_frozen(K,residual.size()))return 12;
  return verify?verify_mode(K,R,residual):scout_mode(K,R,residual);
}
