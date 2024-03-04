import json
from datetime import datetime

from narrant.entity.entityresolver import EntityResolver
from narrec.backend.retriever import DocumentRetriever
from narrec.citation.graph import CitationGraph
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.recommender.aligned_cores import AlignedCoresRecommender
from narrec.recommender.aligned_nodes import AlignedNodesRecommender
from narrec.recommender.equal import EqualRecommender
from narrec.recommender.jaccard import Jaccard
from narrec.recommender.jaccard_weighted import JaccardWeighted
from narrec.recommender.statementoverlap import StatementOverlap
from narrec.scoring.edge import score_edge_sentence, score_edge

relish_entry = """
{
  "pmid": "27122312",
    "response": {
        "relevant": [
            "23639470", "24091716", "24598368"
        ],
        "irrelevant": [
            "24561820", "23927970", "23558901"
        ]
    }
}
"""

data = json.loads(relish_entry)
doc_id = int(data['pmid'])
relevant = {int(d) for d in data["response"]['relevant']}
irrelevant = {int(d) for d in data["response"]['irrelevant']}

docid2label = {d: "relevant" for d in relevant}
docid2label.update({d: "irrelevant" for d in irrelevant})

doc_ids = {doc_id}
doc_ids.update(relevant)
doc_ids.update(irrelevant)

retriever = DocumentRetriever()
corpus = DocumentCorpus(["PubMed"])
core_extractor = NarrativeCoreExtractor(corpus=corpus)
citation_graph = CitationGraph()

docs = list(retriever.retrieve_narrative_documents_for_collections(doc_ids, ["PubMed"]))
id2docs = {d.id: d for d in docs}
# don't recommend the input id
docs = [d for d in docs if d.id != doc_id]

recommenders = [EqualRecommender(),
                AlignedNodesRecommender(corpus), AlignedCoresRecommender(corpus),
                StatementOverlap(core_extractor), Jaccard(), JaccardWeighted(corpus)]

rec_doc = id2docs[doc_id]

for recommender in recommenders:
    print('--' * 60)
    time = datetime.now()
    scored_docs = recommender.recommend_documents(rec_doc, docs, citation_graph=citation_graph)
    scored_docs = [(docid2label[int(d[0])], d[0], round(d[1], 2)) for d in scored_docs]
    print(f'{recommender.name} ({datetime.now() - time}s):\t{scored_docs}')
    print('--' * 60)
    print()
