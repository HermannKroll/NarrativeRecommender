from typing import List

from kgextractiontoolbox.document.document import TaggedEntity
from kgextractiontoolbox.document.narrative_document import NarrativeDocument, NarrativeDocumentMetadata, \
    DocumentSentence, StatementExtraction


class RecommenderDocument(NarrativeDocument):

    def __init__(self, document_id: int = None, title: str = None, abstract: str = None,
                 metadata: NarrativeDocumentMetadata = None,
                 tags: List[TaggedEntity] = [],
                 sentences: List[DocumentSentence] = [],
                 extracted_statements: List[StatementExtraction] = []):
        super().__init__(document_id=document_id, title=title, abstract=abstract,
                         metadata=metadata, tags=tags, sentences=sentences, extracted_statements=extracted_statements)



