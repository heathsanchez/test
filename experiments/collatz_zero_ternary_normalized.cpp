// Normalized exact zero-ternary closure without materializing 3^r.
//
// For q=3^r t:
//   target slope = 2^k 3^r
//   endpoint slope = 3^(c+r).
//
// Track every reverse affine coefficient as 2^u 3^v.  Reverse:
//   E: (u,v,D)->(u+1,v,2D)
//   O: (u,v,D)->(u+1,v-1,(2D-1)/3)
// when v>0 and D == 2 mod 3.
//
// The lower-slope condition cancels the artificial zero-refinement factor:
//   2^u 3^(v-r) <= 2^k.
// Thus r can be large without giant coefficients.
//
// Complete finiteness:
// From (u,v), spending all remaining v O steps gives the smallest possible
// future coefficient (u+v,0). If that still violates the normalized target,
// no continuation can close; larger E runs only worsen it.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <tuple>
#include <vector>

using i128=__int128;
using u128=unsigned __int128;

static std::string s128(u128 x){if(!x)return "0";std::string s;while(x){s.push_back(char('0'+x%10));x/=10;}std::reverse(s.begin(),s.end());return s;}

static u128 pow3u(int n){
  u128 x=1,M=~u128(0);
  for(int i=0;i<n;++i){if(x>M/3){std::cerr<<"POW3_RANGE\n";std::exit(7);}x*=3;}
  return x;
}
static bool coef_le(int u,int v,int k,int r){
  const int z=v-r;
  if(z>=0){
    if(u>k)return false;
    const int gap=k-u;
    if(z==0)return true;
    // Need 3^z <= 2^gap. gap<=k<=24 for this branch.
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
  int u,v;u128 D;
  bool operator<(const NKey&o)const{
    if(u!=o.u)return u<o.u;if(v!=o.v)return v<o.v;return D<o.D;
  }
};
struct NStats{uint64_t nodes=0,memo=0,e=0,o=0,prunes=0,maxNodes=0;int maxU=0,maxV=0;};

static int v3u(u128 x,int cap=200){int z=0;while(z<cap&&x%3==0){x/=3;++z;}return z;}

static bool ndfs(int u,int v,u128 D,int k,int r,uint64_t b,
                 std::set<NKey>&seen,uint64_t&local,NStats&st){
  ++local;++st.nodes;st.maxU=std::max(st.maxU,u);st.maxV=std::max(st.maxV,v);
  if(D==0)return false;
  if(!seen.emplace(NKey{u,v,D}).second){++st.memo;return false;}

  if(coef_le(u,v,k,r)&&D<u128(b))return true;
  if(v<=0)return false;

  int ue=u;u128 De=D;
  const u128 MAX=~u128(0);
  for(int e=0;;++e){
    if(!future_coef_possible(ue,v,k,r)){++st.prunes;break;}
    ++st.e;

    // Avoid unsigned wrap at D=2^128-1.  Mathematically D+1=2^128,
    // which is 1 mod 3, so no O step is valid.
    const int mmax=(De==MAX)?0:std::min(v,v3u(De+1));
    u128 den=1,tw=1;
    for(int m=1;m<=mmax;++m){
      den*=3;tw*=2;++st.o;
      // Dm = 2^m*(De+1)/3^m - 1
      const u128 q=(De+1)/den;
      if(q && tw>MAX/q){std::cerr<<"D_MUL_RANGE\n";std::exit(8);}
      const u128 D2=tw*q-1;
      if(ndfs(ue+m,v-m,D2,k,r,b,seen,local,st))return true;
    }

    if(De>MAX/2){std::cerr<<"D_E_RANGE\n";std::exit(9);}
    De*=2;++ue;
  }
}
static bool normalized_closes(int c,uint64_t d,int k,int r,uint64_t b,NStats&st){
  std::set<NKey>seen;uint64_t local=0;
  bool ok=ndfs(0,c+r,u128(d),k,r,b,seen,local,st);
  st.maxNodes=std::max(st.maxNodes,local);return ok;
}

// Qualified baseline residual builder (r=0 complete affine language).
static int v3i(i128 x,int cap=80){if(x<0)x=-x;int z=0;while(z<cap&&x%3==0){x/=3;++z;}return z;}
static i128 mulc(i128 a,i128 b){if(a<0||b<0||(a&&b>(i128(1)<<120)/a)){std::cerr<<"I128_RANGE\n";std::exit(10);}return a*b;}
static i128 powi(i128 b,int e){i128 x=1;for(int i=0;i<e;++i)x=mulc(x,b);return x;}
static uint64_t child_lower(uint64_t L,int bit){if(L<=uint64_t(bit))return 0;return (L-uint64_t(bit)+1)/2;}
static bool lower_family(i128 A,i128 D,i128 M,i128 b,uint64_t L){
  i128 q=L,s=A-M;return A>0&&A*q+D>0&&s<=0&&s*q+D-b<0;
}
struct AKey{i128 A,D;bool operator<(const AKey&o)const{return A<o.A||(A==o.A&&D<o.D);}};
static bool adfs(i128 A,i128 D,i128 M,i128 b,uint64_t L,std::set<AKey>&seen){
  if(A*i128(L)+D<=0)return false;if(!seen.emplace(AKey{A,D}).second)return false;
  int rem=v3i(A);if(rem<=0)return false;i128 denAll=powi(3,rem),twAll=powi(2,rem),Ae=A,De=D;
  for(int e=0;;++e){
    if(e){Ae=mulc(Ae,2);De*=2;if(De>(i128(1)<<120)){std::cerr<<"BASE_D_RANGE\n";std::exit(11);}}
    if(mulc(Ae/denAll,twAll)>M)break;
    int mm=std::min(rem,v3i(De+1));i128 den=1,tw=1;
    for(int m=1;m<=mm;++m){den*=3;tw*=2;i128 A2=mulc(Ae/den,tw),D2=mulc((De+1)/den,tw)-1;
      if(lower_family(A2,D2,M,b,L)||adfs(A2,D2,M,b,L,seen))return true;}
  }
  return false;
}
static bool acloses(i128 A,i128 D,i128 M,i128 b,uint64_t L){
  if(lower_family(A,D,M,b,L))return true;std::set<AKey>seen;return adfs(A,D,M,b,L,seen);
}
struct State{uint64_t b,d;uint32_t c;uint64_t L;};
static std::vector<State> build(int K,const std::vector<i128>&p3){
  std::vector<State>cur{{0,0,0,2}},next;
  for(int k=1;k<=K;++k){uint64_t half=UINT64_C(1)<<(k-1);i128 M=i128(1)<<k;next.clear();
    for(auto&s:cur)for(int bit=0;bit<2;++bit){uint64_t L=child_lower(s.L,bit),b=s.b+(bit?half:0);
      i128 raw=i128(s.d)+(bit?p3[s.c]:0);uint32_t c=s.c;i128 d;if(raw&1){++c;d=(3*raw+1)/2;}else d=raw/2;
      if(acloses(p3[c],d,M,b,L))continue;next.push_back({b,uint64_t(d),c,L});}
    cur.swap(next);}
  return cur;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: normalized_zero_ternary K R\n";return 2;}
  int K=std::stoi(argv[1]),R=std::stoi(argv[2]);if(K<1||K>24||R<0||R>80)return 2;
  std::vector<i128>p3(K+2,1);for(int i=1;i<(int)p3.size();++i)p3[i]=mulc(p3[i-1],3);
  auto residual=build(K,p3);
  const std::map<int,uint64_t>frozen{{12,144},{16,1363},{20,15870},{24,172868}};
  if(auto it=frozen.find(K);it!=frozen.end()&&residual.size()!=it->second){std::cerr<<"BASELINE_DRIFT\n";return 12;}

  NStats st;std::map<int,uint64_t>hist;uint64_t unresolved=0;int maxR=-1;uint64_t maxB=0;
  for(auto&s:residual){
    if(s.L!=0){std::cerr<<"EXPECTED_L0\n";return 13;}
    bool done=false;
    for(int r=0;r<=R;++r){
      if(normalized_closes((int)s.c,s.d,K,r,s.b,st)){
        ++hist[r];if(r>maxR){maxR=r;maxB=s.b;}done=true;break;
      }
    }
    if(!done)++unresolved;
  }
  uint64_t cum=0;for(auto&kv:hist){cum+=kv.second;
    std::cout<<"NZT_CLOSURE r="<<kv.first<<" newly="<<kv.second<<" cumulative="<<cum<<" remaining="<<(residual.size()-cum)<<"\n";}
  std::cout<<"NZT_RESULT K="<<K<<" R="<<R<<" residual="<<residual.size()
           <<" closed="<<(residual.size()-unresolved)<<" unresolved="<<unresolved
           <<" max_required_r="<<maxR<<" max_witness_b="<<maxB
           <<" search_nodes="<<st.nodes<<" memo_hits="<<st.memo
           <<" e_cases="<<st.e<<" o_run_cases="<<st.o<<" prunes="<<st.prunes
           <<" max_nodes_family="<<st.maxNodes<<" max_u="<<st.maxU<<" max_v="<<st.maxV<<"\n";
  if(!unresolved)std::cout<<"ALL_BOUNDARIES_HAVE_NORMALIZED_ZERO_TERNARY_NEIGHBORHOOD\n";
  else std::cout<<"NORMALIZED_ZERO_TERNARY_RESIDUAL_REMAINS\n";
  std::cout<<"VERIFIED_NORMALIZED_ZERO_TERNARY_SCOUT\n";
}
