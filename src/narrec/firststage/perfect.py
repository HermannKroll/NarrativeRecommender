from narraint.backend.database import SessionExtended
from narrec.benchmark.benchmark import Benchmark, BenchmarkMode, BenchmarkType
from narrec.document.document import RecommenderDocument
from narrec.firststage.base import FirstStageBase


class Perfect(FirstStageBase):

    def __init__(self, benchmark: Benchmark):
        super().__init__(name="Perfect")
        self.benchmark = benchmark
        self.session = SessionExtended.get()

    def retrieve_documents_for(self, document: RecommenderDocument):
        key = self.topic_idx
        if self.benchmark.type == BenchmarkType.REC_BENCHMARK:
            key = (self.topic_idx, document.id)

        rel, irr = self.benchmark.get_evaluation_data_for_topic(key, mode=BenchmarkMode.RELEVANT_PARTIAL_VS_IRRELEVANT)
        docs = set()
        docs.update(rel)
        docs.update(irr)

        return {(d, 1.0) for d in docs}