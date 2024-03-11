from narrec.document.document import RecommenderDocument


class FirstStageBase:

    def __init__(self, name):
        self.name = name
        self.topic_idx = None

    def set_current_topic(self, topic_idx):
        self.topic_idx = topic_idx

    def retrieve_documents_for(self, document: RecommenderDocument):
        pass
