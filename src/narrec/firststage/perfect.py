from kgextractiontoolbox.backend.models import Document
from narraint.backend.database import SessionExtended
from narrec.benchmark.benchmark import Benchmark, BenchmarkMode, BenchmarkType
from narrec.config import GLOBAL_DB_DOCUMENT_COLLECTION
from narrec.document.document import RecommenderDocument
from narrec.firststage.base import FirstStageBase


class Perfect(FirstStageBase):

    def __init__(self, benchmark: Benchmark):
        super().__init__(name="Perfect")
        self.benchmark = benchmark
        session = SessionExtended.get()
        self.document_ids_in_db = set()
        print(f'Perfect stage: querying document ids for collection: {GLOBAL_DB_DOCUMENT_COLLECTION}')
        for row in session.query(Document.id).filter(Document.collection == GLOBAL_DB_DOCUMENT_COLLECTION):
            self.document_ids_in_db.add(row.id)
        print(f'{len(self.document_ids_in_db)} document ids in DB')

    def retrieve_documents_for(self, document: RecommenderDocument):
        key = self.topic_idx
        if self.benchmark.type == BenchmarkType.REC_BENCHMARK:
            key = (self.topic_idx, document.id)

        rel, irr = self.benchmark.get_evaluation_data_for_topic(key, mode=BenchmarkMode.RELEVANT_PARTIAL_VS_IRRELEVANT)
        docs = set()
        docs.update(rel)
        docs.update(irr)

        return {(d, 1.0) for d in docs if int(d) in self.document_ids_in_db}
