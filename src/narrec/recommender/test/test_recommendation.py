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
  "pmid": "29475924",
    "response": {
        "relevant": [
            "18427755", "18707817", "19107346", "20564129", "20638188",
            "22817686", "23138773", "23519358", "23740156", "23740157",
            "23830191", "23861153", "23871680", "24778060", "25240823",
            "25275060", "25368288", "25472758", "25854390", "26124381",
            "26408718", "26637898", "26977000", "27263126", "28061768",
            "28237400", "29715126", "29715148"
        ],
        "partial": [
            "19619958", "22513917", "22528795", "23187817", "23717789",
            "24488446", "24621620", "24658606", "25061863", "25154301",
            "25434933", "25434935", "25434941", "25993245", "26625767",
            "28476824", "28675121"
        ],
        "irrelevant": [
            "18596426", "19402900", "20004125", "23053138", "23205789",
            "23376580", "23563213", "23662828", "24439342", "24923058",
            "25885321", "26209921", "26539264", "27542716", "29125123"
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
