#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <vector>
using boost::multiprecision::cpp_int;
using u128 = unsigned __int128;

static long double log2cpp(const cpp_int& x){
  int b=boost::multiprecision::msb(x), sh=std::max(0,b-62);
  unsigned long long top=(x>>sh).convert_to<unsigned long long>();
  return std::log2((long double)top)+sh;
}
int main(int argc,char**argv){
  int M=argc>1?std::atoi(argv[1]):30, JMAX=argc>2?std::atoi(argv[2]):512;
  if(M<4||M>40||JMAX<60||JMAX>2000) return 2;
  std::vector<int> qmin(JMAX+1); cpp_int p2=1,p3=1; int q=0;
  for(int j=1;j<=JMAX;j++){p2*=2; while(p3<p2){p3*=3;q++;} qmin[j]=q;}
  std::vector<cpp_int> alive(JMAX+2),nxt(JMAX+2),L(JMAX+1); alive[0]=1;
  for(int j=1;j<=JMAX;j++){
    std::fill(nxt.begin(),nxt.end(),cpp_int(0)); cpp_int term=0;
    for(int r=0;r<=j;r++) if(alive[r]!=0) for(int b=0;b<2;b++){
      int s=r+b; if(s<qmin[j]) term+=alive[r]; else nxt[s]+=alive[r];
    }
    L[j]=term; alive.swap(nxt);
  }
  if(L[27]!=312455||L[31]!=1900470||L[34]!=13472296) return 3;
  std::vector<std::vector<unsigned long long>> hist(JMAX+1,std::vector<unsigned long long>(M+1));
  uint64_t N=uint64_t(1)<<M; int maxj=0; unsigned long long unresolved=0,overflow=0;
  auto t0=std::chrono::steady_clock::now();
  for(uint64_t r0=1;r0<N;r0+=2){
    u128 n=r0; int oq=0,fc=0;
    for(int j=1;j<=JMAX;j++){
      if(n&1){
        u128 lim=(((u128)1<<126)-1)/3; if(n>lim){overflow++;break;}
        n=(3*n+1)/2; oq++;
      } else n/=2;
      if(oq<qmin[j]){fc=j;break;}
    }
    if(!fc){unresolved++;continue;}
    int bl=64-__builtin_clzll(r0); hist[fc][bl]++; maxj=std::max(maxj,fc);
  }
  unsigned long long obs=0,viol=0; long double best=-1,bestg=-1; int bj=0,bm=0; unsigned long long bc=0; cpp_int bL=0;
  for(int j=60;j<=JMAX;j++){
    unsigned long long c=0;
    for(int m=1;m<=M;m++){
      c+=hist[j][m]; if(j<=m||c==0||L[j]==0) continue; obs++;
      cpp_int lhs=cpp_int(c)<<(j-m);
      cpp_int rhs=L[j]<<(1+(6*j)/125);
      if(lhs>rhs) viol++;
      long double g=std::log2((long double)c)-log2cpp(L[j])-m+j, e=g/j;
      if(e>best){best=e;bestg=g;bj=j;bm=m;bc=c;bL=L[j];}
    }
  }
  long double a=std::log(2.0L)/std::log(3.0L);
  long double H=-a*std::log2(a)-(1-a)*std::log2(1-a), gap=1-H;
  auto t1=std::chrono::steady_clock::now();
  if(overflow||unresolved||viol||!(0.048L<gap)) return 4;
  std::cout<<std::setprecision(18)
    <<"{\n"
    <<"  \"schema\":\"COLLATZ_ORIGIN_POWER_WINDOW_V1\",\n"
    <<"  \"status\":\"EXACT_FINITE_WARRANTED_BY_THIS_RUN\",\n"
    <<"  \"max_source_exponent\":"<<M<<",\n"
    <<"  \"odd_sources_scanned\":"<<(N/2)<<",\n"
    <<"  \"max_j\":"<<JMAX<<",\n"
    <<"  \"max_observed_first_crossing_j\":"<<maxj<<",\n"
    <<"  \"origin_window_observations_j_ge_60\":"<<obs<<",\n"
    <<"  \"exact_bound\":\"C_j(2^m)*2^(j-m) <= 2^(1+floor(6j/125))*|L_j|\",\n"
    <<"  \"exact_bound_violations\":"<<viol<<",\n"
    <<"  \"asymptotic_eta\":0.048,\n"
    <<"  \"entropy_loss_bits_per_step\":"<<(double)gap<<",\n"
    <<"  \"eta_below_entropy_gap\":true,\n"
    <<"  \"worst_observed\":{\"j\":"<<bj<<",\"m\":"<<bm<<",\"C\":"<<bc
    <<",\"L\":\""<<bL<<"\",\"log2_distortion\":"<<(double)bestg
    <<",\"normalized_exponent\":"<<(double)best<<"},\n"
    <<"  \"archived_count_regressions\":{\"J27\":312455,\"J31\":1900470,\"J34\":13472296},\n"
    <<"  \"runtime_seconds\":"<<(double)std::chrono::duration<long double>(t1-t0).count()<<",\n"
    <<"  \"interpretation\":\"All exact dyadic origin windows tested satisfy a fixed-factor eta=0.048 distortion envelope, on the sufficient side of the legal-language entropy gap.\",\n"
    <<"  \"not_proved\":\"No all-depth/all-X origin anti-concentration theorem is proved.\",\n"
    <<"  \"global_collatz\":\"UNKNOWN\"\n}\n";
}