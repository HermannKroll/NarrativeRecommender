from kgextractiontoolbox.document.narrative_document import NarrativeDocument


class RecommenderDocument(NarrativeDocument):

    def __init__(self, nd: NarrativeDocument):
        super().__init__(document_id=nd.id, title=nd.title, abstract=nd.abstract,
                         metadata=nd.metadata, tags=nd.tags, sentences=nd.sentences,
                         extracted_statements=nd.extracted_statements)

        self.classification = nd.classification
