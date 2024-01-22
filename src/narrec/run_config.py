from narrec.benchmark.genomics2005 import Genomics2005
from narrec.benchmark.pm2020 import PM2020Benchmark
from narrec.benchmark.relish import RelishBenchmark

FIRST_STAGES = [
    "BM25Title"
]

BENCHMARKS = [
   # PM2020Benchmark(),
    RelishBenchmark(),
   # Genomics2005()
]