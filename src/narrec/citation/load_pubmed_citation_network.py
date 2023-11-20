import glob
import gzip
import logging
from argparse import ArgumentParser
from datetime import datetime
from typing import Set, Dict, List

from lxml import etree

from narrec.backend.database import SessionRecommender
from narrec.backend.models import DocumentCitation
from kgextractiontoolbox.backend.models import Document
from kgextractiontoolbox.progress import print_progress_with_eta


def pubmed_medline_load_document_citations(filename: str, document_ids: Set[int], document_collection: str) \
        -> (List[Dict], Set[int]):
    """
    Extracts the PubMed Medline Citations from an xml file
    :param filename: an PubMed Medline xml file
    :param document_ids: a set of relevant document ids
    :param document_collection: the corresponding document collection
    :return: A list of dictionaries corresponding to DocumentCitation, a list of processed document ids
    """
    if filename.endswith('.xml'):
        with open(filename) as f:
            tree = etree.parse(f)
    elif filename.endswith('.xml.gz'):
        with gzip.open(filename) as f:
            tree = etree.parse(f)

    citations_to_insert = []
    pmids_processed = set()
    for article in tree.iterfind("PubmedArticle"):

        # Get PMID
        pmids = article.findall("./MedlineCitation/PMID")
        if len(pmids) > 1:
            logging.warning(f"PubMed citation has more than one PMID {pmids}")
            continue  # BAD

        pmid = int(pmids[0].text)
        if pmid not in document_ids or pmid in pmids_processed:
            continue
        pmids_processed.add(pmid)

        citation_list = set()
        for citation in article.findall('./PubmedData/ReferenceList/Reference'):
            citation_id = citation.findall("./ArticleIdList/ArticleId[@IdType='pubmed']")
            if not len(citation_id):
                continue
            citation_list.add(int(citation_id[0].text))

        for citation in citation_list:
            citations_to_insert.append(dict(document_source_id=pmid, document_source_collection=document_collection,
                                            document_target_id=citation, document_target_collection=document_collection))
    return citations_to_insert, pmids_processed


def pubmed_medline_load_citations_from_dictionary(directory, document_collection='PubMed'):
    """
    Loads a whole folder containing PubMed Medline XML files into the database
    Extracts all relevant citations and inserts it
    Only loads citations for documents that have no citations in the db and that are available in the document table
    :param directory: PubMed Medline XML file directory
    :param document_collection: the document collection to insert
    :return: None
    """
    session = SessionRecommender.get()
    logging.info(f'Querying document ids for collection {document_collection}...')
    d_query = session.query(Document.id).filter(Document.collection == document_collection)
    document_ids = set([d[0] for d in d_query])
    logging.info(f'{len(document_ids)} retrieved')
    logging.info(f'Querying documents that have citation already...')
    d2_query = session.query(DocumentCitation.document_source_id) \
        .filter(DocumentCitation.document_source_collection == document_collection)
    document_id_processed = set([d[0] for d in d2_query])
    logging.info(f'{len(document_id_processed)} documents already have citation...')
    document_ids = document_ids - document_id_processed
    logging.info(f'{len(document_ids)} document ids remaining...')

    if directory[-1] == '/':
        directory = directory[:-1]
    files = glob.glob(f'{directory}/**/*.xml.gz', recursive=True) + glob.glob(f'{directory}/**/*.xml', recursive=True)
    start = datetime.now()
    for idx, fn in enumerate(files):
        print_progress_with_eta("Loading PubMed Medline citation", idx, len(files), start, 1)
        citations_to_insert, pmids_processed = pubmed_medline_load_document_citations(fn, document_ids,
                                                                                    document_collection)
        DocumentCitation.bulk_insert_values_into_table(session, citations_to_insert, check_constraints=False)
        document_ids = document_ids - pmids_processed


def main():
    parser = ArgumentParser()
    parser.add_argument("input", help="PubMed Medline Directory containing all xml files")
    parser.add_argument("-c", "--collection", required=True, help="Name of the document collection")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    logging.info(f'Loading PubMed Medline metadata from {args.input}...')
    pubmed_medline_load_citations_from_dictionary(args.input, document_collection=args.collection)


if __name__ == "__main__":
    # session = SessionRecommender.get()
    # query = session.query(DocumentCitation)
    # for q in query:
    #     print(f'document_source_id={q.document_source_id}, document_source_collection={q.document_source_collection}, '
    #           f'document_target_id={q.document_target_id}, document_target_collection={q.document_target_collection}')
    main()
