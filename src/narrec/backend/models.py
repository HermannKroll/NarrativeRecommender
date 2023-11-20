from sqlalchemy import Column, String, Integer

from narraint.backend.models import Extended, DatabaseTable

BULK_QUERY_CURSOR_COUNT_DEFAULT = 10000

Recommender = Extended


class DocumentCitation(Recommender, DatabaseTable):
    __tablename__ = "document_citation"

    document_source_id = Column(Integer, primary_key=True)
    document_source_collection = Column(String, primary_key=True)
    document_target_id = Column(Integer, primary_key=True)
    document_target_collection = Column(String, primary_key=True)
