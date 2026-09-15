// Zero-search replay of a frozen deep reverse constructor bank.
//
// Discovery is performed elsewhere on B<=24.  This evaluator receives:
//   1) the frozen q14 first-contraction donor bank;
//   2) a frozen set of exact deep continuation constructors.
//
// It performs NO continuation-word search.  For each unresolved affine family
// it applies only the finite supplied constructor bank.
//
// A deep constructor row is:
//   o steps C residue word
//
// where (o,steps,C,residue) identifies the exact prefix-free q14 donor and
// word is the already-discovered continuation over reverse E/O operations.
//
// This is an untouched-future transfer test in the RealityGraph sense:
// capability learned on earlier worlds is compiled, frozen, and applied to
// later binary depths with zero new constructor discovery.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

static inline u128 T(u128 n){return (n&1)?(3*n+1)/2:n/2;}
static u128 iterate(u128 n,int steps){for(int i=0;i<steps;++i)n=T(n);return n;}

struct RevCert{int o;int steps;uint64_t C;uint64_t residue;};

static std::string cert_key(const RevCert& z){
  return std::to_string(z.o)+":"+
         std::to_string(z.steps)+":"+
         std::to_string(z.C)+":"+
         std::to_string(z.residue);
}

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
  for(const auto& z:all){
    auto [it,ok]=bank[z.o].emplace(z.residue,z);
    if(!ok){std::cerr<<"Q14_BANK_DUPLICATE\n";std::exit(4);}
  }
  std::cout<<"COMPILED_Q14_BANK certificates="<<all.size()
           <<" max_o="<<max_o<<"\n";
  return bank;
}

struct DeepBank {
  std::unordered_map<std::string,std::vector<std::string>> words;
  uint64_t exact_rows=0;
};

static DeepBank load_deep(const std::string& path){
  std::ifstream in(path);
  if(!in){std::cerr<<"DEEP_BANK_OPEN_FAILED\n";std::exit(5);}
  DeepBank out;
  std::string line;
  while(std::getline(in,line)){
    if(line.empty())continue;
    std::istringstream ss(line);
    RevCert z{};std::string word;
    if(!(ss>>z.o>>z.steps>>z.C>>z.residue>>word)){
      std::cerr<<"DEEP_BANK_PARSE_FAILED "<<line<<"\n";std::exit(6);
    }
    auto& v=out.words[cert_key(z)];
    if(std::find(v.begin(),v.end(),word)==v.end())v.push_back(word);
    ++out.exact_rows;
  }
  uint64_t unique_words=0;
  for(auto& [k,v]:out.words){
    std::sort(v.begin(),v.end(),
      [](const std::string&a,const std::string&b){
        if(a.size()!=b.size())return a.size()<b.size();
        return a<b;
      });
    unique_words+=v.size();
  }
  std::cout<<"COMPILED_DEEP_BANK"
           <<" exact_rows="<<out.exact_rows
           <<" donor_keys="<<out.words.size()
           <<" unique_words="<<unique_words<<"\n";
  return out;
}

struct State{uint64_t b;uint64_t dc;};
static constexpr uint64_t CMASK=63;

static State make_state(uint64_t b,uint64_t d,int c){
  if(c<0||c>=64){std::cerr<<"PACK_C_RANGE\n";std::exit(7);}
  if(d>=(UINT64_C(1)<<58)){std::cerr<<"PACK_D_RANGE\n";std::exit(8);}
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
    const std::vector<std::unordered_map<uint64_t,RevCert>>& bank,
    int max_o,const std::vector<uint64_t>& p3,
    RevCert& z,i128& A,i128& D){
  const int top=std::min(c,max_o);
  uint64_t mod=1;
  for(int o=1;o<=top;++o){
    mod*=3;
    auto it=bank[o].find(d%mod);
    if(it==bank[o].end())continue;
    z=it->second;
    const i128 nc=(i128(1)<<z.steps)*i128(d)-i128(z.C);
    if(nc%i128(mod)!=0){std::cerr<<"MATCH_DIV_FAIL\n";std::exit(9);}
    D=nc/i128(mod);
    A=(i128(1)<<z.steps)*i128(p3[c-z.o]);
    return true;
  }
  return false;
}

static bool deep_o_closes(
    uint64_t b,int c,uint64_t d,int k,
    const std::vector<uint64_t>& p3,
    int& used_j,i128& A,i128& D){
  if(c<2 || d==UINT64_MAX)return false;
  const uint64_t dp1=d+1;
  int maxj=0;
  for(int j=1;j<=c;++j){
    if(dp1%p3[j])break;
    maxj=j;
  }
  for(int j=2;j<=maxj;++j){
    const uint64_t q=dp1/p3[j];
    const i128 d2=(i128(1)<<j)*i128(q)-1;
    const i128 a2=(i128(1)<<j)*i128(p3[c-j]);
    if(lower_family(a2,d2,k,b)){
      used_j=j;A=a2;D=d2;return true;
    }
  }
  return false;
}

static bool apply_word(
    i128 A,i128 D,const std::string& word,
    i128& outA,i128& outD){
  for(char ch:word){
    if(ch=='E'){
      A*=2;D*=2;
    }else if(ch=='O'){
      if(A%3!=0)return false;
      const i128 z=2*D-1;
      if(z%3!=0)return false;
      A=2*(A/3);
      D=z/3;
      if(D%2==0)return false;
    }else{
      std::cerr<<"DEEP_BANK_BAD_WORD\n";std::exit(10);
    }
  }
  outA=A;outD=D;return true;
}

static bool compiled_deep_closes(
    uint64_t b,int c,uint64_t d,int k,
    const std::vector<std::unordered_map<uint64_t,RevCert>>& bank,
    int max_o,const std::vector<uint64_t>& p3,
    const DeepBank& deep,
    RevCert& used,std::string& used_word,i128& outA,i128& outD){
  RevCert z{};i128 A=0,D=0;
  if(!first_reverse_match(c,d,bank,max_o,p3,z,A,D))return false;

  auto it=deep.words.find(cert_key(z));
  if(it==deep.words.end())return false;

  for(const std::string& word:it->second){
    i128 a2=0,d2=0;
    if(!apply_word(A,D,word,a2,d2))continue;
    if(lower_family(a2,d2,k,b)){
      used=z;used_word=word;outA=a2;outD=d2;return true;
    }
  }
  return false;
}

int main(int argc,char**argv){
  if(argc!=4){
    std::cerr<<"usage: compiled_future K Q14_BANK DEEP_BANK\n";return 2;
  }
  const int K=std::stoi(argv[1]);
  if(K<1||K>34){std::cerr<<"K_OUT_OF_RANGE\n";return 2;}
  const std::string qpath=argv[2],dpath=argv[3];

  std::vector<uint64_t> p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i){
    if(p3[i-1]>UINT64_MAX/3){std::cerr<<"P3_OVERFLOW\n";return 3;}
    p3[i]=p3[i-1]*3;
  }

  int max_o=0;
  const auto bank=load_q14(qpath,max_o);
  const DeepBank deep=load_deep(dpath);

  std::vector<State> cur,next;
  cur.push_back(make_state(0,0,0));

  uint64_t total_descent=0,total_bridge=0,total_deep_o=0,total_compiled=0;
  uint64_t controls=0;

  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1);
    const uint64_t M=UINT64_C(1)<<k;
    next.clear();
    if(cur.size()<=std::numeric_limits<size_t>::max()/2)next.reserve(cur.size()*2);

    uint64_t descent=0,bridge=0,deep_o=0,compiled=0;

    for(const State&s:cur){
      const uint64_t b0=s.b,d0=state_d(s);
      const int c0=state_c(s);

      for(int e=0;e<2;++e){
        const uint64_t b=b0+(e?half:0);
        const uint64_t y=d0+(e?p3[c0]:0);
        int c=c0;uint64_t d;
        if(y&1){
          ++c;
          if(y>(UINT64_MAX-1)/3){std::cerr<<"CHILD_D_OVERFLOW\n";return 11;}
          d=(3*y+1)/2;
        }else d=y/2;

        if(lower_family(i128(p3[c]),i128(d),k,b)){
          ++descent;++total_descent;continue;
        }

        RevCert base{};i128 A=0,D=0;
        if(first_reverse_match(c,d,bank,max_o,p3,base,A,D) &&
           lower_family(A,D,k,b)){
          ++bridge;++total_bridge;continue;
        }

        int oj=0;i128 oA=0,oD=0;
        if(deep_o_closes(b,c,d,k,p3,oj,oA,oD)){
          ++deep_o;++total_deep_o;continue;
        }

        RevCert used{};std::string word;i128 qA=0,qD=0;
        if(compiled_deep_closes(
              b,c,d,k,bank,max_o,p3,deep,used,word,qA,qD)){
          ++compiled;++total_compiled;

          if(controls<20000){
            for(uint64_t a:{1ULL,3ULL}){
              const u128 n=u128(a)*M+b;
              const u128 m=u128(a)*p3[c]+d;
              const i128 ps=i128(a)*qA+qD;
              if(ps<=0||u128(ps)>=n||
                 iterate(n,k)!=m||
                 iterate(u128(ps),used.steps+int(word.size()))!=m){
                std::cerr<<"COMPILED_TRANSFER_CONTROL_FAILED"
                         <<" k="<<k<<" b="<<b<<" word="<<word<<"\n";
                return 12;
              }
              ++controls;
            }
          }
          continue;
        }

        next.push_back(make_state(b,d,c));
      }
    }

    std::cout<<"COMPILED_FUTURE_LEVEL"
             <<" k="<<k
             <<" parents="<<cur.size()
             <<" descent="<<descent
             <<" bridge="<<bridge
             <<" deep_o="<<deep_o
             <<" compiled="<<compiled
             <<" live="<<next.size()
             <<" odd_live_fraction="
             <<(double(next.size())/double(UINT64_C(1)<<(k-1)))<<"\n";
    cur.swap(next);
  }

  std::cout<<"COMPILED_FUTURE_DONE"
           <<" K="<<K
           <<" final_live="<<cur.size()
           <<" total_descent="<<total_descent
           <<" total_bridge="<<total_bridge
           <<" total_deep_o="<<total_deep_o
           <<" total_compiled="<<total_compiled
           <<" controls="<<controls
           <<" new_search_calls=0\n";
  std::cout<<"VERIFIED_ZERO_SEARCH_COMPILED_FUTURE_TRANSFER\n";
  return 0;
}
