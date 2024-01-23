import json

from narraint.backend.database import SessionExtended
from narraint.backend.models import PredicationInvertedIndex
from narrec.benchmark.benchmark import Benchmark
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.document import RecommenderDocument
from narrec.firststage.base import FirstStageBase
from narrec.run_config import FS_DOCUMENT_CUTOFF


class FSCore(FirstStageBase):

    def __init__(self, extractor: NarrativeCoreExtractor, benchmark: Benchmark, name="FSCore"):
        super().__init__(name=name)
        self.extractor = extractor
        self.benchmark = benchmark
        self.session = SessionExtended.get()

    def retrieve_documents(self, spo: tuple):
        q = self.session.query(PredicationInvertedIndex)
        q = q.filter(PredicationInvertedIndex.subject_id == spo[0])
        q = q.filter(PredicationInvertedIndex.relation == spo[1])
        q = q.filter(PredicationInvertedIndex.object_id == spo[2])

        document_ids = set()
        for row in q:
            prov_mapping = json.loads(row.provenance_mapping)
            for doc_col, docids2prov in prov_mapping.items():
                if doc_col == self.benchmark.document_collection:
                    for doc_id in docids2prov.keys():
                        doc_id_int = int(doc_id)
                        if self.benchmark.document_collection == "PubMed" and self.benchmark.get_documents_for_baseline():
                            if doc_id_int not in self.benchmark.get_documents_for_baseline():
                                document_ids.add(doc_id_int)

        return document_ids

    def retrieve_documents_for(self, document: RecommenderDocument):
        # Compute the cores
        cores = self.extractor.extract_narrative_core_from_document(document)

        # We dont have any core
        if not cores:
            return []

        # scores are sorted by their size
        max_core = cores[0]

        # Core statements are also sorted by their score
        document_ids_scored = []
        # dont add documents multiple times
        contained_doc_ids = set()
        for stmt in max_core.statements:
            # retrieve matching documents
            document_ids = self.retrieve_documents((stmt.subject_id, stmt.relation, stmt.object_id))
            # add all documents with the statement score to our list
            document_ids_scored.extend([(d, stmt.score) for d in document_ids if d not in contained_doc_ids])
            contained_doc_ids.update(document_ids)

            if len(document_ids) >= FS_DOCUMENT_CUTOFF:
                break

        # Ensure cutoff
        return document_ids_scored[:FS_DOCUMENT_CUTOFF]