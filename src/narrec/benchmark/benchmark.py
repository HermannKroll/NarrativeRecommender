import logging
import os
from abc import abstractmethod
from enum import Enum

from narrec.config import GLOBAL_DB_DOCUMENT_COLLECTION, BENCHMKARK_QRELS_DIR


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

    def get_qrel_path(self):
        raise NotImplementedError

    def get_index_name(self):
        return self.name

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


class IRBenchmark(Benchmark):

    def __init__(self, name, path_to_document_ids):
        super().__init__(name=name, path_to_document_ids=path_to_document_ids, type=BenchmarkType.IR_BENCHMARK)

    @staticmethod
    def get_doc_query_key(query_id: int, doc_id: int) -> str:
        return f'Q{query_id}D{doc_id}'

    @staticmethod
    def get_doc_id_from_doc_query_key(doc_query_key: str) -> int:
        return int(doc_query_key.split('D')[-1])

    @staticmethod
    def get_query_id_from_doc_query_key(doc_query_key: str) -> int:
        # Take everything between Q and D
        return int(doc_query_key.split('D')[0][1:])

    def load_benchmark_data(self):
        # extend the dictionaries by own query doc keys (composed out of topic + input doc)
        # will not overwrite existing keys
        for querydockey, doc_id in self.iterate_over_document_entries():
            assert querydockey not in self.topic2relevant_docs
            assert querydockey not in self.topic2partially_relevant_docs
            assert querydockey not in self.topic2not_relevant_docs

            q_id = IRBenchmark.get_query_id_from_doc_query_key(querydockey)
            self.topic2relevant_docs[querydockey] = {rel_id for rel_id in self.topic2relevant_docs[q_id]
                                                     if rel_id != doc_id}
            self.topic2partially_relevant_docs[querydockey] = {rel_id
                                                               for rel_id in self.topic2partially_relevant_docs[q_id]
                                                               if rel_id != doc_id}
            self.topic2not_relevant_docs[querydockey] = {rel_id for rel_id in self.topic2not_relevant_docs[q_id]
                                                         if rel_id != doc_id}

    def get_qrel_path(self):
        path = os.path.join(BENCHMKARK_QRELS_DIR, f'{self.name}_qrels.txt')
        if not os.path.isfile(path):
            result_lines = []

            for querydockey, doc_id in self.iterate_over_document_entries():
                q_id = IRBenchmark.get_query_id_from_doc_query_key(querydockey)
                result_lines.extend(f'{querydockey}\t0\t{rel_id}\t2'
                                    for rel_id in self.topic2relevant_docs[q_id] if rel_id != doc_id)

                result_lines.extend(f'{querydockey}\t0\t{part_id}\t1'
                                    for part_id in self.topic2partially_relevant_docs[q_id] if part_id != doc_id)

                result_lines.extend(f'{querydockey}\t0\t{irrel_id}\t0'
                                    for irrel_id in self.topic2not_relevant_docs[q_id] if irrel_id != doc_id)

            with open(path, 'wt') as f:
                f.write('\n'.join(result_lines))

        return path

    def iterate_over_document_entries(self):
        for q_id in self.topics:
            for rel_doc_id in self.topic2relevant_docs[q_id.query_id]:
                yield IRBenchmark.get_doc_query_key(q_id.query_id, rel_doc_id), rel_doc_id
