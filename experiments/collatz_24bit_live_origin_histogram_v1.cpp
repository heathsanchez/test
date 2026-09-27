// Exact 24-bit live-origin first-crossing histogram for Crystal carry audits.
// Bounded diagnostic only. Global Collatz remains UNKNOWN.
#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
using boost::multiprecision::cpp_int;
using U = unsigned __int128;

struct Prefix {
  uint64_t r;
  U y;
  U p3;
  int q;
  int crossing;
};

static bool step(U& y, int& q) {
  if (y & 1) {
    if (y > (~U(0)-1)/3) return false;
    y = (3*y+1)/2;
    ++q;
  } else {
    y /= 2;
  }
  return true;
}

static std::vector<int> thresholds(int J) {
  std::vector<int> t(J+1,0);
  cpp_int a=1,b=1;
  int q=0;
  for (int j=1;j<=J;++j) {
    a*=2;
    while (b<a) { b*=3; ++q; }
    t[j]=q;
  }
  return t;
}

static int bitlen(uint64_t n) {
  return 64 - __builtin_clzll(n);
}

int main() {
  constexpr int BITS=24;
  constexpr int PREFIX=20;
  constexpr int DEPTH=512;
  const auto qm=thresholds(DEPTH);
  const uint64_t mod=uint64_t(1)<<PREFIX;
  const uint64_t tails=uint64_t(1)<<(BITS-PREFIX);

  std::vector<std::vector<uint64_t>> hist(DEPTH+1, std::vector<uint64_t>(BITS+1,0));
  std::vector<Prefix> live;
  uint64_t overflow=0, unresolved=0, total=0;
  int max_cross=0;

  for (uint64_t r=1;r<mod;r+=2) {
    U y=r, p3=1;
    int q=0, crossing=0;
    for (int j=1;j<=PREFIX;++j) {
      const int before=q;
      if (!step(y,q)) return 3;
      if (q>before) p3*=3;
      if (q<qm[j]) { crossing=j; break; }
    }
    live.push_back({r,y,p3,q,crossing});
  }

  for (const auto& p : live) {
    for (uint64_t u=0; u<tails; ++u) {
      const uint64_t n=p.r + mod*u;
      ++total;
      const int m=bitlen(n);

      if (p.crossing) {
        hist[p.crossing][m]++;
        max_cross=std::max(max_cross,p.crossing);
        continue;
      }

      U y=p.y + p.p3*u;
      int q=p.q;
      int crossing=0;
      bool ov=false;
      for (int j=PREFIX+1;j<=DEPTH;++j) {
        if (!step(y,q)) { ov=true; ++overflow; break; }
        if (q<qm[j]) { crossing=j; break; }
      }
      if (ov) continue;
      if (!crossing) {
        ++unresolved;
      } else {
        hist[crossing][m]++;
        max_cross=std::max(max_cross,crossing);
      }
    }
  }

  std::cout << "{\n"
            << "  \"schema\":\"COLLATZ_24BIT_LIVE_ORIGIN_HISTOGRAM_V1\",\n"
            << "  \"source_bits\":" << BITS << ",\n"
            << "  \"prefix_bits\":" << PREFIX << ",\n"
            << "  \"depth\":" << DEPTH << ",\n"
            << "  \"odd_sources\":" << total << ",\n"
            << "  \"unresolved\":" << unresolved << ",\n"
            << "  \"overflow\":" << overflow << ",\n"
            << "  \"max_first_crossing\":" << max_cross << ",\n"
            << "  \"rows\":[\n";
  bool first=true;
  for (int j=1;j<=DEPTH;++j) {
    for (int m=1;m<=BITS;++m) {
      if (!hist[j][m]) continue;
      if (!first) std::cout << ",\n";
      first=false;
      std::cout << "    {\"j\":" << j << ",\"m\":" << m
                << ",\"count\":" << hist[j][m] << "}";
    }
  }
  std::cout << "\n  ],\n"
            << "  \"global_collatz\":\"UNKNOWN\"\n"
            << "}\n";
  return (overflow||unresolved) ? 1 : 0;
}
