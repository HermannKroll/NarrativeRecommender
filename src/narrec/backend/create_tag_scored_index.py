import json
from collections import defaultdict
from datetime import datetime

from narrant.entity.entityidtranslator import EntityIDTranslator
from sqlalchemy import delete
from tqdm import tqdm

from kgextractiontoolbox.document.document import TaggedEntity
from kgextractiontoolbox.document.narrative_document import NarrativeDocument
from kgextractiontoolbox.progress import Progress
from narraint.backend.models import Tag, Document
from narraint.config import QUERY_YIELD_PER_K
from narrec.backend.database import SessionRecommender
from narrec.backend.models import TagInvertedIndexScored
from narrec.config import GLOBAL_DB_DOCUMENT_COLLECTION
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.scoring.concept import score_concept_by_tf_idf_and_coverage

"""
The tag-cache dictionary uses strings instead of tuples as keys ('seen_keys') for predication entries. With this, 
the memory usage is lower.
"""

SEPERATOR_STRING = "_;_"


def compute_scored_inverted_index_for_tags(collection="PubMed"):
    start_time = datetime.now()
    session = SessionRecommender.get()

    print('Deleting old inverted index for tags...')
    stmt = delete(TagInvertedIndexScored)
    session.execute(stmt)
    session.commit()

    print('Counting db documents...')
    docid2narrative_doc = dict()
    doc_count = session.query(Document).filter(Document.collection == collection).count()
    print(f'{doc_count} documents found')
    print('Retrieving document data...')
    doc_query = session.query(Document).filter(Document.collection == collection)
    doc_query = doc_query.order_by(Document.id)

    for doc in tqdm(doc_query, total=doc_count):
        docid2narrative_doc[doc.id] = NarrativeDocument(document_id=doc.id, title=doc.title, abstract=doc.abstract)

    print('Counting the number of tags...')
    tag_count = session.query(Tag).filter(Tag.document_collection == collection).count()
    print(f'{tag_count} tags found')

    progress = Progress(total=tag_count, print_every=1000, text="Computing inverted tag index...")
    progress.start_time()

    query = session.query(Tag).filter(Tag.document_collection == collection)
    query = query.order_by(Tag.document_id)
    query = query.yield_per(QUERY_YIELD_PER_K * 100)

    index = defaultdict(set)
    print('Using the Gene Resolver to replace gene ids by symbols')
    entityidtranslator = EntityIDTranslator()
    for idx, tag_row in tqdm(enumerate(query), total=tag_count):
        progress.print_progress(idx)
        try:
            translated_id = entityidtranslator.translate_entity_id(tag_row.ent_id, tag_row.ent_type)
        except (KeyError, ValueError):
            continue

        key = SEPERATOR_STRING.join([str(translated_id), str(tag_row.ent_type), str(tag_row.document_collection)])
        doc_id = tag_row.document_id

        docid2narrative_doc[doc_id].tags.append(TaggedEntity(document=tag_row.document_id,
                                                             start=tag_row.start,
                                                             end=tag_row.end,
                                                             text=tag_row.ent_str,
                                                             ent_type=tag_row.ent_type,
                                                             ent_id=tag_row.ent_id))
        index[key].add(doc_id)

    # Convert all narrative documents to recommender documents to get the statistics
    print('Converting narrative documents to recommender documents...')
    docid2recommenderdoc = dict()
    for did, nd in tqdm(docid2narrative_doc.items()):
        docid2recommenderdoc[did] = RecommenderDocument(nd)

    corpus = DocumentCorpus(collections=[GLOBAL_DB_DOCUMENT_COLLECTION])

    print("Computing insert values...")
    insert_list = []
    for row_key, doc_ids in tqdm(index.items(), total=len(index)):
        entity_id, entity_type, doc_col = row_key.split(SEPERATOR_STRING)

        doc2score = {}
        for did in doc_ids:
            doc = docid2recommenderdoc[did]
            tf = doc.get_concept_tf(entity_id)
            doc2score[did] = (tf, score_concept_by_tf_idf_and_coverage(entity_id, doc, corpus))

        doc2score = sorted([(doc, tf, score) for doc, (tf, score) in doc2score.items()],
                           key=lambda x: int(x[0]),
                           reverse=True)
        insert_list.append(dict(entity_id=entity_id,
                                entity_type=entity_type,
                                document_collection=doc_col,
                                support=len(doc_ids),
                                scored_document_ids=json.dumps(doc2score)))
    progress.done()
    print('Beginning insert into tag_inverted_index table...')
    TagInvertedIndexScored.bulk_insert_values_into_table(session, insert_list, check_constraints=False, commit=True)
    insert_list.clear()

    session.commit()

    progress.done()

    end_time = datetime.now()
    print(f"Tag inverted index table created. Took me {end_time - start_time} minutes.")


def main():
    compute_scored_inverted_index_for_tags()


if __name__ == "__main__":
    main()
