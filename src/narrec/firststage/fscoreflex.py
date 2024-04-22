import json

from sqlalchemy import or_, and_

from narraint.backend.database import SessionExtended
from narraint.backend.models import PredicationInvertedIndex
from narrec.benchmark.benchmark import Benchmark
from narrec.document.core import NarrativeCoreExtractor, NarrativeCore
from narrec.document.document import RecommenderDocument
from narrec.firststage.base import FirstStageBase
from narrec.firststage.fscore import FSCore
from narrec.run_config import FS_DOCUMENT_CUTOFF, CORE_TOP_K


class FSCoreFlex(FSCore):

    def __init__(self, extractor: NarrativeCoreExtractor, benchmark: Benchmark, name="FSCoreFlex"):
        super().__init__(name=name, extractor=extractor, benchmark=benchmark)

    def retrieve_documents_for(self, document: RecommenderDocument):
        # Compute the cores
        max_core = self.extractor.extract_narrative_core_from_document(document)

        # We dont have any core
        if not max_core:
            return []

        # score documents with this core
        document_ids_scored = self.score_document_ids_with_core(max_core)

        # We did not find any documents
        if len(document_ids_scored) == 0:
            return []

        return FirstStageBase.apply_dynamic_cutoff(document_ids_scored)