import json
import logging
import math

from kgextractiontoolbox.backend.models import Document
from narraint.backend.database import SessionExtended
from narraint.backend.models import PredicationInvertedIndex


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

    def get_idf_score(self, statement: tuple):
        # Introduce normalization here
        return math.log(self.get_document_count() / self.get_statement_documents(statement)) / math.log(self.document_count)

    def get_document_count(self):
        return self.document_count

    def get_statement_documents(self, statement: tuple):
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
