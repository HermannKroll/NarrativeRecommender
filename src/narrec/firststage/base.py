from narrec.document.document import RecommenderDocument
from narrec.run_config import FS_DOCUMENT_CUTOFF


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

    @staticmethod
    def apply_dynamic_cutoff(document_ids_scored):
        if len(document_ids_scored) > FS_DOCUMENT_CUTOFF:
            # get score at position
            score_at_cutoff = document_ids_scored[FS_DOCUMENT_CUTOFF][1]
            # search position where score is lower
            new_cutoff_position = 0
            for idx, (d, score) in enumerate(document_ids_scored[FS_DOCUMENT_CUTOFF:]):
                if score < score_at_cutoff:
                    new_cutoff_position = idx
                    break
            return document_ids_scored[:FS_DOCUMENT_CUTOFF + new_cutoff_position]
        else:
            # Ensure cutoff
            return document_ids_scored[:FS_DOCUMENT_CUTOFF]
