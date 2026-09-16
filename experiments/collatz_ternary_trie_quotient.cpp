// Canonical Collatz survivor quotient diagnostic.
//
// Measures how much of the canonical 2/3-adic survivor tree is redundant
// after quotienting by the exact forward invariant
//
//   B = 2^A x - 3^j r.
//
// Ternary refinement leaves B invariant. A forward valuation step a obeys
//
//   B' = 3 B + 2^A.
//
// The diagnostic also records the surviving valuation alphabet (last a and
// maximum a seen on a path). It reuses the exact canonical consequence rules;
// UNKNOWN remains UNKNOWN.

#include <algorithm>
#include <array>
#include <functional>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

using u128 = unsigned __int128;
using i128 = __int128;

struct State {
  u128 r, x;
  int j, A, k;
  int last_a, max_a;
  u128 B;
};

static std::vector<u128> P3;

static std::string s128(u128 z) {
  if (!z) return "0";
  std::string s;
  while (z) { s.push_back(char('0' + z % 10)); z /= 10; }
  std::reverse(s.begin(), s.end());
  return s;
}

static int v2(u128 z) {
  if (!z) return 128;
  uint64_t lo=(uint64_t)z;
  return lo ? __builtin_ctzll(lo)
            : 64 + __builtin_ctzll((uint64_t)(z>>64));
}
static int v3(u128 z,int cap=128) {
  int c=0; while(c<cap && z%3==0){z/=3;++c;} return c;
}
static u128 Ncoef(const State&s) {
  if(s.A+1>=126){std::cerr<<"N_RANGE\n";std::exit(20);}
  return (u128(1)<<(s.A+1))*P3.at(s.k);
}
static u128 Xcoef(const State&s) {
  return u128(2)*P3.at(s.j+s.k);
}
static u128 pow2A(int A) {
  if(A<0||A>=127){std::cerr<<"A_RANGE\n";std::exit(21);}
  return u128(1)<<A;
}
static uint64_t invodd64(uint64_t a,int bits) {
  uint64_t x=a;
  x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;x*=2-a*x;
  if(bits==64)return x;
  return x&((UINT64_C(1)<<bits)-1);
}

struct Interval {
  enum Kind{EMPTY,ALL,PREFIX,SUFFIX}kind=EMPTY;
  u128 bound=0;
};
static Interval lt_interval(i128 slope,i128 base) {
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
static bool covers_all(const Interval&a,const Interval&b) {
  if(a.kind==Interval::ALL||b.kind==Interval::ALL)return true;
  if(a.kind==Interval::PREFIX&&b.kind==Interval::SUFFIX)return b.bound<=a.bound+1;
  if(b.kind==Interval::PREFIX&&a.kind==Interval::SUFFIX)return a.bound<=b.bound+1;
  return false;
}

struct Classification {bool closed=false,partial=false;int uniform_o=0;};
static Classification classify(const State&s) {
  const u128 N=Ncoef(s),X=Xcoef(s);
  const Interval direct=lt_interval(i128(X)-i128(N),i128(s.x)-i128(s.r));
  const int o=std::min(v3(s.x+1),v3(X));
  Interval deep;
  if(o>0){
    const u128 den=P3[o],tw=u128(1)<<o;
    const u128 p0=tw*((s.x+1)/den)-1;
    const u128 P=tw*(X/den);
    if(p0!=0)deep=lt_interval(i128(P)-i128(N),i128(p0)-i128(s.r));
  }
  return {covers_all(direct,deep),
          !covers_all(direct,deep) &&
            (direct.kind!=Interval::EMPTY||deep.kind!=Interval::EMPTY),
          o};
}

static void verify_B(const State&s) {
  const u128 lhs=pow2A(s.A)*s.x;
  const u128 rhs=P3.at(s.j)*s.r;
  if(lhs<rhs || lhs-rhs!=s.B){
    std::cerr<<"B_IDENTITY_FAIL j="<<s.j<<" A="<<s.A<<" k="<<s.k<<"\n";
    std::exit(22);
  }
}

static State refine3(const State&s,int e) {
  const u128 N=Ncoef(s),X=Xcoef(s);
  State z{s.r+N*u128(e),s.x+X*u128(e),s.j,s.A,s.k+1,
          s.last_a,s.max_a,s.B};
  verify_B(z);
  return z;
}

static State extend_forward(const State&s,int a) {
  if(a<1||a>=63||s.A+a+1>=126){std::cerr<<"FORWARD_RANGE\n";std::exit(23);}
  const u128 N=Ncoef(s),X=Xcoef(s);
  const uint64_t mod=UINT64_C(1)<<a,mask=mod-1;
  const u128 B0=(3*s.x+1)>>1;
  const u128 C=(3*X)>>1;
  const uint64_t cc=(uint64_t)(C&mask);
  if(!(cc&1)){std::cerr<<"COEF_NOT_ODD\n";std::exit(24);}
  const uint64_t q0=(uint64_t)((u128(
      ((UINT64_C(1)<<(a-1))-(uint64_t)(B0&mask))&mask)
      *invodd64(cc,a))&mask);

  State z;
  z.r=s.r+N*u128(q0);
  const u128 xx=s.x+X*u128(q0);
  const u128 numer=3*xx+1;
  if(v2(numer)!=a){std::cerr<<"VALUATION_FAIL\n";std::exit(25);}
  z.x=numer>>a;
  z.j=s.j+1;z.A=s.A+a;z.k=s.k;
  z.last_a=a;z.max_a=std::max(s.max_a,a);
  z.B=3*s.B+pow2A(s.A);
  verify_B(z);
  return z;
}

static int forward_tail_start(const State&s) {
  const u128 N=Ncoef(s),X=Xcoef(s);
  const int a0=v2(3*s.x+1);
  int a=std::max(1,a0+1);
  for(;;++a){
    if(a>=63||s.A+a+1>=126){std::cerr<<"TAIL_RANGE\n";std::exit(26);}
    const u128 two=u128(1)<<a;
    if(3*X<two*N && 3*s.x+1+3*X<two*(s.r+N))return a;
  }
}

struct RevAff{u128 a,d;};
static bool reverse_closes(const State&s,int&used,uint64_t&expanded) {
  const u128 N=Ncoef(s);
  RevAff z{Xcoef(s),s.x};
  const int maxDepth=s.j+s.k;
  for(int depth=1;depth<=maxDepth;++depth){
    if(z.a%3!=0)break;
    int e=-1;
    if(z.d%3==2)e=0;
    else if(z.d%3==1)e=1;
    else break;
    ++expanded;
    const u128 mul=u128(1)<<(e+1);
    const u128 na=mul*z.a,nd=mul*z.d-1;
    if(na%3||nd%3){std::cerr<<"REV_DIV_FAIL\n";std::exit(27);}
    z={na/3,nd/3};
    if(z.d>0 && z.a<=N && z.d<s.r){used=depth;return true;}
  }
  return false;
}

struct Stats {
  uint64_t closed=0,macro=0,splits=0,expanded=0,partial=0;
};
static void merge(Stats&a,const Stats&b){
  a.closed+=b.closed;a.macro+=b.macro;a.splits+=b.splits;
  a.expanded+=b.expanded;a.partial+=b.partial;
}

static void refine_consequence(const State&s,int budget,
                               std::vector<State>&out,Stats&st) {
  const auto c=classify(s);
  if(c.closed){++st.closed;return;}
  if(c.partial)++st.partial;
  int used=0;uint64_t ex=0;
  if(reverse_closes(s,used,ex)){++st.macro;st.expanded+=ex;return;}
  st.expanded+=ex;

  if(budget>0){
    std::vector<State>trial;Stats ts;
    for(int e=0;e<3;++e)refine_consequence(refine3(s,e),budget-1,trial,ts);
    int K=s.k;
    for(const auto&z:trial)K=std::max(K,z.k);
    u128 sm=0;
    for(const auto&z:trial)sm+=P3.at(K-z.k);
    const u128 pm=P3.at(K-s.k);
    if(sm<pm){
      ++st.splits;merge(st,ts);
      out.insert(out.end(),trial.begin(),trial.end());
      return;
    }
    st.expanded+=ts.expanded;
  }
  out.push_back(s);
}

struct ABKey {
  int A;
  u128 B;
  bool operator<(const ABKey&o)const{
    if(A!=o.A)return A<o.A;
    return B<o.B;
  }
};
struct ABKKey {
  int A,k;
  u128 B;
  bool operator<(const ABKKey&o)const{
    if(A!=o.A)return A<o.A;
    if(B!=o.B)return B<o.B;
    return k<o.k;
  }
};


struct TrieNode {
  int ch[3] = {-1,-1,-1};
  bool leaf=false;
};

static uint32_t ternary_shape_signature(
    const std::vector<const State*>& states,
    std::map<std::array<uint32_t,3>,uint32_t>& intern,
    uint32_t& nextSig,
    uint64_t& nodesBuilt,
    int& maxDepthSeen) {
  std::vector<TrieNode> trie(1);
  for (const State* sp: states) {
    const State& st=*sp;
    const u128 N0=u128(1)<<(st.A+1);
    const u128 r0=st.r%N0;
    if(r0==0 || st.r<r0 || (st.r-r0)%N0!=0){
      std::cerr<<"TERNARY_ROOT_RECOVERY_FAIL\n";std::exit(40);
    }
    const u128 t=(st.r-r0)/N0;
    if(t>=P3.at(st.k)){
      std::cerr<<"TERNARY_DIGIT_RANGE_FAIL\n";std::exit(41);
    }
    int node=0;
    for(int i=0;i<st.k;++i){
      if(trie[node].leaf){
        std::cerr<<"TERNARY_PREFIX_CONFLICT_ANCESTOR\n";std::exit(42);
      }
      const int e=int((t/P3.at(i))%3);
      if(trie[node].ch[e]<0){
        trie[node].ch[e]=int(trie.size());
        trie.push_back(TrieNode{});
      }
      node=trie[node].ch[e];
    }
    if(trie[node].leaf){
      std::cerr<<"TERNARY_DUPLICATE_LEAF\n";std::exit(43);
    }
    if(trie[node].ch[0]>=0||trie[node].ch[1]>=0||trie[node].ch[2]>=0){
      std::cerr<<"TERNARY_PREFIX_CONFLICT_DESCENDANT\n";std::exit(44);
    }
    trie[node].leaf=true;
    maxDepthSeen=std::max(maxDepthSeen,st.k);
  }
  nodesBuilt+=trie.size();

  std::function<uint32_t(int)> sig=[&](int u)->uint32_t{
    if(trie[u].leaf)return 1; // whole surviving cylinder
    std::array<uint32_t,3> key{0,0,0}; // 0 = killed/absent
    for(int e=0;e<3;++e)
      if(trie[u].ch[e]>=0)key[e]=sig(trie[u].ch[e]);
    auto it=intern.find(key);
    if(it==intern.end())it=intern.emplace(key,nextSig++).first;
    return it->second;
  };
  return sig(0);
}

static long double weight(const State&s){
  return std::ldexp(std::pow((long double)3.0,-s.k),-s.A);
}

int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: quotient DEPTH R\n";return 2;}
  const int DEPTH=std::stoi(argv[1]),R=std::stoi(argv[2]);
  if(DEPTH<1||DEPTH>16||R<0||R>3)return 2;

  P3.resize(128);P3[0]=1;
  for(int i=1;i<(int)P3.size();++i)P3[i]=P3[i-1]*3;

  // At depth zero B = 1*3 - 1*3 = 0.
  std::vector<State>live{{3,3,0,0,0,0,0,0}};
  verify_B(live[0]);

  for(int depth=1;depth<=DEPTH;++depth){
    std::vector<State>next;Stats st;
    for(const auto&p:live){
      const int tail=forward_tail_start(p);
      for(int a=1;a<tail;++a)
        refine_consequence(extend_forward(p,a),R,next,st);
    }

    std::set<int> As;
    std::set<ABKey> AB;
    std::set<ABKKey> ABK;
    std::map<int,uint64_t> lastCount,maxCount;
    std::map<int,long double> lastMass,maxMass;
    std::map<ABKey,uint64_t> mult;
    long double rho=0;
    int largestLast=0,largestMax=0;
    for(const auto&s:next){
      verify_B(s);
      As.insert(s.A);
      AB.insert({s.A,s.B});
      ABK.insert({s.A,s.k,s.B});
      ++lastCount[s.last_a];++maxCount[s.max_a];
      lastMass[s.last_a]+=weight(s);maxMass[s.max_a]+=weight(s);
      ++mult[{s.A,s.B}];
      rho+=weight(s);
      largestLast=std::max(largestLast,s.last_a);
      largestMax=std::max(largestMax,s.max_a);
    }
    uint64_t maxMult=0;
    for(const auto&kv:mult)maxMult=std::max(maxMult,kv.second);

    std::cout<<"FORWARD_B_QUOTIENT_LEVEL depth="<<depth
             <<" R="<<R
             <<" survivors="<<next.size()
             <<" density="<<(double)rho
             <<" unique_A="<<As.size()
             <<" unique_AB="<<AB.size()
             <<" unique_ABK="<<ABK.size()
             <<" compression_AB="<<(AB.empty()?0.0:double(next.size())/double(AB.size()))
             <<" compression_ABK="<<(ABK.empty()?0.0:double(next.size())/double(ABK.size()))
             <<" max_AB_multiplicity="<<maxMult
             <<" largest_last_a="<<largestLast
             <<" largest_path_a="<<largestMax
             <<" partial="<<st.partial
             <<" ternary_splits="<<st.splits
             <<"\n";

    std::cout<<"LAST_A_HIST depth="<<depth;
    for(const auto&kv:lastCount)
      std::cout<<" a"<<kv.first<<"="<<kv.second<<":"<<(double)lastMass[kv.first];
    std::cout<<"\n";

    std::cout<<"MAX_A_HIST depth="<<depth;
    for(const auto&kv:maxCount)
      std::cout<<" a"<<kv.first<<"="<<kv.second<<":"<<(double)maxMass[kv.first];
    std::cout<<"\n";

    // Exact ternary-prefix-code quotient above each forward (A,B) state.
    std::map<ABKey,std::vector<const State*>> groups;
    for(const auto&st:next)groups[{st.A,st.B}].push_back(&st);
    std::map<std::array<uint32_t,3>,uint32_t> shapeIntern;
    uint32_t nextShape=2; // 0 absent/killed, 1 whole surviving leaf
    std::map<uint32_t,uint64_t> rootFreq;
    uint64_t trieNodes=0;
    int trieMaxDepth=0;
    for(auto&kv:groups){
      const uint32_t root=ternary_shape_signature(
          kv.second,shapeIntern,nextShape,trieNodes,trieMaxDepth);
      ++rootFreq[root];
    }
    uint64_t largestRootClass=0;
    for(const auto&kv:rootFreq)largestRootClass=std::max(largestRootClass,kv.second);
    std::cout<<"TERNARY_TRIE_QUOTIENT_LEVEL depth="<<depth
             <<" R="<<R
             <<" forward_AB_states="<<groups.size()
             <<" distinct_root_shapes="<<rootFreq.size()
             <<" distinct_subtree_shapes="<<nextShape
             <<" total_trie_nodes="<<trieNodes
             <<" leaf_cylinders="<<next.size()
             <<" trie_compression="<<(trieNodes?double(next.size())/double(trieNodes):0.0)
             <<" largest_root_shape_class="<<largestRootClass
             <<" max_ternary_depth="<<trieMaxDepth
             <<"\n";

    live.swap(next);
  }
  std::cout<<"VERIFIED_TERNARY_TRIE_FORWARD_PRODUCT_QUOTIENT\n";
  std::cout<<"FINAL_GATE=TERNARY_TRIE_QUOTIENT_D"<<DEPTH<<"_R"<<R<<"\n";
  return 0;
}
