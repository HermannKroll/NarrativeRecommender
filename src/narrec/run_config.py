from narrec.benchmark.genomics2005 import Genomics2005
from narrec.benchmark.pm2020 import PM2020Benchmark
from narrec.benchmark.relish import RelishBenchmark

FIRST_STAGES = [
    "BM25Title",
    "BM25Abstract",
    "BM25Yake"
]

BENCHMARKS = [
   # PM2020Benchmark(),
    RelishBenchmark(),
   # Genomics2005()
]


CONFIDENCE_WEIGHT = 0.5
TFIDF_WEIGHT = 0.5

assert CONFIDENCE_WEIGHT + TFIDF_WEIGHT == 1.0

NARRATIVE_CORE_THRESHOLD = 0.5