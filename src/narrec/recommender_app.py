import logging

from flask import Flask
import pyterrier as pt

from narraint.queryengine.engine import QueryEngine
from narraint.queryengine.result import QueryDocumentResult
from narrant.entity.entityresolver import EntityResolver
from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import Benchmark, BenchmarkType
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.firststage.create_bm25_index import BenchmarkIndex
from narrec.firststage.fsnodeflex import FSNodeFlex
from narrec.recommender.coreoverlap import CoreOverlap

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

CREATE_PUBMED_BM25_INDEX = True

pt.init()

# Faked benchmark object that allows all documents within our db
class PubMedBenchmark(Benchmark):

    def __init__(self):
        super().__init__(name="PubMed", path_to_document_ids=None, type=BenchmarkType.REC_BENCHMARK)

    def get_documents_for_baseline(self):
        return None


if CREATE_PUBMED_BM25_INDEX:
    index = BenchmarkIndex(PubMedBenchmark())

resolver = EntityResolver()
retriever = DocumentRetriever()
corpus = DocumentCorpus(["PubMed"])
corpus.load_all_support_into_memory()
core_extractor = NarrativeCoreExtractor(corpus=corpus)

first_stage = FSNodeFlex(extractor=core_extractor, benchmark=PubMedBenchmark())

recommender = CoreOverlap(extractor=core_extractor)

# index_path = os.path.join(INDEX_DIR, "pubmed")
# bm25_scorer = BM25Scorer(index_path)

# recommender = GraphBaseFallbackBM25(bm25scorer=bm25_scorer, graph_recommender=recommender_coreoverlap)

app = Flask(__name__)


@app.route("/<document_id>")
def hello(document_id):
    document_id = int(document_id)
    collection = "PubMed"

    # Step 1: First stage retrieval
    print('Step 1: Perform first stage retrieval...')
    input_docs = retriever.retrieve_narrative_documents(document_ids=[document_id],
                                                        document_collection=collection)
    if len(input_docs) != 1:
        return "Error"

    input_doc = input_docs[0]
    candidate_document_ids = first_stage.retrieve_documents_for(input_doc)

    # Step 2: document data retrieval
    print('Step 2: Query document data...')
    retrieved_doc_ids = [d[0] for d in candidate_document_ids]
    documents = retriever.retrieve_narrative_documents(retrieved_doc_ids, collection)
    docid2doc = {d.id: d for d in documents}

    # Step 3: recommendation
    print('Step 3: Perform recommendation...')
    rec_doc_ids = recommender.recommend_documents(input_doc, documents, citation_graph=None)
    # ingore scores
    rec_doc_ids = [d[0] for d in rec_doc_ids]
    ranked_docs = [docid2doc[d] for d in rec_doc_ids]

    # Step 4: Get cores of all documents

    # Produce the result
    print('Step 4: Converting results...')
    results = []
    for rec_doc in ranked_docs:
        results.append(QueryDocumentResult(document_id=rec_doc.id,
                                           title=rec_doc.title, authors="", journals="",
                                           publication_year=0, publication_month=0,
                                           var2substitution={}, confidence=0.0,
                                           position2provenance_ids={},
                                           org_document_id=None, doi=None,
                                           document_collection="PubMed", document_classes=None))

    print('Step 5: Loading document metadata...')
    # Load metadata for the documents
    results = QueryEngine.enrich_document_results_with_metadata(results, {"PubMed": rec_doc_ids})

    # Convert to a json structure
    results_converted = [r.to_dict() for r in results]
    print('Step 6: Enriching with graph data...')
    for r in results_converted:
        facts = [{'s': 'Metformin', 'p': 'treats', 'o': 'Diabetes Mellitus'}]
        nodes = ['Metformin', 'Diabetes Mellitus']

        data = {
            "nodes": [],
            "edges": []
        }

        node_id_map = {}
        next_node_id = 1

        for node in nodes:
            node_id = next_node_id
            node_id_map[node] = node_id
            data["nodes"].append({"id": node_id, "label": node})
            next_node_id += 1

        for fact in facts:
            source_id = node_id_map[fact["s"]]
            target_id = node_id_map[fact["o"]]
            data["edges"].append({"from": source_id, "to": target_id, "label": fact["p"]})
        r["graph_data"] = data

    return results_converted
