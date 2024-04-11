import json
import os
from datetime import datetime

from narrec.backend.retriever import DocumentRetriever
from narrec.citation.graph import CitationGraph
from narrec.config import INDEX_DIR
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.recommender.aligned_cores import AlignedCoresRecommender
from narrec.recommender.aligned_nodes import AlignedNodesRecommender
from narrec.recommender.coreoverlap import CoreOverlap
from narrec.recommender.equal import EqualRecommender
from narrec.recommender.graph_base_fallback_bm25 import GraphBaseFallbackBM25
from narrec.recommender.jaccard import Jaccard
from narrec.recommender.jaccard_combined import JaccardCombinedWeighted
from narrec.recommender.jaccard_concepts_weighted import JaccardConceptWeighted
from narrec.recommender.jaccard_graph_weighted import JaccardGraphWeighted
from narrec.recommender.statementoverlap import StatementOverlap
from narrec.run_config import ADD_GRAPH_BASED_BM25_FALLBACK_RECOMMENDERS
from narrec.scoring.BM25Scorer import BM25Scorer

relish_entry = """
{
  "pmid": "21397062",
        "response": {
            "relevant": [
                "18818955", "20147368", "20625291", "21191290", "21983221",
                "22399287", "23027747", "23201160", "24339795", "24699222",
                "24706765", "24966690", "25184538", "25540137", "25589264",
                "26446763", "27068403", "27219040", "27234911", "27899452",
                "27906866", "28033128", "29686978", "29793662"
            ],
            "partial": [
                "18385471", "18448590", "18949482", "19307729", "19348045",
                "19389850", "19780717", "19812536", "19903818", "20081299",
                "20511716", "20616717", "21130072", "21791920", "21848011",
                "23301036", "23636770", "23661805", "23689795", "23942199",
                "24100128", "24204001", "24965791", "29791908"
            ],
            "irrelevant": [
                "18667602", "19289823", "20924400", "21170879", "21468194",
                "22338089", "24715567", "24797667", "27129733", "29072386",
                "29102372", "29393102"
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

index_path = os.path.join(INDEX_DIR, "PM2020")
bm25_scorer = BM25Scorer(index_path)

recommenders = [EqualRecommender(), AlignedNodesRecommender(corpus), AlignedCoresRecommender(corpus),
                StatementOverlap(core_extractor), Jaccard(), CoreOverlap(extractor=core_extractor),
                JaccardGraphWeighted(corpus), JaccardConceptWeighted(corpus), JaccardCombinedWeighted(corpus)]

if ADD_GRAPH_BASED_BM25_FALLBACK_RECOMMENDERS:
    for r in recommenders.copy():
        recommenders.append(GraphBaseFallbackBM25(bm25scorer=bm25_scorer, graph_recommender=r))

rec_doc = id2docs[doc_id]

for recommender in recommenders:
    print('--' * 60)
    time = datetime.now()
    scored_docs = recommender.recommend_documents(rec_doc, docs, citation_graph=citation_graph)
    scored_docs = [(docid2label[int(d[0])], d[0], round(d[1], 2)) for d in scored_docs]
    print(f'{recommender.name} ({datetime.now() - time}s):\t{scored_docs}')
    print('--' * 60)
    print()
