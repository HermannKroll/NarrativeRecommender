import logging
import os

from flask import Flask
import pyterrier as pt

from narraint.queryengine.engine import QueryEngine
from narraint.queryengine.result import QueryDocumentResult
from narrant.entity.entityresolver import EntityResolver
from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import Benchmark, BenchmarkType
from narrec.config import INDEX_DIR
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.firststage.create_bm25_index import BenchmarkIndex
from narrec.firststage.fsnodeflex import FSNodeFlex
from narrec.recommender.coreoverlap import CoreOverlap
from narrec.recommender.graph_base_fallback_bm25 import GraphBaseFallbackBM25
from narrec.scoring.BM25Scorer import BM25Scorer

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

CREATE_PUBMED_BM25_INDEX = False

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

recommender_coreoverlap = CoreOverlap(extractor=core_extractor)

index_path = os.path.join(INDEX_DIR, "PubMed")
bm25_scorer = BM25Scorer(index_path)

recommender = GraphBaseFallbackBM25(bm25scorer=bm25_scorer, graph_recommender=recommender_coreoverlap)

app = Flask(__name__)

enttype2colour = {
    "Disease": "#aeff9a",
    "Drug": "#ff8181",
    "Species": "#b88cff",
    "Excipient": "#ffcf97",
    "LabMethod": "#9eb8ff",
    "Chemical": "#fff38c",
    "Gene": "#87e7ff",
    "Target": "#1fe7ff",
    "Method": "#7897ff",
    "DosageForm": "#9189ff",
    "Mutation": "#8cffa9",
    "ProteinMutation": "#b9ffcb",
    "DNAMutation": "#4aff78",
    "Variant": "#ffa981",
    "CellLine": "#00bc0f",
    "SNP": "#fd83ca",
    "DomainMotif": "#f383fd",
    "Plant": "#dcfd83",
    "Strain": "#75c4c7",
    "Vaccine": "#c7767d",
    "HealthStatus": "#bbaabb",
    "Organism": "#00bc0f",
    "Tissue": "#dc8cff"
}

NOT_CONTAINED_COLOUR = "#FFFFFF"
NOT_CONTAINED_COLOUR_EDGE = "#E5E4E2"

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
    input_core = core_extractor.extract_narrative_core_from_document(input_doc)
    input_core_concept = core_extractor.extract_concept_core(input_doc)
    candidate_document_ids = first_stage.retrieve_documents_for(input_doc)
    candidate_document_ids = [d for d in candidate_document_ids if d[0] != input_doc.id]

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

    # get input core concepts
    input_core_concepts = set([sc.concept for sc in input_core_concept.concepts])

    # Convert to a json structure
    results_converted = [r.to_dict() for r in results]
    print('Step 6: Enriching with graph data...')
    for r in results_converted:
        NO_STATEMENTS_TO_SHOW = 6
        rec_doc = docid2doc[int(r["docid"])]
        rec_core = core_extractor.extract_narrative_core_from_document(rec_doc)
        facts = []
        nodes = set()
        # nodes that overlap between input doc and rec doc
        overlapping_nodes = set()

        if rec_core:
            core_intersection = input_core.intersect(rec_core)
            core_intersection.statements.sort(key=lambda x: x.score, reverse=True)
            visited = set()

            if core_intersection and len(core_intersection.statements) > 0:
                for s in core_intersection.statements:
                    if len(facts) > NO_STATEMENTS_TO_SHOW:
                        break

                    try:
                        subject_name = resolver.get_name_for_var_ent_id(s.subject_id, s.subject_type,
                                                                        resolve_gene_by_id=False)
                        object_name = resolver.get_name_for_var_ent_id(s.object_id, s.object_type,
                                                                       resolve_gene_by_id=False)

                        if (subject_name, object_name) in visited:
                            continue
                        if (object_name, subject_name) in visited:
                            continue

                        visited.add((subject_name, object_name))
                        visited.add((object_name, subject_name))

                        # none means default colour
                        facts.append(({'s': subject_name, 'p': s.relation, 'o': object_name}, None))
                        nodes.add((subject_name, s.subject_type))
                        nodes.add((object_name, s.object_type))

                        overlapping_nodes.add((subject_name, s.subject_type))
                        overlapping_nodes.add((object_name, s.object_type))
                    except KeyError:
                        pass

            for s in rec_core.statements:
                if len(facts) > NO_STATEMENTS_TO_SHOW * 2:
                    break
                if s.subject_id in input_core_concepts or s.object_id in input_core_concepts:
                    try:
                        subject_name = resolver.get_name_for_var_ent_id(s.subject_id, s.subject_type,
                                                                        resolve_gene_by_id=False)
                        object_name = resolver.get_name_for_var_ent_id(s.object_id, s.object_type,
                                                                       resolve_gene_by_id=False)

                        if (subject_name, object_name) in visited:
                            continue
                        if (object_name, subject_name) in visited:
                            continue

                        visited.add((subject_name, object_name))
                        visited.add((object_name, subject_name))

                        facts.append(({'s': subject_name, 'p': s.relation, 'o': object_name}, NOT_CONTAINED_COLOUR_EDGE))
                        nodes.add((subject_name, s.subject_type))
                        nodes.add((object_name, s.object_type))

                        if s.subject_id in input_core_concepts:
                            overlapping_nodes.add((subject_name, s.subject_type))
                        else:
                            overlapping_nodes.add((object_name, s.object_type))
                    except KeyError:
                        pass

        else:
            facts = []
            nodes = set()

        # facts = [{'s': 'Metformin', 'p': 'treats', 'o': 'Diabetes Mellitus'}]
        # nodes = ['Metformin', 'Diabetes Mellitus']
        #
        data = {
            "nodes": [],
            "edges": []
        }

        node_id_map = {}
        next_node_id = 1

        for node, node_type in nodes:
            node_id = next_node_id
            node_id_map[node] = node_id

            if (node, node_type) in overlapping_nodes:
                data["nodes"].append({"id": node_id, "label": node, "color": enttype2colour[node_type]})
            else:
                data["nodes"].append({"id": node_id, "label": node, "color": NOT_CONTAINED_COLOUR})
            next_node_id += 1

        for fact, colour in facts:
            source_id = node_id_map[fact["s"]]
            target_id = node_id_map[fact["o"]]
            if colour == NOT_CONTAINED_COLOUR_EDGE:
                data["edges"].append({"from": source_id, "to": target_id, "label": fact["p"],
                                      "color": NOT_CONTAINED_COLOUR_EDGE, "dashes": "true"})
            else:
                data["edges"].append({"from": source_id, "to": target_id, "label": fact["p"]})
        r["graph_data"] = data

    return results_converted
