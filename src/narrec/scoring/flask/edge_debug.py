import logging
from collections import defaultdict

from flask import Flask, render_template

from kgextractiontoolbox.backend.models import Predication
from kgextractiontoolbox.backend.retrieve import retrieve_narrative_documents_from_database
from narraint.backend.database import SessionExtended
from narrant.entity.entityresolver import EntityResolver

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)
resolver = EntityResolver.instance()


def get_document_graph(document_id):
    document_id = int(document_id)
    session = SessionExtended.get()
    query = session.query(Predication)
    query = query.filter(Predication.document_collection == "PubMed")
    query = query.filter(Predication.document_id == document_id)
    query = query.filter(Predication.relation.isnot(None))
    facts = defaultdict(set)
    nodes = set()
    for r in query:
        try:
            subject_name = resolver.get_name_for_var_ent_id(r.subject_id, r.subject_type, resolve_gene_by_id=False)
            object_name = resolver.get_name_for_var_ent_id(r.object_id, r.object_type, resolve_gene_by_id=False)
            subject_name = f'{subject_name} ({r.subject_type})'
            object_name = f'{object_name} ({r.object_type})'
            if subject_name < object_name:
                key = subject_name, r.relation, object_name
                so_key = subject_name, object_name
            else:
                key = object_name, r.relation, subject_name
                so_key = object_name, subject_name
            if key not in facts:
                facts[so_key].add(r.relation)
                nodes.add(subject_name)
                nodes.add(object_name)
        except Exception:
            pass

    result = []
    for (s, o), predicates in facts.items():
        p_txt = []
        for p in predicates:
            # if there is a more specific edge then associated, ignore it
            if len(predicates) > 1 and p == "associated":
                continue
            p_txt.append(p)
        p_txt = '|'.join([pt for pt in p_txt])
        result.append(dict(s=s, p=p_txt, o=o))
    print(f'Querying document graph for document id: {document_id} - {len(facts)} facts found')
    session.remove()
    return str(dict(nodes=list(nodes), facts=result))


def get_document_content(document_id):
    session = SessionExtended.get()

    doc = (retrieve_narrative_documents_from_database(session, document_ids={document_id},
                                                          document_collection="PubMed")[0])
    doc.title = doc.title.replace('\'', ' ')
    doc.abstract = doc.abstract.replace('\'', ' ')
    return str(doc.to_dict())


app = Flask(__name__)


@app.route("/<document_id>")
def hello(document_id):
    return render_template("document.html", document_id=document_id,
                           # escape "
                           graph=get_document_graph(document_id).replace('\'', 'XXXXX'),
                           paper=get_document_content(document_id).replace('\'', 'XXXXX'))
