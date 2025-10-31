import sys, time

def main():
    N = 1_000_000
    start = time.perf_counter()

    for i in range(1, N + 1):
        # Uncomment to spam numbers:
        print(i)
        if i % 100_000 == 0:
            elapsed = time.perf_counter() - start
            rate = i / elapsed if elapsed > 0 else 0.0
            eta = (N - i) / rate if rate > 0 else float("inf")
            print(f"\r{i}/{N}  elapsed={elapsed:.2f}s  ETA={eta:.2f}s", file=sys.stderr, end="", flush=True)

    # finish line
    print(file=sys.stderr)
    total = time.perf_counter() - start
    rate = N / total if total > 0 else 0.0
    print(f"Done. Elapsed={total:.3f}s  Avg={rate:,.0f} it/s", file=sys.stderr)

if __name__ == "__main__":
    main()
