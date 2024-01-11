import logging

from narrec.benchmark.benchmark import Benchmark
from narrec.config import TG2005_PMIDS_FILE


class Genomics2005(Benchmark):

    def __init__(self):
        super().__init__(name="Genomics2005", path_to_document_ids=TG2005_PMIDS_FILE)

    def load_benchmark_data(self):
        pass



def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)
    benchmark = Genomics2005()
    logging.info(f'Benchmark has {len(benchmark.get_documents_for_baseline())} documents')


if __name__ == '__main__':
    main()