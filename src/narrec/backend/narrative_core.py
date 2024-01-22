from narrec.document.document import RecommenderDocument
from narraint.backend.database import SessionExtended
from narraint.backend.models import Predication


def retrieve_facts(document_id):
    document_id = int(document_id)
    session = SessionExtended.get()
    query = session.query(Predication)
    query = query.filter(Predication.document_id == document_id)
    query = query.filter(Predication.relation.isnot(None))
    facts = [{'s': r.subject_id, 'p': r.relation, 'o': r.object_id} for r in query]
    session.remove()
    return facts


def score_edge(fact):
    return fact.update({"score": 0})


def extract_narrative_core_from_document(document: RecommenderDocument, threshold):
    facts = retrieve_facts(document.id)
    scored_facts = [scored_fact for fact in facts if (scored_fact := score_edge(fact)) >= threshold]
    return scored_facts

