import json
from collections import defaultdict
from datetime import datetime

from sqlalchemy import delete

from kgextractiontoolbox.backend.models import Predication
from kgextractiontoolbox.progress import Progress
from narraint.config import QUERY_YIELD_PER_K
from narrec.backend.database import SessionRecommender
from narrec.backend.models import NodeInvertedIndex


def compute_node_inverted_index(collection="PubMed"):
    session = SessionRecommender.get()
    print('Deleting old inverted index for nodes...')
    stmt = delete(NodeInvertedIndex)
    session.execute(stmt)
    session.commit()

    print('Counting the number of predications...')
    pred_count = session.query(Predication)
    pred_count = pred_count.filter(Predication.document_collection == collection)
    pred_count = pred_count.filter(Predication.relation != None)
    pred_count = pred_count.count()
    print(f'{pred_count} predication were found')

    start_time = datetime.now()
    # "is not None" instead of "!=" None" DOES NOT WORK!
    prov_query = session.query(Predication.document_id, Predication.subject_id, Predication.object_id)
    prov_query = prov_query.filter(Predication.relation != None)
    prov_query = prov_query.yield_per(10 * QUERY_YIELD_PER_K)

    insert_list = []
    print("Starting...")
    concept2docs = defaultdict(set)

    progress = Progress(total=pred_count, print_every=1000, text="denormalizing predication...")
    progress.start_time()

    for idx, prov in enumerate(prov_query):
        progress.print_progress(idx)
        s_id = prov.subject_id
        o_id = prov.object_id

        for concept in [s_id, o_id]:
            concept2docs[concept].add(prov.document_id)

    key_count = len(concept2docs)
    progress2 = Progress(total=key_count, print_every=100, text="insert values...")
    progress2.start_time()
    for idx, concept in enumerate(concept2docs):
        progress2.print_progress(idx)
        assert len(concept2docs[concept]) > 0

        doc_list = sorted([d for d in concept2docs[concept]], reverse=True)

        insert_list.append(dict(
            entity_id=concept,
            document_collection=collection,
            support=len(doc_list),
            document_ids=json.dumps(doc_list)
        ))
    progress2.done()

    NodeInvertedIndex.bulk_insert_values_into_table(session, insert_list)
    insert_list.clear()
    session.commit()

    progress.done()

    end_time = datetime.now()
    print(f"Query table created. Took me {end_time - start_time} minutes.")


def main():
    compute_node_inverted_index()


if __name__ == "__main__":
    main()
