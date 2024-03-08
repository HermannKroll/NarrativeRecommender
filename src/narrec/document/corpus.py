import json
import logging
import math

from kgextractiontoolbox.backend.models import Document
from narraint.backend.database import SessionExtended
from narraint.backend.models import PredicationInvertedIndex, TagInvertedIndex
from narrant.cleaning.pharmaceutical_vocabulary import SYMMETRIC_PREDICATES


class DocumentCorpus:

    def __init__(self, collections: [str]):
        self.collections = collections

        logging.info(f'Estimating size of document corpus (collections = {self.collections})')
        session = SessionExtended.get()
        self.document_count = 0
        for collection in collections:
            logging.info(f'Counting documents in collection: {collection}')
            col_count = session.query(Document.id).filter(Document.collection == collection).count()
            self.document_count += col_count
            logging.info(f'{col_count} documents found')

        logging.info(f'{self.document_count} documents in corpus')
        self.cache_statement2count = dict()
        self.cache_concept2support = dict()


    def get_idf_score(self, statement: tuple):
        # Introduce normalization here
        return math.log(self.get_document_count() / self.get_statement_documents(statement)) / math.log(self.document_count)

    def get_concept_ifd_score(self, entity_id: str):
        return math.log(self.get_document_count() / self.get_concept_support(entity_id))

    def get_document_count(self):
        return self.document_count

    def _get_statement_documents_without_symmetric(self, statement: tuple):
        # number of documents which support the statement
        if statement in self.cache_statement2count:
            return self.cache_statement2count[statement]

        session = SessionExtended.get()
        q = session.query(PredicationInvertedIndex.support)
        q = q.filter(PredicationInvertedIndex.subject_id == statement[0])
        q = q.filter(PredicationInvertedIndex.relation == statement[1])
        q = q.filter(PredicationInvertedIndex.object_id == statement[2])

        support = 0
        for row in q:
            support += row.support

        self.cache_statement2count[statement] = support
        return support

    def get_statement_documents(self, statement: tuple):
        if statement[1] in SYMMETRIC_PREDICATES:
            support = (self._get_statement_documents_without_symmetric(statement) +
                       self._get_statement_documents_without_symmetric((statement[2], statement[1], statement[0])))
        else:
            support = self._get_statement_documents_without_symmetric(statement)

        assert support > 0
        return support

    def get_concept_support(self, entity_id):
        if entity_id in self.cache_concept2support:
            return self.cache_concept2support[entity_id]

        session = SessionExtended.get()
        q = session.query(TagInvertedIndex.support)
        q = q.filter(TagInvertedIndex.entity_id == entity_id)
        support = 0
        for row in q:
            support += row.support

        if support == 0:
            support = 1

        self.cache_concept2support[entity_id] = support
        return support
