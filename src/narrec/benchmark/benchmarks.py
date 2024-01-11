from narrec.benchmark.genomics2005 import Genomics2005
from narrec.benchmark.pm2020 import PM2020Benchmark
from narrec.benchmark.relish import RelishBenchmark


class Benchmarks:

    def __init__(self):
        self.benchmarks = [
            PM2020Benchmark(),
            RelishBenchmark(),
            Genomics2005()
        ]

    def __iter__(self):
        for b in self.benchmarks:
            yield b
