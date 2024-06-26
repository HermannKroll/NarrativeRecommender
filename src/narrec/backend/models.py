from sqlalchemy import Column, String, Integer, ForeignKeyConstraint

from narraint.backend.models import Extended, DatabaseTable

BULK_QUERY_CURSOR_COUNT_DEFAULT = 10000

Recommender = Extended


class DocumentCitation(Recommender, DatabaseTable):
    __tablename__ = "document_citation"
    __table_args__ = (
        ForeignKeyConstraint(('document_source_id', 'document_source_collection'),
                             ('document.id', 'document.collection')),
        ForeignKeyConstraint(('document_target_id', 'document_target_collection'),
                             ('document.id', 'document.collection')),
    )

    document_source_id = Column(Integer, primary_key=True)
    document_source_collection = Column(String, primary_key=True)
    document_target_id = Column(Integer, primary_key=True)
    document_target_collection = Column(String, primary_key=True)


class TagInvertedIndexScored(Extended, DatabaseTable):
    __tablename__ = "tag_inverted_index_scored"

    entity_id = Column(String, nullable=False, index=True, primary_key=True)
    document_collection = Column(String, nullable=False, index=True, primary_key=True)
    support = Column(Integer, nullable=False)
    scored_document_ids = Column(String, nullable=False)

class NodeInvertedIndex(Extended, DatabaseTable):
    __tablename__ = "node_inverted_index"

    entity_id = Column(String, nullable=False, index=True, primary_key=True)
    document_collection = Column(String, nullable=False, index=True, primary_key=True)
    support = Column(Integer, nullable=False)
    document_ids = Column(String, nullable=False)