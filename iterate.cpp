#include <iostream>
#include <chrono>
#include <iomanip>

int main() {
    using clock = std::chrono::high_resolution_clock;
    const int N = 1'000'000;
    auto t0 = clock::now();

    for (int i = 1; i <= N; ++i) {
        // Uncomment to spam numbers:
        // std::cout << i << '\n';
        if (i % 100000 == 0) {
            double elapsed = std::chrono::duration<double>(clock::now() - t0).count();
            double rate = (elapsed > 0) ? (i / elapsed) : 0.0;
            double eta  = (rate > 0) ? ((N - i) / rate) : 0.0;
            std::cerr << "\r" << i << "/" << N
                      << "  elapsed=" << std::fixed << std::setprecision(2) << elapsed << "s"
                      << "  ETA=" << std::fixed << std::setprecision(2) << eta << "s"
                      << std::flush;
        }
    }

    std::cerr << std::endl;
    double total = std::chrono::duration<double>(clock::now() - t0).count();
    double rate  = (total > 0) ? (N / total) : 0.0;
    std::cerr << "Done. Elapsed=" << std::fixed << std::setprecision(3) << total
              << "s  Avg=" << std::fixed << std::setprecision(0) << rate << " it/s\n";
    return 0;
}
