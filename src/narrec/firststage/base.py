from typing import Dict, List, Tuple

from narrec.document.document import RecommenderDocument


class FirstStageBase:

    def __init__(self, name):
        self.name = name
        self.topic_idx = None

    def set_current_topic(self, topic_idx):
        self.topic_idx = topic_idx

    def retrieve_documents_for(self, document: RecommenderDocument):
        pass

    @staticmethod
    def normalize_and_sort_document_scores(document_ids_scored):
        # We did not find any documents
        if len(document_ids_scored) == 0:
            return []

        # Get the maximum score to normalize the scores
        max_score = max(document_ids_scored.values())
        if max_score > 0.0:
            # Convert to list
            document_ids_scored = [(k, v / max_score) for k, v in document_ids_scored.items()]
        else:
            document_ids_scored = [(k, v) for k, v in document_ids_scored.items()]
        # Sort by score and then doc desc
        document_ids_scored.sort(key=lambda x: (x[1], int(x[0])), reverse=True)
        return document_ids_scored
