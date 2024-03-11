from narrec.citation.graph import CitationGraph
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.recommender.graph_base import GraphBase
from narrec.run_config import NODE_SIMILARITY_THRESHOLD
from narrec.scoring.edge import score_edge_by_tf_and_concept_idf


class AlignedNodesRecommender(GraphBase):
    def __init__(self, corpus: DocumentCorpus, name="AlignedNodesRecommender", threshold=NODE_SIMILARITY_THRESHOLD):
        super().__init__(threshold, name=name)
        self.corpus = corpus
        self.extractor = NarrativeCoreExtractor(corpus=self.corpus)

    def node_score(self, node, document_i: RecommenderDocument):
        core = self.extractor.extract_narrative_core_from_document(document_i)
        scores = [score_edge_by_tf_and_concept_idf(statement.get_triple(), document_i, self.corpus)
                  for statement in core.statements
                  if statement.subject_id == node or statement.object_id == node]
        if len(scores) == 0:
            return 0.0
        return sum(scores) / len(scores)

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        node_matchings = self.greedy_node_matching(doc, candidate)
        if len(node_matchings) == 0:
            return 0.0
        total_score = 0
        for node_a, node_b in node_matchings:
            similarity = self.ontological_node_similarity(node_a, node_b)
            score = self.node_score(node_b, candidate)
            total_score += similarity * score
        return total_score / len(doc.nodes)
