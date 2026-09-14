// Exact exhaustive scan of the live Collatz interval restricted to
// n == -1 (mod 2^k). The first k shortcut steps are compiled:
//   n = 2^k m - 1  =>  T^k(n) = 3^k m - 1.
//
// Usage:
//   g++ -O3 -fopenmp collatz_spine_scan.cpp -o collatz_spine_scan
//   ./collatz_spine_scan 45 900
//
// Output reports the exact maximum first-descent time in the selected family.
#include <boost/multiprecision/cpp_int.hpp>
#include <omp.h>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>

using boost::multiprecision::cpp_int;
using u128 = unsigned __int128;

static u128 parse128(const std::string& s) {
    u128 x = 0;
    for (char c : s) x = x * 10 + (c - '0');
    return x;
}

static std::string str128(u128 x) {
    if (!x) return "0";
    std::string s;
    while (x) {
        s.push_back(char('0' + x % 10));
        x /= 10;
    }
    std::reverse(s.begin(), s.end());
    return s;
}

static cpp_int to_cpp(u128 x) {
    cpp_int y = std::uint64_t(x >> 64);
    y <<= 64;
    y += std::uint64_t(x);
    return y;
}

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: " << argv[0] << " K H\n";
        return 2;
    }
    const int k = std::stoi(argv[1]);
    const int H = std::stoi(argv[2]);
    if (k <= 0 || k >= 72 || H <= k) return 2;

    const u128 L = parse128("2392312122059207475200");
    const u128 U = parse128("4722366482869645213695");
    const u128 M = u128(1) << k;
    const std::uint64_t mlo =
        std::uint64_t((L + 1 + M - 1) / M);
    const std::uint64_t mhi =
        std::uint64_t((U + 1) / M);

    u128 p3 = 1;
    for (int i = 0; i < k; ++i) p3 *= 3;

    const u128 U128_MAX = ~u128(0);
    int global_best = 0;
    u128 global_seed = 0;
    unsigned long long fallback_count = 0;

    std::cout << "FAMILY k=" << k
              << " count=" << (mhi - mlo + 1)
              << " horizon=" << H << "\n";

#pragma omp parallel
    {
        int local_best = 0;
        u128 local_seed = 0;
        unsigned long long local_fallbacks = 0;

#pragma omp for schedule(dynamic, 8192)
        for (std::uint64_t m = mlo; m <= mhi; ++m) {
            const u128 n = (u128(m) << k) - 1;
            const u128 seed = n;
            u128 x = p3 * u128(m) - 1;
            int descent = H + 1;
            bool big = false;
            cpp_int bx;
            const cpp_int bseed = to_cpp(seed);

            for (int t = k + 1; t <= H; ++t) {
                if (!big) {
                    if (x & 1) {
                        if (x > (U128_MAX - 1) / 3) {
                            bx = to_cpp(x);
                            big = true;
                        } else {
                            x = (3 * x + 1) >> 1;
                        }
                    } else {
                        x >>= 1;
                    }
                    if (!big) {
                        if (x < seed) {
                            descent = t;
                            break;
                        }
                        continue;
                    }
                }

                if ((bx & 1) != 0)
                    bx = (3 * bx + 1) >> 1;
                else
                    bx >>= 1;

                if (bx < bseed) {
                    descent = t;
                    break;
                }
            }

            if (big) ++local_fallbacks;
            if (descent > local_best) {
                local_best = descent;
                local_seed = n;
            }
        }

#pragma omp critical
        {
            fallback_count += local_fallbacks;
            if (local_best > global_best) {
                global_best = local_best;
                global_seed = local_seed;
            }
        }
    }

    std::cout << "BEST first_descent=" << global_best
              << " seed=" << str128(global_seed)
              << " big_fallbacks=" << fallback_count << "\n";
    return 0;
}
