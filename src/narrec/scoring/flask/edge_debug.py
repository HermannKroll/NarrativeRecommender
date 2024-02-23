import logging

from flask import Flask, render_template

from kgextractiontoolbox.backend.models import Predication
from kgextractiontoolbox.backend.retrieve import retrieve_narrative_documents_from_database
from narraint.backend.database import SessionExtended
from narrant.entity.entityresolver import EntityResolver
from narrec.backend.retriever import DocumentRetriever
from narrec.document.corpus import DocumentCorpus
from narrec.scoring.edge import score_edge, score_edge_sentence, score_edge_connectivity, score_edge_confidence, \
    score_edge_tfidf

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

resolver = EntityResolver.instance()
retriever = DocumentRetriever()
corpus = DocumentCorpus(["PubMed"])

SCORE_FUNCTIONS = [
    ("confidence", score_edge_confidence),
    ("tfidf", score_edge_tfidf),
    ("tfidf+conf", score_edge),
    ("tfidf+conf+sentence", score_edge_sentence),
    ("connectivity", score_edge_connectivity)
]

def retrieve_document_graph(document_id):
    session = SessionExtended.get()
    query = session.query(Predication)
    query = query.filter(Predication.document_collection == "PubMed")
    query = query.filter(Predication.document_id == document_id)
    query = query.filter(Predication.relation.isnot(None))
    facts = set()
    nodes = set()

    docs = list(retriever.retrieve_narrative_documents_for_collections([document_id], ["PubMed"]))
    doc = docs[0]

    result = []
    for r in query:
        try:
            subject_name = resolver.get_name_for_var_ent_id(r.subject_id, r.subject_type, resolve_gene_by_id=False)
            object_name = resolver.get_name_for_var_ent_id(r.object_id, r.object_type, resolve_gene_by_id=False)
            subject_name = f'{subject_name} ({r.subject_type})'
            object_name = f'{object_name} ({r.object_type})'
            key = subject_name, r.relation, object_name
            if key not in facts:
                scores = {}
                for name, score_function in SCORE_FUNCTIONS:
                    edge = (r.subject_id, r.relation, r.object_id)
                    scores[name] = round(score_function(edge, doc, corpus), 2)

                result.append(dict(s=subject_name, p=r.relation, o=object_name, scores=scores))
                facts.add(key)
                nodes.add(subject_name)
                nodes.add(object_name)
        except Exception:
            pass

    session.remove()
    print(f'Querying document graph for document id: {document_id} - {len(facts)} facts found')

    # Apply filter
    scores = [res["scores"]["tfidf+conf"] for res in result]
    print(scores)
    avg_score = sum(scores) / len(scores)
    result = [r for r in result if r["scores"]["tfidf+conf"] >= avg_score]
    nodes = set()
    for r in result:
        nodes.add(r["s"])
        nodes.add(r["o"])

    return result, nodes

def get_document_graph(document_id):
    document_id = int(document_id)
    result, nodes = retrieve_document_graph(document_id)
    return str(dict(nodes=list(nodes), facts=result))


def get_document_graph_intersection(document_ids):
    docs = document_ids.split(',')
    assert len(docs) == 2
    docid_a = int(docs[0])
    docid_b = int(docs[1])

    result_a, nodes_a = retrieve_document_graph(docid_a)
    result_b, nodes_b = retrieve_document_graph(docid_b)

    result = []
    for a in result_a:
        found = False
        for b in result_b:
            if a["s"] == b["s"] and a["o"] == b["o"]:
                found = True
                break
            if a["s"] == b["o"] and a["o"] == b["s"]:
                found = True
                break
        if found:
            result.append(a)

    nodes = set()
    for r in result:
        nodes.add(r["s"])
        nodes.add(r["o"])

    return str(dict(nodes=list(nodes), facts=result))



def get_document_content(document_id):
    session = SessionExtended.get()
    document_id = int(document_id.split(',')[0])

    doc = (retrieve_narrative_documents_from_database(session, document_ids={document_id},
                                                      document_collection="PubMed")[0])
    doc.title = doc.title.replace('\'', ' ')
    doc.abstract = doc.abstract.replace('\'', ' ')
    return str(doc.to_dict())


app = Flask(__name__)


@app.route("/<document_id>")
def hello(document_id):
    return render_template("document.html", document_id=int(document_id.split(',')[0]),
                           # escape "
                           graph=get_document_graph_intersection(document_id).replace('\'', 'XXXXX'),
                           paper=get_document_content(document_id).replace('\'', 'XXXXX'))
