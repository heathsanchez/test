#include <cstdint>
#include <iostream>
#include <limits>
#include <utility>

static inline uint64_t T(uint64_t n) {
    return (n & 1ULL) ? (3ULL*n + 1ULL)/2ULL : n/2ULL;
}

int main() {
    const uint64_t X = 157755113ULL;
    const uint64_t Z = 2668133ULL;

    uint64_t y = X;
    for (int i=0;i<36;i++) y=T(y);
    if (y != Z) {
        std::cerr << "bad endpoint descent " << y << "\n";
        return 2;
    }

    uint64_t max_steps=0, argmax=0, max_peak=0;
    for (uint64_t n=2;n<=Z;n++) {
        uint64_t v=n;
        uint64_t peak=v;
        uint64_t steps=0;
        while (v>=n) {
            v=T(v);
            if (v>peak) peak=v;
            if (++steps > 10000) {
                std::cerr << "descent guard " << n << " " << v << "\n";
                return 3;
            }
        }
        if (steps>max_steps) {
            max_steps=steps; argmax=n; max_peak=peak;
        }
    }

    std::cout << "ENDPOINT " << X << "\n";
    std::cout << "ENDPOINT_DESCENT_STEPS 36\n";
    std::cout << "ENDPOINT_DESCENT_VALUE " << Z << "\n";
    std::cout << "FINITE_BASE_MAX " << Z << "\n";
    std::cout << "FINITE_BASE_CASES " << (Z-1) << "\n";
    std::cout << "FINITE_BASE_MAX_FIRST_DESCENT_STEPS " << max_steps << "\n";
    std::cout << "FINITE_BASE_ARGMAX " << argmax << "\n";
    std::cout << "FINITE_BASE_ARGMAX_PEAK " << max_peak << "\n";
    std::cout << "PASS_C9_TWO_REPLAY_ENDPOINT_COMPLETE_CLOSURE\n";
    std::cout << "IMPLICATION any_source_hitting_endpoint_has_lower_merge\n";
    return 0;
}
