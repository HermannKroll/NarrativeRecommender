from narrec.benchmark.pm2020 import PM2020Benchmark
from narrec.benchmark.relish import RelishBenchmark

BENCHMARKS = [
    PM2020Benchmark(),
    RelishBenchmark()
]
