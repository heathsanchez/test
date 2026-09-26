// Exact bounded CST audit. No assertion of global Collatz closure.
#include <boost/multiprecision/cpp_int.hpp>
#include <cstdint>
#include <iostream>
#include <vector>
#include <string>
#include <limits>
#include <stdexcept>
using boost::multiprecision::cpp_int;
using U = unsigned __int128;
struct Prefix { uint64_t r; U y, p3; int q; };
struct Report {
  std::vector<uint64_t> hist;
  uint64_t unknown=0, overflow=0, bad=0, firstBad=0, continued=0;
  uint64_t livePrefixes=0, directChecks=0;
  int maxJ=0;
  explicit Report(int j): hist(j+1,0) {}
  void terminal(int j, uint64_t n, U y) {
    ++hist[j]; if(j>maxJ)maxJ=j;
    if(n>1 && y>=n){++bad;if(!firstBad)firstBad=n;}
  }
};
bool step(U& y, int& q) {
  if(y&1){ if(y>(~U(0)-1)/3)return false; y=(3*y+1)/2;++q; }
  else y/=2;
  return true;
}
std::vector<int> ceilThresholds(int J) {
  std::vector<int> t(J+1,0); cpp_int a=1,b=1;int q=0;
  for(int j=1;j<=J;++j){a*=2;while(b<a){b*=3;++q;}t[j]=q;}
  return t;
}
Report prefixAudit(int B,int K,int J) {
  auto qm=ceilThresholds(J);Report z(J);
  uint64_t modulus=uint64_t(1)<<K, tails=uint64_t(1)<<(B-K);
  std::vector<Prefix> live;
  for(uint64_t r=1;r<modulus;r+=2) {
    U y=r;int q=0,fc=0;
    for(int j=1;j<=K;++j){
      if(!step(y,q))throw std::runtime_error("prefix overflow");
      if(q<qm[j]){fc=j;break;}
    }
    if(fc){
      // Contraction coefficient makes all positive tail lifts descend if
      // the smallest representative descends. r=1 is the sole trivial equality.
      if((r>1 && y>=r)||(r==1 && y>r))throw std::runtime_error("short-prefix CST failure");
      z.hist[fc]+=tails;
      if(fc>z.maxJ)z.maxJ=fc;
    } else {
      U p3=1;for(int a=0;a<q;++a)p3*=3;
      if(!(y<p3))throw std::runtime_error("canonical endpoint bound failure");
      live.push_back({r,y,p3,q});
    }
  }
  z.livePrefixes=live.size();
  for(const auto& p:live)for(uint64_t u=0;u<tails;++u){
    uint64_t n=p.r+modulus*u;U y=p.y+p.p3*u;int q=p.q,fc=0;
    ++z.continued;
    for(int j=K+1;j<=J;++j){
      if(!step(y,q)){++z.overflow;break;}
      if(q<qm[j]){fc=j;break;}
    }
    if(!fc)++z.unknown;else z.terminal(fc,n,y);
  }
  return z;
}
Report directAudit(int B,int J){
  // Independently indexed coefficient test: j > floor(log_2(3^q)).
  std::vector<int> floors(J+1,0);cpp_int p=1;
  for(int q=0;q<=J;++q){floors[q]=boost::multiprecision::msb(p);p*=3;}
  Report z(J);uint64_t N=uint64_t(1)<<B;
  for(uint64_t n=1;n<N;n+=2){
    U y=n;int q=0,fc=0;++z.directChecks;
    for(int j=1;j<=J;++j){
      if(!step(y,q)){++z.overflow;break;}
      if(j>floors[q]){fc=j;break;}
    }
    if(!fc)++z.unknown;else z.terminal(fc,n,y);
  }
  return z;
}
int main(int argc,char**argv){
  if(argc!=5)return 2;
  std::string mode=argv[1];int B=std::stoi(argv[2]),K=std::stoi(argv[3]),J=std::stoi(argv[4]);
  if(B<4||B>36||K<2||K>26||K>B||J<K||J>4096)return 2;
  Report z = mode=="prefix" ? prefixAudit(B,K,J) : mode=="direct" ? directAudit(B,J) : throw std::runtime_error("unknown mode");
  uint64_t total=0;for(auto n:z.hist)total+=n;
  std::cout<<"{\"schema\":\"CST_SOURCE_FLOOR_V1\",\"mode\":\""<<mode<<"\",\"source_bits\":"<<B
    <<",\"prefix_bits\":"<<K<<",\"depth_limit\":"<<J<<",\"odd_sources_accounted\":"<<total
    <<",\"live_prefixes\":"<<z.livePrefixes<<",\"continued_sources\":"<<z.continued
    <<",\"direct_checks\":"<<z.directChecks<<",\"max_first_crossing\":"<<z.maxJ
    <<",\"unresolved\":"<<z.unknown<<",\"overflow\":"<<z.overflow
    <<",\"nontrivial_nondescending\":"<<z.bad<<",\"first_bad_source\":"<<z.firstBad
    <<",\"global_collatz\":\"UNKNOWN\",\"first_crossing_histogram\":[";
  for(int j=0;j<=z.maxJ;++j){if(j)std::cout<<",";std::cout<<z.hist[j];}
  std::cout<<"]}\n";
  return (z.unknown||z.overflow||z.bad||total!=(uint64_t(1)<<(B-1)))?1:0;
}
