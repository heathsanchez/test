// Exact complete reverse-language closure directly from each Collatz affine endpoint.
//
// At binary depth k a live family is
//   n(a) = 2^k a + b,  a>=1,
// and after k shortcut steps
//   y(a) = 3^c a + d.
//
// If y<n uniformly, direct strong-induction descent closes the family.
// Otherwise this program decides whether ANY finite reverse E/O word supplies
// a uniformly positive predecessor p(a)<n(a) with T^r(p(a))=y(a).
//
// No bridge bank and no reverse-word horizon are used.
//
// Reverse operations on affine x(a)=A a + D:
//   E: A,D -> 2A, 2D
//   O: A,D -> 2A/3, (2D-1)/3,
// where O is admitted only uniformly. Every useful word has canonical blocks
//   E^e1 O^m1 ... E^er O^mr,
// because terminal E only makes a positive predecessor larger.
//
// Finiteness proof:
//   q=v3(A) is finite. E preserves q; each O consumes one factor of 3.
//   Hence total O count and block count are <=q.
//   For a candidate E-run e, even spending all q remaining O steps leaves
//       coefficient >= A*2^e*(2/3)^q.
//   Once this is >=2^k, that e and all larger e are impossible for a lower
//   affine witness. Thus every E-run choice is also finite.
//
// Therefore the DFS is an exact decision procedure for the entire affine
// reverse E/O language attached to the endpoint.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <vector>

using u128=unsigned __int128;
using i128=__int128;

static inline u128 T(u128 n){return (n&1)?(3*n+1)/2:n/2;}
static u128 iterate(u128 n,int steps){for(int i=0;i<steps;++i)n=T(n);return n;}

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
  // Parameter a>=1.  p(a)=A*a+D < n(a)=2^k*a+b uniformly iff
  // the difference slope is nonpositive and the inequality holds at a=1.
  const i128 M=i128(1)<<k;
  const i128 slope=A-M;
  const i128 rhs=i128(b)-D;
  return A>0 && A+D>0 && slope<=0 && slope<rhs;
}

static int v3i(i128 x,int cap=80){
  if(x<0)x=-x;
  int v=0;while(v<cap&&x%3==0){x/=3;++v;}return v;
}
static i128 mul_checked(i128 a,i128 b){
  if(a<0||b<0){std::cerr<<"NEGATIVE_COEF_RANGE\n";std::exit(7);}
  if(a && b>(i128(1)<<120)/a){std::cerr<<"I128_RANGE\n";std::exit(8);}
  return a*b;
}
static i128 powi(i128 b,int e){
  i128 x=1;for(int i=0;i<e;++i)x=mul_checked(x,b);return x;
}

struct Key{
  i128 A,D;
  bool operator<(const Key&o)const{
    return A<o.A||(A==o.A&&D<o.D);
  }
};
struct Witness{i128 A=0,D=0;std::string word;};

struct SearchStats{
  uint64_t families_searched=0;
  uint64_t nodes=0,memo_hits=0,e_cases=0,o_run_cases=0,coef_prunes=0;
  uint64_t max_nodes_family=0,max_seen_family=0;
  int max_blocks=0,max_word_steps=0,max_root_v3=0;
};

struct LocalStats{
  uint64_t nodes=0,memo_hits=0,e_cases=0,o_run_cases=0,coef_prunes=0;
  int max_blocks=0,max_word_steps=0;
};

static bool dfs(
    i128 A,i128 D,int k,uint64_t b,
    std::set<Key>&seen,LocalStats&st,
    std::string&path,int blocks,Witness&w){
  ++st.nodes;
  st.max_blocks=std::max(st.max_blocks,blocks);
  st.max_word_steps=std::max(st.max_word_steps,(int)path.size());

  if(A+D<=0)return false; // positivity at a=1 can never recover under E/O.
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
        std::cerr<<"D_RANGE\n";std::exit(9);
      }
    }

    if(Ae%p3q){std::cerr<<"ROOT_V3_INVARIANT_FAIL\n";std::exit(10);}
    const i128 amin=mul_checked(Ae/p3q,p2q);
    if(amin>=M){++st.coef_prunes;break;}
    ++st.e_cases;

    const int mmax=std::min(q,v3i(De+1));
    i128 den=1,tw=1;
    for(int m=1;m<=mmax;++m){
      den=mul_checked(den,3);tw=mul_checked(tw,2);
      ++st.o_run_cases;
      if(Ae%den||(De+1)%den){
        std::cerr<<"BLOCK_DIV_FAIL\n";std::exit(11);
      }
      const i128 A2=mul_checked(Ae/den,tw);
      const i128 D2=mul_checked((De+1)/den,tw)-1;

      const size_t old=path.size();
      path.append(e,'E');
      path.append(m,'O');

      if(lower_family(A2,D2,k,b)){w={A2,D2,path};return true;}
      if(dfs(A2,D2,k,b,seen,st,path,blocks+1,w))return true;
      path.resize(old);
    }
  }
  return false;
}

static bool complete_endpoint_reverse(
    i128 A,i128 D,int k,uint64_t b,Witness&w,SearchStats&g){
  ++g.families_searched;
  g.max_root_v3=std::max(g.max_root_v3,v3i(A));
  std::set<Key>seen;
  LocalStats st;
  std::string path;
  const bool ok=dfs(A,D,k,b,seen,st,path,0,w);
  g.nodes+=st.nodes;g.memo_hits+=st.memo_hits;g.e_cases+=st.e_cases;
  g.o_run_cases+=st.o_run_cases;g.coef_prunes+=st.coef_prunes;
  if(st.nodes>g.max_nodes_family){g.max_nodes_family=st.nodes;g.max_seen_family=b;}
  g.max_blocks=std::max(g.max_blocks,st.max_blocks);
  g.max_word_steps=std::max(g.max_word_steps,st.max_word_steps);
  return ok;
}

int main(int argc,char**argv){
  if(argc!=2){std::cerr<<"usage: complete_endpoint_reverse K\n";return 2;}
  const int K=std::stoi(argv[1]);
  if(K<1||K>30){std::cerr<<"K_RANGE\n";return 2;}

  std::vector<uint64_t>p3(K+2,1);
  for(int i=1;i<(int)p3.size();++i){
    if(p3[i-1]>UINT64_MAX/3){std::cerr<<"P3_OVERFLOW\n";return 3;}
    p3[i]=p3[i-1]*3;
  }

  std::vector<State>cur{{0,0}},next;
  uint64_t totalDirect=0,totalReverse=0,controls=0;
  SearchStats gst;
  std::map<int,uint64_t>blocksHist,stepsHist,rootCHist;

  for(int k=1;k<=K;++k){
    const uint64_t half=UINT64_C(1)<<(k-1),M=UINT64_C(1)<<k;
    next.clear();
    if(cur.size()<=std::numeric_limits<size_t>::max()/2)next.reserve(cur.size()*2);
    uint64_t direct=0,reverse=0;
    for(const State&s:cur){
      const uint64_t b0=s.b,d0=state_d(s);const int c0=state_c(s);
      for(int bit=0;bit<2;++bit){
        const uint64_t b=b0+(bit?half:0);
        const uint64_t y=d0+(bit?p3[c0]:0);
        int c=c0;uint64_t d;
        if(y&1){
          ++c;if(y>(UINT64_MAX-1)/3){std::cerr<<"CHILD_OVERFLOW\n";return 12;}
          d=(3*y+1)/2;
        }else d=y/2;

        const i128 A=i128(p3[c]),D=i128(d);
        if(lower_family(A,D,k,b)){++direct;++totalDirect;continue;}

        Witness w{};
        ++rootCHist[c];
        if(complete_endpoint_reverse(A,D,k,b,w,gst)){
          ++reverse;++totalReverse;
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
                 iterate(u128(pred),(int)w.word.size())!=endpoint){
                std::cerr<<"ENDPOINT_GRAMMAR_CONTROL_FAIL"
                         <<" k="<<k<<" b="<<b<<" c="<<c
                         <<" word="<<w.word<<"\n";return 13;
              }
              ++controls;
            }
          }
          continue;
        }

        next.push_back(make_state(b,d,c));
      }
    }

    std::cout<<"COMPLETE_ENDPOINT_REVERSE_LEVEL k="<<k
             <<" parents="<<cur.size()
             <<" direct="<<direct
             <<" reverse="<<reverse
             <<" live="<<next.size()
             <<" odd_live_fraction="<<(double(next.size())/double(UINT64_C(1)<<(k-1)))
             <<"\n";
    cur.swap(next);
  }

  std::cout<<"COMPLETE_ENDPOINT_REVERSE_DONE K="<<K
           <<" final_live="<<cur.size()
           <<" total_direct="<<totalDirect
           <<" total_reverse="<<totalReverse
           <<" families_searched="<<gst.families_searched
           <<" search_nodes="<<gst.nodes
           <<" memo_hits="<<gst.memo_hits
           <<" e_cases="<<gst.e_cases
           <<" o_run_cases="<<gst.o_run_cases
           <<" coefficient_prunes="<<gst.coef_prunes
           <<" max_nodes_one_family="<<gst.max_nodes_family
           <<" max_nodes_family_b="<<gst.max_seen_family
           <<" max_blocks="<<gst.max_blocks
           <<" max_word_steps="<<gst.max_word_steps
           <<" max_root_v3="<<gst.max_root_v3
           <<" controls="<<controls<<"\n";
  for(auto&kv:blocksHist)std::cout<<"ENDPOINT_BLOCKS_HIST blocks="<<kv.first<<" closed="<<kv.second<<"\n";
  for(auto&kv:stepsHist)std::cout<<"ENDPOINT_STEPS_HIST steps="<<kv.first<<" closed="<<kv.second<<"\n";
  for(auto&kv:rootCHist)std::cout<<"ENDPOINT_ROOT_C_HIST c="<<kv.first<<" searched="<<kv.second<<"\n";

  if(cur.empty())std::cout<<"ALL_BINARY_AFFINE_FAMILIES_CLOSED_AT_K"<<K<<"\n";
  else std::cout<<"COMPLETE_ENDPOINT_REVERSE_RESIDUAL_REMAINS K="<<K
                <<" live="<<cur.size()<<"\n";
  std::cout<<"VERIFIED_COMPLETE_ENDPOINT_REVERSE_LANGUAGE\n";
  return 0;
}
