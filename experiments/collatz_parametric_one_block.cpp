// Complete parametric one-block reverse grammar for shortcut Collatz.
//
// After the retained q14 reverse bridge, an unresolved affine predecessor is
//   p(a)=A*a+D.
// Consider EVERY continuation of the form E^e O^m, e>=0,m>=1, where
//   E(x)=2x,
//   O(x)=(2x-1)/3
// and O must be uniformly integral/odd.
//
// For fixed e, after E^e the maximum valid O-run is exactly
//   mmax = min(v3(A), v3(2^e D + 1)).
// Since O(x)<x for every positive valid x>1, if any shorter valid O-run is
// lower than the target family then the maximal valid run is lower too.
// Therefore one maximal-run check per e is complete for that e.
//
// Moreover m<=q=v3(A).  The smallest coefficient attainable for a given e is
//   A*2^e*(2/3)^q.
// This doubles when e increases.  Once it is >=2^k, no larger e can ever be
// coefficient-subcritical, so the infinite e search terminates exactly.
//
// Thus this program decides the ENTIRE infinite one-block language E^*O^+
// without a word horizon or learned constructor bank.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

static inline u128 T(u128 n){return (n&1)?(3*n+1)/2:n/2;}
static u128 iterate(u128 n,int steps){for(int i=0;i<steps;++i)n=T(n);return n;}

struct RevCert{int o;int steps;uint64_t C;uint64_t residue;};

static std::vector<std::unordered_map<uint64_t,RevCert>>
load_q14(const std::string& path,int& max_o){
  std::ifstream in(path);
  if(!in){std::cerr<<"Q14_BANK_OPEN_FAILED\n";std::exit(2);}
  std::vector<RevCert> all;max_o=0;std::string line;
  while(std::getline(in,line)){
    if(line.empty())continue;
    std::istringstream ss(line);RevCert z{};
    if(!(ss>>z.o>>z.steps>>z.C>>z.residue)){
      std::cerr<<"Q14_BANK_PARSE_FAILED\n";std::exit(3);
    }
    max_o=std::max(max_o,z.o);all.push_back(z);
  }
  std::vector<std::unordered_map<uint64_t,RevCert>> bank(max_o+1);
  for(const auto&z:all){
    auto[it,ok]=bank[z.o].emplace(z.residue,z);
    if(!ok){std::cerr<<"Q14_BANK_DUPLICATE\n";std::exit(4);}
  }
  std::cout<<"PARAMETRIC_Q14_BANK certificates="<<all.size()
           <<" max_o="<<max_o<<"\n";
  return bank;
}

struct State{uint64_t b;uint64_t dc;};
static constexpr uint64_t CMASK=63;
static State make_state(uint64_t b,uint64_t d,int c){
  if(c<0||c>=64){std::cerr<<"PACK_C_RANGE\n";std::exit(5);}
  if(d>=(UINT64_C(1)<<58)){std::cerr<<"PACK_D_RANGE\n";std::exit(6);}
  return {b,(d<<6)|uint64_t(c)};
}
static inline int state_c(const State&s){return int(s.dc&CMASK);}
static inline uint64_t state_d(const State&s){return s.dc>>6;}

static bool lower_family(i128 A,i128 D,int k,uint64_t b){
  const i128 M=i128(1)<<k;
  const i128 L=A-M;
  const i128 R=i128(b)-D;
  return A>0 && A+D>0 && L<0 && L<R;
}

static bool first_reverse_match(
    int c,uint64_t d,
    const std::vector<std::unordered_map<uint64_t,RevCert>>&bank,
    int max_o,const std::vector<uint64_t>&p3,
    RevCert&z,i128&A,i128&D){
  const int top=std::min(c,max_o);
  uint64_t mod=1;
  for(int o=1;o<=top;++o){
    mod*=3;
    auto it=bank[o].find(d%mod);
    if(it==bank[o].end())continue;
    z=it->second;
    const i128 nc=(i128(1)<<z.steps)*i128(d)-i128(z.C);
    if(nc%i128(mod)!=0){std::cerr<<"MATCH_DIV_FAIL\n";std::exit(7);}
    D=nc/i128(mod);
    A=(i128(1)<<z.steps)*i128(p3[c-z.o]);
    return true;
  }
  return false;
}

static bool deep_o_closes(
    uint64_t b,int c,uint64_t d,int k,
    const std::vector<uint64_t>&p3,
    int&used_j,i128&A,i128&D){
  if(c<2||d==UINT64_MAX)return false;
  const uint64_t dp1=d+1;
  int maxj=0;
  for(int j=1;j<=c;++j){if(dp1%p3[j])break;maxj=j;}
  for(int j=2;j<=maxj;++j){
    const uint64_t q=dp1/p3[j];
    const i128 d2=(i128(1)<<j)*i128(q)-1;
    const i128 a2=(i128(1)<<j)*i128(p3[c-j]);
    if(lower_family(a2,d2,k,b)){used_j=j;A=a2;D=d2;return true;}
  }
  return false;
}

static int v3i(i128 x,int cap=80){
  if(x<0)x=-x;
  int v=0;
  while(v<cap&&x%3==0){x/=3;++v;}
  return v;
}
static i128 powi(i128 b,int e){
  i128 x=1;
  for(int i=0;i<e;++i){
    if(x>(i128(1)<<120)/b){std::cerr<<"POWI_RANGE\n";std::exit(8);}
    x*=b;
  }
  return x;
}

struct ParamWitness{int e=0,m=0; i128 A=0,D=0;};

static bool complete_one_block_closes(
    uint64_t b,int c,uint64_t d,int k,
    const std::vector<std::unordered_map<uint64_t,RevCert>>&bank,
    int max_o,const std::vector<uint64_t>&p3,
    RevCert&base,ParamWitness&w,uint64_t&ecases,uint64_t&maxruns){
  i128 A=0,D=0;
  if(!first_reverse_match(c,d,bank,max_o,p3,base,A,D))return false;
  if(lower_family(A,D,k,b))return false; // earlier bridge already handles it.

  const int q=v3i(A);
  if(q<=0)return false;
  const i128 M=i128(1)<<k;
  const i128 p3q=powi(3,q);
  const i128 p2q=powi(2,q);

  // e is complete, not a heuristic horizon.
  for(int e=0;;++e){
    const i128 pe=powi(2,e);
    const i128 Ae=A*pe;
    const i128 De=D*pe;

    // Even with all q possible O steps, no current or larger e can recover.
    const i128 theoreticalMin=(Ae/p3q)*p2q;
    if(theoreticalMin>=M)break;

    ++ecases;
    const int m=std::min(q,v3i(De+1));
    if(m<=0)continue;
    maxruns=std::max<uint64_t>(maxruns,m);

    const i128 den=powi(3,m),tw=powi(2,m);
    if(Ae%den || (De+1)%den){
      std::cerr<<"PARAM_DIV_FAIL\n";std::exit(9);
    }
    const i128 A2=tw*(Ae/den);
    const i128 D2=tw*((De+1)/den)-1;

    // Completeness control for the monotonic maximal-O reduction:
    // explicitly inspect every shorter valid run and require that if one
    // closes, the maximal run closes too.
    bool shorter=false;
    for(int j=1;j<m;++j){
      const i128 dj=powi(3,j),tj=powi(2,j);
      const i128 Aj=tj*(Ae/dj);
      const i128 Dj=tj*((De+1)/dj)-1;
      if(lower_family(Aj,Dj,k,b))shorter=true;
    }
    const bool maximal=lower_family(A2,D2,k,b);
    if(shorter&&!maximal){
      std::cerr<<"MAXIMAL_O_MONOTONICITY_FAIL\n";std::exit(10);
    }
    if(maximal){w={e,m,A2,D2};return true;}
  }
  return false;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: parametric_future K Q14_BANK\n";return 2;}
  const int K=std::stoi(argv[1]);
  if(K<1||K>34){std::cerr<<"K_RANGE\n";return 2;}
  const std::string qpath=argv[2];

  std::vector<uint64_t>p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i){
    if(p3[i-1]>UINT64_MAX/3){std::cerr<<"P3_OVERFLOW\n";return 3;}
    p3[i]=p3[i-1]*3;
  }
  int max_o=0;
  const auto bank=load_q14(qpath,max_o);

  std::vector<State>cur{{0,0}},next;
  uint64_t totalDes=0,totalBridge=0,totalDeepO=0,totalParam=0;
  uint64_t controls=0,totalEcases=0,maxOrun=0;
  std::unordered_map<int,uint64_t> ehist,mhist;

  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1),M=UINT64_C(1)<<k;
    next.clear();
    if(cur.size()<=std::numeric_limits<size_t>::max()/2)next.reserve(cur.size()*2);
    uint64_t des=0,bridge=0,deepo=0,param=0;

    for(const State&s:cur){
      const uint64_t b0=s.b,d0=state_d(s);const int c0=state_c(s);
      for(int bit=0;bit<2;++bit){
        const uint64_t b=b0+(bit?half:0);
        const uint64_t y=d0+(bit?p3[c0]:0);
        int c=c0;uint64_t d;
        if(y&1){++c;if(y>(UINT64_MAX-1)/3){std::cerr<<"CHILD_OVERFLOW\n";return 11;}d=(3*y+1)/2;}
        else d=y/2;

        if(lower_family(i128(p3[c]),i128(d),k,b)){++des;++totalDes;continue;}

        RevCert base{};i128 A=0,D=0;
        if(first_reverse_match(c,d,bank,max_o,p3,base,A,D)&&lower_family(A,D,k,b)){
          ++bridge;++totalBridge;continue;
        }

        int oj=0;i128 oA=0,oD=0;
        if(deep_o_closes(b,c,d,k,p3,oj,oA,oD)){++deepo;++totalDeepO;continue;}

        ParamWitness w{};uint64_t ec=0,mr=0;
        if(complete_one_block_closes(b,c,d,k,bank,max_o,p3,base,w,ec,mr)){
          totalEcases+=ec;maxOrun=std::max(maxOrun,mr);
          ++param;++totalParam;++ehist[w.e];++mhist[w.m];
          if(controls<20000){
            for(uint64_t a:{1ULL,3ULL}){
              const u128 n=u128(a)*M+b;
              const u128 endpoint=u128(a)*p3[c]+d;
              const i128 pred=i128(a)*w.A+w.D;
              if(pred<=0||u128(pred)>=n||
                 iterate(n,k)!=endpoint||
                 iterate(u128(pred),base.steps+w.e+w.m)!=endpoint){
                std::cerr<<"PARAM_CONTROL_FAIL k="<<k<<" b="<<b
                         <<" e="<<w.e<<" m="<<w.m<<"\n";return 12;
              }
              ++controls;
            }
          }
          continue;
        }
        totalEcases+=ec;maxOrun=std::max(maxOrun,mr);
        next.push_back(make_state(b,d,c));
      }
    }
    std::cout<<"PARAMETRIC_ONE_BLOCK_LEVEL k="<<k
             <<" descent="<<des<<" bridge="<<bridge<<" deep_o="<<deepo
             <<" parametric="<<param<<" live="<<next.size()<<"\n";
    cur.swap(next);
  }

  std::cout<<"PARAMETRIC_ONE_BLOCK_DONE K="<<K
           <<" final_live="<<cur.size()
           <<" total_descent="<<totalDes
           <<" total_bridge="<<totalBridge
           <<" total_deep_o="<<totalDeepO
           <<" total_parametric="<<totalParam
           <<" e_cases="<<totalEcases
           <<" max_valid_o_run="<<maxOrun
           <<" controls="<<controls<<"\n";
  for(auto&kv:ehist)std::cout<<"PARAM_E_HIST e="<<kv.first<<" closed="<<kv.second<<"\n";
  for(auto&kv:mhist)std::cout<<"PARAM_M_HIST m="<<kv.first<<" closed="<<kv.second<<"\n";
  std::cout<<"VERIFIED_COMPLETE_PARAMETRIC_ESTAR_OPLUS_GRAMMAR\n";
  return 0;
}
