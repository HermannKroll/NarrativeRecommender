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
    "pmid": "22569528",
    "response": {
        "relevant": [
            "17928366", "18562239", "19052640", "19060905", "19242111",
            "19244124", "19414607", "19805545", "19816936", "20079430",
            "20811985", "22028468", "22177953", "23549785", "23712012",
            "24089523", "25350931", "26235619", "27376062", "28474232",
            "29454854"
        ],
        "partial": [],
        "irrelevant": [
            "18280112", "18332145", "18463290", "18665890", "18983981",
            "19114553", "19282669", "19361221", "19541618", "19583964",
            "19835659", "20226096", "20674547", "20868520", "21098038",
            "21102438", "21135229", "21135874", "21144847", "21403838",
            "21596018", "21730285", "21833774", "22056560", "22065579",
            "22257058", "22292131", "23560844", "23603816", "23817184",
            "24113259", "24158441", "24185007", "24434059", "24602610",
            "26838549", "27226552", "27422819", "28396345"
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
    print('--'*60)
    time = datetime.now()
    scored_docs = recommender.recommend_documents(rec_doc, docs, citation_graph=citation_graph)
    scored_docs = [(docid2label[int(d[0])], d[0], round(d[1], 2)) for d in scored_docs]
    print(f'{recommender.name} ({datetime.now()- time}s):\t{scored_docs}')
    print('--'*60)
    print()
