from narrec.document.document import RecommenderDocument


class FirstStageBase:

    def __init__(self, name):
        self.name = name

    def retrieve_documents_for(self, document: RecommenderDocument):
        pass
