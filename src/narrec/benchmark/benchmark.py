from abc import abstractmethod
from enum import Enum

from narrec.recommender.base import RecommenderBase


class BenchmarkMode(Enum):
    RELEVANT_VS_IRRELEVANT = 0
    RELEVANT_VS_PARTIAL_IRRELEVANT = 1
    RELEVANT_PARTIAL_VS_IRRELEVANT = 2


class Benchmark:

    def __init__(self):
        pass

    @abstractmethod
    def load_benchmark_data(self):
        raise NotImplementedError

    def perform_evaluation(self, recommender: RecommenderBase, mode: BenchmarkMode):
        raise NotImplementedError
