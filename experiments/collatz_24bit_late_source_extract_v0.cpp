// Exact 24-bit late coefficient-live source extractor.
// Bounded diagnostic only; global Collatz remains UNKNOWN.
#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
using boost::multiprecision::cpp_int;
using U = unsigned __int128;

struct Prefix { uint64_t r; U y, p3; int q; };
struct Row { uint64_t n; int crossing; U endpoint; int q; };

static bool step(U& y, int& q) {
  if (y & 1) {
    if (y > (~U(0)-1)/3) return false;
    y = (3*y+1)/2; ++q;
  } else y /= 2;
  return true;
}
static std::vector<int> thresholds(int J) {
  std::vector<int> t(J+1,0);
  cpp_int a=1,b=1; int q=0;
  for (int j=1;j<=J;++j) {
    a*=2;
    while (b<a) { b*=3; ++q; }
    t[j]=q;
  }
  return t;
}
static std::string u128(U x) {
  if (!x) return "0";
  std::string s;
  while (x) { s.push_back(char('0'+x%10)); x/=10; }
  std::reverse(s.begin(),s.end());
  return s;
}
int main() {
  constexpr int B=24, K=20, J=512, THRESHOLD=230;
  const auto qm=thresholds(J);
  const uint64_t modulus=uint64_t(1)<<K;
  const uint64_t tails=uint64_t(1)<<(B-K);

  std::vector<Prefix> live;
  for (uint64_t r=1;r<modulus;r+=2) {
    U y=r; int q=0, crossing=0;
    for (int j=1;j<=K;++j) {
      if (!step(y,q)) return 3;
      if (q<qm[j]) { crossing=j; break; }
    }
    if (!crossing) {
      U p3=1; for (int i=0;i<q;++i) p3*=3;
      live.push_back({r,y,p3,q});
    }
  }

  std::vector<Row> rows;
  uint64_t unresolved=0, overflow=0, all=0;
  int maxCross=0;
  for (const auto& p:live) for (uint64_t u=0;u<tails;++u) {
    uint64_t n=p.r+modulus*u;
    U y=p.y+p.p3*u; int q=p.q, crossing=0;
    ++all;
    for (int j=K+1;j<=J;++j) {
      if (!step(y,q)) { ++overflow; break; }
      if (q<qm[j]) {
        crossing=j;
        maxCross=std::max(maxCross,j);
        if (j>=THRESHOLD) rows.push_back({n,j,y,q});
        break;
      }
    }
    if (!crossing && !overflow) ++unresolved;
  }
  std::sort(rows.begin(), rows.end(), [](const Row&a,const Row&b){
    if (a.crossing!=b.crossing) return a.crossing>b.crossing;
    return a.n<b.n;
  });

  std::cout << "{\n"
            << "  \"schema\": \"COLLATZ_24BIT_LATE_SOURCE_EXTRACT_V0\",\n"
            << "  \"source_bits\": 24,\n"
            << "  \"prefix_bits\": 20,\n"
            << "  \"depth_limit\": 512,\n"
            << "  \"late_threshold\": 230,\n"
            << "  \"continued_sources\": " << all << ",\n"
            << "  \"unresolved\": " << unresolved << ",\n"
            << "  \"overflow\": " << overflow << ",\n"
            << "  \"max_first_crossing\": " << maxCross << ",\n"
            << "  \"late_sources\": [\n";
  for (size_t i=0;i<rows.size();++i) {
    const auto&r=rows[i];
    std::cout << "    {\"source\":" << r.n
              << ",\"first_crossing\":" << r.crossing
              << ",\"crossing_endpoint\":" << u128(r.endpoint)
              << ",\"odd_count\":" << r.q << "}";
    if (i+1<rows.size()) std::cout << ",";
    std::cout << "\n";
  }
  std::cout << "  ],\n"
            << "  \"global_collatz\": \"UNKNOWN\"\n"
            << "}\n";
  return (unresolved||overflow)?1:0;
}
