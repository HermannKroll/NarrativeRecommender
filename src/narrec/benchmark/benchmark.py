from abc import abstractmethod
from enum import Enum

from narrec.recommender.base import RecommenderBase


class BenchmarkMode(Enum):
    RELEVANT_VS_IRRELEVANT = 0
    RELEVANT_VS_PARTIAL_IRRELEVANT = 1
    RELEVANT_PARTIAL_VS_IRRELEVANT = 2


class Benchmark:

    def __init__(self, name, path_to_document_ids):
        self.name = name
        self.document_ids = set()
        self.path_to_document_ids = path_to_document_ids
        self.documents_for_baseline_load = False

    @abstractmethod
    def load_benchmark_data(self):
        raise NotImplementedError

    def perform_evaluation(self, recommender: RecommenderBase, mode: BenchmarkMode):
        raise NotImplementedError


    def get_documents_for_baseline(self):
        if self.documents_for_baseline_load:
            return self.document_ids
        else:
            self.document_ids = set()
            with open(self.path_to_document_ids, 'rt') as f:
                for line in f:
                    self.document_ids.add(int(line.strip()))
            print(f'Load {len(self.document_ids)} for {self.name}')
        self.documents_for_baseline_load = True