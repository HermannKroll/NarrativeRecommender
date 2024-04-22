import ast

from narraint.backend.database import SessionExtended
from narraint.backend.models import TagInvertedIndex
from narrec.benchmark.benchmark import Benchmark
from narrec.document.core import NarrativeCoreExtractor, NarrativeConceptCore
from narrec.document.document import RecommenderDocument
from narrec.firststage.base import FirstStageBase
from narrec.firststage.fsconcept import FSConcept
from narrec.run_config import FS_DOCUMENT_CUTOFF


class FSConceptFlex(FSConcept):

    def __init__(self, extractor: NarrativeCoreExtractor, benchmark: Benchmark, name="FSConceptFlex"):
        super().__init__(name=name, extractor=extractor, benchmark=benchmark)

    def retrieve_documents_for(self, document: RecommenderDocument):
        # Compute the cores
        core = self.extractor.extract_concept_core(document)

        # We dont have any core
        if not core:
            return []

        # score documents with this core
        document_ids_scored = self.score_document_ids_with_core(core)

        # We did not find any documents
        if len(document_ids_scored) == 0:
            return []

        # Ensure cutoff
        return FirstStageBase.apply_dynamic_cutoff(document_ids_scored)
