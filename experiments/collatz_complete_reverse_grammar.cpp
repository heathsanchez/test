// Complete finite decision procedure for the infinite reverse E/O grammar
// after a retained Collatz q14 bridge.
//
// Given an unresolved affine predecessor p(a)=A*a+D and target family
// n(a)=2^k*a+b, reverse operations are
//   E: (A,D) -> (2A,2D)
//   O: (A,D) -> (2A/3,(2D-1)/3)
// with O allowed only when the result is uniformly integral and odd.
//
// Every useful word can be uniquely written as blocks
//   E^e1 O^m1 E^e2 O^m2 ... E^er O^mr
// with ei>=0, mi>=1. Terminal E operations can never turn a non-lower positive
// predecessor into a lower one and are therefore irrelevant.
//
// Completeness is finite:
//  * Let q=v3(A). E does not change q; every O consumes one factor 3.
//    Hence every branch has at most q total O operations and at most q blocks.
//  * For a candidate E-run e, even the best possible use of all q remaining
//    O steps has coefficient A*2^e*(2/3)^q. Once this is >=2^k, no current or
//    larger e can ever become coefficient-subcritical. Thus each E choice is
//    bounded exactly.
//  * At each e, all uniformly valid O-run lengths 1..mmax are enumerated,
//    mmax=min(v3(A),v3(2^e D+1)).
//
// Therefore the DFS exhausts every reverse E/O word that could possibly yield
// a uniform lower affine consequence. No word horizon is used.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <set>
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
load_q14(const std::string&path,int&max_o){
  std::ifstream in(path);
  if(!in){std::cerr<<"Q14_BANK_OPEN_FAILED\n";std::exit(2);}
  std::vector<RevCert>all;max_o=0;std::string line;
  while(std::getline(in,line)){
    if(line.empty())continue;
    std::istringstream ss(line);RevCert z{};
    if(!(ss>>z.o>>z.steps>>z.C>>z.residue)){
      std::cerr<<"Q14_BANK_PARSE_FAILED\n";std::exit(3);
    }
    max_o=std::max(max_o,z.o);all.push_back(z);
  }
  std::vector<std::unordered_map<uint64_t,RevCert>>bank(max_o+1);
  for(const auto&z:all){
    auto[it,ok]=bank[z.o].emplace(z.residue,z);
    if(!ok){std::cerr<<"Q14_BANK_DUPLICATE\n";std::exit(4);}
  }
  std::cout<<"COMPLETE_GRAMMAR_Q14_BANK certificates="<<all.size()
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
    uint64_t b,int c,uint64_t d,int k,const std::vector<uint64_t>&p3,
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
  int v=0;while(v<cap&&x%3==0){x/=3;++v;}return v;
}
static i128 mul_checked(i128 a,i128 b){
  if(a<0||b<0){std::cerr<<"NEGATIVE_COEF_RANGE\n";std::exit(8);}
  if(a && b>(i128(1)<<120)/a){std::cerr<<"I128_RANGE\n";std::exit(9);}
  return a*b;
}
static i128 powi(i128 b,int e){
  i128 x=1;for(int i=0;i<e;++i)x=mul_checked(x,b);return x;
}

struct GrammarStats{
  uint64_t nodes=0;
  uint64_t memo_hits=0;
  uint64_t e_cases=0;
  uint64_t o_run_cases=0;
  uint64_t coefficient_prunes=0;
  uint64_t max_nodes_one_family=0;
  int max_blocks=0;
  int max_word_steps=0;
};

struct Witness{
  i128 A=0,D=0;
  std::string word;
};

struct Key{
  i128 A,D;
  bool operator<(const Key&o)const{
    return A<o.A||(A==o.A&&D<o.D);
  }
};

static bool exhaustive_reverse_dfs(
    i128 A,i128 D,int k,uint64_t b,
    std::set<Key>&seen,
    GrammarStats&st,
    std::string&path,
    int blocks,
    Witness&w){
  ++st.nodes;
  st.max_blocks=std::max(st.max_blocks,blocks);
  st.max_word_steps=std::max(st.max_word_steps,(int)path.size());

  if(!seen.emplace(Key{A,D}).second){++st.memo_hits;return false;}

  const int q=v3i(A);
  if(q<=0)return false;
  const i128 M=i128(1)<<k;
  const i128 p3q=powi(3,q),p2q=powi(2,q);

  i128 Ae=A,De=D;
  for(int e=0;;++e){
    if(e>0){
      Ae=mul_checked(Ae,2);
      De*=2;
      if(De>(i128(1)<<120)||De<-(i128(1)<<120)){
        std::cerr<<"D_RANGE\n";std::exit(10);
      }
    }

    // Rigorous lower bound on every descendant coefficient from this E-run:
    // use all q remaining O factors. Larger e only doubles this bound.
    if(Ae%p3q!=0){std::cerr<<"COEF_V3_INVARIANT_FAIL\n";std::exit(11);}
    const i128 amin=mul_checked(Ae/p3q,p2q);
    if(amin>=M){++st.coefficient_prunes;break;}
    ++st.e_cases;

    const int mmax=std::min(q,v3i(De+1));
    if(mmax<=0)continue;

    i128 den=1,tw=1;
    for(int m=1;m<=mmax;++m){
      den=mul_checked(den,3);tw=mul_checked(tw,2);
      ++st.o_run_cases;
      if(Ae%den||(De+1)%den){
        std::cerr<<"BLOCK_DIV_FAIL\n";std::exit(12);
      }
      const i128 A2=mul_checked(Ae/den,tw);
      const i128 D2=mul_checked((De+1)/den,tw)-1;

      const size_t old=path.size();
      path.append(e,'E');
      path.append(m,'O');

      if(lower_family(A2,D2,k,b)){
        w={A2,D2,path};
        return true;
      }
      if(exhaustive_reverse_dfs(A2,D2,k,b,seen,st,path,blocks+1,w))
        return true;
      path.resize(old);
    }
  }
  return false;
}

static bool complete_reverse_closes(
    uint64_t b,int c,uint64_t d,int k,
    const std::vector<std::unordered_map<uint64_t,RevCert>>&bank,
    int max_o,const std::vector<uint64_t>&p3,
    RevCert&base,Witness&w,GrammarStats&global){
  i128 A=0,D=0;
  if(!first_reverse_match(c,d,bank,max_o,p3,base,A,D))return false;
  if(lower_family(A,D,k,b))return false;

  std::set<Key>seen;
  GrammarStats local;
  std::string path;
  const bool ok=exhaustive_reverse_dfs(A,D,k,b,seen,local,path,0,w);
  local.max_nodes_one_family=local.nodes;

  global.nodes+=local.nodes;
  global.memo_hits+=local.memo_hits;
  global.e_cases+=local.e_cases;
  global.o_run_cases+=local.o_run_cases;
  global.coefficient_prunes+=local.coefficient_prunes;
  global.max_nodes_one_family=std::max(global.max_nodes_one_family,local.nodes);
  global.max_blocks=std::max(global.max_blocks,local.max_blocks);
  global.max_word_steps=std::max(global.max_word_steps,local.max_word_steps);
  return ok;
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: complete_reverse K Q14_BANK\n";return 2;}
  const int K=std::stoi(argv[1]);
  if(K<1||K>32){std::cerr<<"K_RANGE\n";return 2;}
  const std::string qpath=argv[2];

  std::vector<uint64_t>p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i){
    if(p3[i-1]>UINT64_MAX/3){std::cerr<<"P3_OVERFLOW\n";return 3;}
    p3[i]=p3[i-1]*3;
  }
  int max_o=0;const auto bank=load_q14(qpath,max_o);

  std::vector<State>cur{{0,0}},next;
  uint64_t totalDes=0,totalBridge=0,totalDeepO=0,totalGrammar=0,controls=0;
  GrammarStats gst;
  std::map<int,uint64_t>blocksHist,stepsHist;

  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1),M=UINT64_C(1)<<k;
    next.clear();
    if(cur.size()<=std::numeric_limits<size_t>::max()/2)next.reserve(cur.size()*2);
    uint64_t des=0,bridge=0,deepo=0,grammar=0;

    for(const State&s:cur){
      const uint64_t b0=s.b,d0=state_d(s);const int c0=state_c(s);
      for(int bit=0;bit<2;++bit){
        const uint64_t b=b0+(bit?half:0);
        const uint64_t y=d0+(bit?p3[c0]:0);
        int c=c0;uint64_t d;
        if(y&1){++c;if(y>(UINT64_MAX-1)/3){std::cerr<<"CHILD_OVERFLOW\n";return 13;}d=(3*y+1)/2;}
        else d=y/2;

        if(lower_family(i128(p3[c]),i128(d),k,b)){++des;++totalDes;continue;}

        RevCert base{};i128 A=0,D=0;
        if(first_reverse_match(c,d,bank,max_o,p3,base,A,D)&&lower_family(A,D,k,b)){
          ++bridge;++totalBridge;continue;
        }

        int oj=0;i128 oA=0,oD=0;
        if(deep_o_closes(b,c,d,k,p3,oj,oA,oD)){++deepo;++totalDeepO;continue;}

        Witness w{};
        if(complete_reverse_closes(b,c,d,k,bank,max_o,p3,base,w,gst)){
          ++grammar;++totalGrammar;
          int blocks=0;char prev=0;
          for(char ch:w.word){if(ch=='O'&&prev!='O')++blocks;prev=ch;}
          ++blocksHist[blocks];++stepsHist[(int)w.word.size()];

          if(controls<30000){
            for(uint64_t a:{1ULL,3ULL}){
              const u128 n=u128(a)*M+b;
              const u128 endpoint=u128(a)*p3[c]+d;
              const i128 pred=i128(a)*w.A+w.D;
              if(pred<=0||u128(pred)>=n||
                 iterate(n,k)!=endpoint||
                 iterate(u128(pred),base.steps+(int)w.word.size())!=endpoint){
                std::cerr<<"COMPLETE_GRAMMAR_CONTROL_FAIL k="<<k<<" b="<<b
                         <<" word="<<w.word<<"\n";return 14;
              }
              ++controls;
            }
          }
          continue;
        }

        next.push_back(make_state(b,d,c));
      }
    }
    std::cout<<"COMPLETE_REVERSE_GRAMMAR_LEVEL k="<<k
             <<" descent="<<des<<" bridge="<<bridge<<" deep_o="<<deepo
             <<" grammar="<<grammar<<" live="<<next.size()<<"\n";
    cur.swap(next);
  }

  std::cout<<"COMPLETE_REVERSE_GRAMMAR_DONE K="<<K
           <<" final_live="<<cur.size()
           <<" total_descent="<<totalDes
           <<" total_bridge="<<totalBridge
           <<" total_deep_o="<<totalDeepO
           <<" total_grammar="<<totalGrammar
           <<" search_nodes="<<gst.nodes
           <<" memo_hits="<<gst.memo_hits
           <<" e_cases="<<gst.e_cases
           <<" o_run_cases="<<gst.o_run_cases
           <<" coefficient_prunes="<<gst.coefficient_prunes
           <<" max_nodes_one_family="<<gst.max_nodes_one_family
           <<" max_blocks="<<gst.max_blocks
           <<" max_word_steps="<<gst.max_word_steps
           <<" controls="<<controls<<"\n";
  for(auto&kv:blocksHist)std::cout<<"COMPLETE_BLOCKS_HIST blocks="<<kv.first<<" closed="<<kv.second<<"\n";
  for(auto&kv:stepsHist)std::cout<<"COMPLETE_STEPS_HIST steps="<<kv.first<<" closed="<<kv.second<<"\n";
  std::cout<<"VERIFIED_COMPLETE_FINITE_REVERSE_EO_GRAMMAR\n";
  return 0;
}
