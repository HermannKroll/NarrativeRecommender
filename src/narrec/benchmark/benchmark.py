import logging
from abc import abstractmethod
from enum import Enum
from typing import List

from narrec.config import GLOBAL_DB_DOCUMENT_COLLECTION
from narrec.recommender.base import RecommenderBase


class BenchmarkMode(Enum):
    RELEVANT_VS_IRRELEVANT = 0
    RELEVANT_VS_PARTIAL_IRRELEVANT = 1
    RELEVANT_PARTIAL_VS_IRRELEVANT = 2

class BenchmarkType(Enum):
    IR_BENCHMARK = 0
    REC_BENCHMARK = 1

class Benchmark:

    def __init__(self, name, path_to_document_ids, type: BenchmarkType):
        self.document_collection = GLOBAL_DB_DOCUMENT_COLLECTION
        self.name = name
        self.document_ids = set()
        self.path_to_document_ids = path_to_document_ids
        self.documents_for_baseline_load = False

        self.topics = []
        self.topic2relevant_docs = {}
        self.topic2partially_relevant_docs = {}
        self.topic2not_relevant_docs = {}
        self.type = type

        self.load_benchmark_data()


    def get_evaluation_data_for_topic(self, topic: int, mode: BenchmarkMode):
        if mode == BenchmarkMode.RELEVANT_VS_IRRELEVANT:
            return self.topic2relevant_docs[topic], self.topic2not_relevant_docs[topic]
        elif mode == BenchmarkMode.RELEVANT_PARTIAL_VS_IRRELEVANT:
            relevant = set()
            relevant.update(self.topic2relevant_docs[topic])
            relevant.update(self.topic2partially_relevant_docs[topic])
            return relevant, self.topic2not_relevant_docs[topic]
        elif mode == BenchmarkMode.RELEVANT_VS_PARTIAL_IRRELEVANT:
            irrelevant = set()
            irrelevant.update(self.topic2partially_relevant_docs[topic])
            irrelevant.update(self.topic2not_relevant_docs[topic])
            return self.topic2relevant_docs[topic], irrelevant
        else:
            raise ValueError(f'Enum value {mode} unknown and not supported')

    @abstractmethod
    def load_benchmark_data(self):
        raise NotImplementedError


    def get_documents_for_baseline(self):
        if not self.documents_for_baseline_load:
            self.document_ids = set()
            logging.info(f'Loading ids from file: {self.path_to_document_ids}...')
            with open(self.path_to_document_ids, 'rt') as f:
                for line in f:
                    self.document_ids.add(int(line.strip()))
            logging.info(f'Load {len(self.document_ids)} for {self.name}')
        self.documents_for_baseline_load = True
        return self.document_ids

    def iterate_over_document_entries(self):
        raise NotImplementedError