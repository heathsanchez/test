// Independent odd-count-indexed replay, using exact Boost big integers.
#include <boost/multiprecision/cpp_int.hpp>
#include <cstdint>
#include <iostream>
using boost::multiprecision::cpp_int;
int main() {
  constexpr unsigned N = 271782;
  cpp_int p3 = 1;
  std::uint64_t best = 0;
  unsigned count = 1, bestj = 0, bestq = 0; // q=0,j=1 has B=0 and cap=0
  for (unsigned q = 1; ; ++q) {
    p3 *= 3;
    unsigned j = boost::multiprecision::msb(p3) + 1;
    if (j > N) break;
    cpp_int p2 = cpp_int(1) << j;
    cpp_int D = p2 - p3;
    cpp_int numerator = q * (p3 / 3);
    if (!(p3 < p2 && p2 <= 2 * p3 && D > 0)) return 2;
    cpp_int cap = numerator / D;
    if (!(cap * D <= numerator && numerator < (cap + 1) * D)) return 3;
    if (!(numerator < D * (cpp_int(1) << 33))) return 4;
    auto value = cap.convert_to<std::uint64_t>();
    ++count;
    if (value > best) { best = value; bestj = j; bestq = q; }
  }
  if (count != 171476 || best != 7216089270ULL || bestj != 125743 || bestq != 79335) return 5;
  std::cout << "{\"depth\":" << N << ",\"types\":" << count
            << ",\"max_cap\":" << best << ",\"j\":" << bestj << ",\"q\":" << bestq
            << ",\"all_caps_below_2_pow_33\":true,\"global_collatz\":\"UNKNOWN\"}\n";
}
