from collections import defaultdict

from kgextractiontoolbox.document.narrative_document import NarrativeDocument
from narrant.cleaning.pharmaceutical_vocabulary import SYMMETRIC_PREDICATES


class RecommenderDocument(NarrativeDocument):

    def __init__(self, nd: NarrativeDocument):
        super().__init__(document_id=nd.id, title=nd.title, abstract=nd.abstract,
                         metadata=nd.metadata, tags=nd.tags, sentences=nd.sentences,
                         extracted_statements=nd.extracted_statements)

        self.extracted_statements = [s for s in self.extracted_statements if s.relation]
        self.extracted_statements = [s for s in self.extracted_statements if s.subject_type != s.object_type]

        self.classification = nd.classification

        self.spo2confidences = defaultdict(list)
        self.spo2frequency = dict()
        self.spo2sentences = dict()
        self.sentence2spo = dict()
        self.graph = set()
        self.nodes = set()
        self.concept2frequency = dict()

        if self.extracted_statements:
            for statement in self.extracted_statements:
                spos = [(statement.subject_id, statement.relation, statement.object_id)]
                if statement.relation in SYMMETRIC_PREDICATES:
                    spos.append((statement.object_id, statement.relation, statement.subject_id))

                for spo in spos:
                    self.spo2confidences[spo].append(statement.confidence)

                    if statement.sentence_id not in self.sentence2spo:
                        self.sentence2spo[statement.sentence_id] = {spo}
                    else:
                        self.sentence2spo[statement.sentence_id].add(spo)

                    if spo not in self.spo2frequency:
                        self.spo2frequency[spo] = 1
                        self.spo2sentences[spo] = {statement.sentence_id}
                    else:
                        self.spo2frequency[spo] += 1
                        self.spo2sentences[spo].add(statement.sentence_id)

                    for concept in [statement.subject_id, statement.object_id]:
                        if concept in self.concept2frequency:
                            self.concept2frequency[concept] += 1
                        else:
                            self.concept2frequency[concept] = 1

                    self.graph.add(spo)
                    self.nodes.add(statement.subject_id)
                    self.nodes.add(statement.object_id)

            self.max_statement_frequency = max(self.spo2frequency.values())
