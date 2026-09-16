// Exact future-consequence minimization AFTER complete affine reverse closure.
//
// This is the all-integer symbolic tree:
//   n(q)=2^k q+b, q>=L,
//   T^k(n(q))=3^c q+d.
// Every child is first tested by direct descent and then by the complete,
// finite reverse E/O decision procedure. Closed children are DEAD.
//
// We then quotient the remaining hereditary live tree bottom-up by its complete
// bounded future CLOSED/UNKNOWN behavior. This asks whether the much stronger
// residual finally forms a small recursive language.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <set>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;
static constexpr uint32_t DEAD=std::numeric_limits<uint32_t>::max();

struct State{uint64_t b,d;uint32_t c;uint64_t L;};
struct Edge{uint32_t lo=DEAD,hi=DEAD;};

static bool lower_family(i128 A,i128 D,int k,uint64_t b,uint64_t L){
  const i128 M=i128(1)<<k,q=i128(L);
  const i128 slope=A-M;
  return A>0 && A*q+D>0 && slope<=0 && slope*q+D-i128(b)<0;
}
static uint64_t child_lower(uint64_t L,int e){
  if(L<=uint64_t(e))return 0;
  return (L-uint64_t(e)+1)/2;
}
static int v3i(i128 x,int cap=80){
  if(x<0)x=-x;int v=0;while(v<cap&&x%3==0){x/=3;++v;}return v;
}
static i128 mulc(i128 a,i128 b){
  if(a<0||b<0|| (a&&b>(i128(1)<<120)/a)){std::cerr<<"RANGE\n";std::exit(7);}
  return a*b;
}
static i128 powi(i128 b,int e){i128 x=1;for(int i=0;i<e;++i)x=mulc(x,b);return x;}

struct Key{
  i128 A,D;
  bool operator<(const Key&o)const{return A<o.A||(A==o.A&&D<o.D);}
};

static bool reverse_dfs(i128 A,i128 D,int k,uint64_t b,uint64_t L,
                        std::set<Key>&seen){
  if(A*i128(L)+D<=0)return false;
  if(!seen.emplace(Key{A,D}).second)return false;
  const int q=v3i(A);
  if(q<=0)return false;
  const i128 M=i128(1)<<k,p3q=powi(3,q),p2q=powi(2,q);
  i128 Ae=A,De=D;
  for(int e=0;;++e){
    if(e){Ae=mulc(Ae,2);De*=2;if(De>(i128(1)<<120)||De<-(i128(1)<<120)){std::cerr<<"D_RANGE\n";std::exit(8);}}
    const i128 amin=mulc(Ae/p3q,p2q);
    if(amin>M)break;
    const int mmax=std::min(q,v3i(De+1));
    i128 den=1,tw=1;
    for(int m=1;m<=mmax;++m){
      den=mulc(den,3);tw=mulc(tw,2);
      const i128 A2=mulc(Ae/den,tw),D2=mulc((De+1)/den,tw)-1;
      if(lower_family(A2,D2,k,b,L))return true;
      if(reverse_dfs(A2,D2,k,b,L,seen))return true;
    }
  }
  return false;
}
static bool reverse_closes(i128 A,i128 D,int k,uint64_t b,uint64_t L){
  std::set<Key>seen;return reverse_dfs(A,D,k,b,L,seen);
}
static uint64_t pairkey(uint32_t a,uint32_t b){return (uint64_t(a)<<32)|b;}

int main(int argc,char**argv){
  if(argc!=2){std::cerr<<"usage: quotient K\n";return 2;}
  const int K=std::stoi(argv[1]);
  if(K<1||K>26)return 2;
  std::vector<uint64_t>p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i)p3[i]=p3[i-1]*3;

  std::vector<State>cur{{0,0,0,2}};
  std::vector<std::vector<Edge>>edges(K);
  std::vector<uint64_t>liveCount(K+1);liveCount[0]=1;

  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1),M=UINT64_C(1)<<k;
    auto&E=edges[k-1];E.resize(cur.size());
    std::vector<State>next;
    uint64_t direct=0,reverse=0;
    for(size_t i=0;i<cur.size();++i){
      const State&s=cur[i];const uint64_t P=p3[s.c];
      Edge ed;
      for(int bit=0;bit<2;++bit){
        const uint64_t L=child_lower(s.L,bit);
        const uint64_t b=s.b+(bit?half:0);
        const uint64_t raw=s.d+(bit?P:0);
        uint32_t c=s.c;uint64_t d;
        if(raw&1){++c;d=(3*raw+1)/2;}else d=raw/2;
        if(u128(M)*L+b<=1){std::cerr<<"DOMAIN_FAIL\n";return 3;}
        const i128 A=i128(p3[c]),D=i128(d);
        bool closed=lower_family(A,D,k,b,L);
        if(closed)++direct;
        else if(reverse_closes(A,D,k,b,L)){closed=true;++reverse;}
        if(!closed){
          if(next.size()>=size_t(DEAD)){std::cerr<<"INDEX_RANGE\n";return 4;}
          const uint32_t idx=(uint32_t)next.size();
          next.push_back({b,d,c,L});
          if(bit==0)ed.lo=idx;else ed.hi=idx;
        }
      }
      E[i]=ed;
    }
    liveCount[k]=next.size();
    std::cout<<"COMPLETE_RESIDUAL_BUILD k="<<k<<" parents="<<cur.size()
             <<" direct="<<direct<<" reverse="<<reverse<<" live="<<next.size()<<"\n";
    cur.swap(next);
  }

  const uint64_t frontier=cur.size();
  std::vector<State>().swap(cur);
  std::vector<uint32_t>nextSig(frontier,1),curSig;
  std::unordered_map<uint64_t,uint32_t>intern;
  uint32_t nextId=2;
  uint64_t maxUnique=frontier?1:0;int maxDepth=K;

  std::cout<<"COMPLETE_RESIDUAL_QUOTIENT k="<<K<<" remaining=0 states="<<frontier
           <<" unique=1 compression="<<(frontier?double(frontier):0.0)<<"\n";

  for(int k=K-1;k>=0;--k){
    const auto&E=edges[k];
    curSig.resize(E.size());
    std::unordered_set<uint32_t>unique;
    for(size_t i=0;i<E.size();++i){
      const uint32_t a=E[i].lo==DEAD?0:nextSig[E[i].lo];
      const uint32_t b=E[i].hi==DEAD?0:nextSig[E[i].hi];
      const uint64_t key=pairkey(a,b);
      auto it=intern.find(key);
      if(it==intern.end())it=intern.emplace(key,nextId++).first;
      curSig[i]=it->second;unique.insert(it->second);
    }
    const uint64_t u=unique.size();
    if(u>maxUnique){maxUnique=u;maxDepth=k;}
    std::cout<<"COMPLETE_RESIDUAL_QUOTIENT k="<<k<<" remaining="<<(K-k)
             <<" states="<<E.size()<<" unique="<<u
             <<" compression="<<(u?double(E.size())/u:0.0)<<"\n";
    nextSig.swap(curSig);
  }

  std::cout<<"COMPLETE_RESIDUAL_QUOTIENT_DONE K="<<K
           <<" frontier="<<frontier<<" signature_types="<<nextId
           <<" max_unique="<<maxUnique<<" max_unique_depth="<<maxDepth
           <<" root_signature="<<(nextSig.empty()?0:nextSig[0])<<"\n";
  std::cout<<"VERIFIED_COMPLETE_RESIDUAL_FUTURE_QUOTIENT\n";
  return 0;
}
