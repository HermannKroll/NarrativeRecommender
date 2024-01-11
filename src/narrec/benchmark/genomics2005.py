from narrec.benchmark.benchmark import Benchmark
from narrec.config import TG2005_PMIDS_FILE


class Genomics2005(Benchmark):

    def __init__(self):
        super().__init__(name="Genomics2005", path_to_document_ids=TG2005_PMIDS_FILE)

    def load_benchmark_data(self):
        pass
