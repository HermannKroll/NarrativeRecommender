from sqlalchemy import func

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document

PMIDS_PATH = 'pm2020_docs.txt'
PMIDS_PER_LIST = 100000


def get_pmids():
    print(f"Reading file {PMIDS_PATH}...")
    with open(PMIDS_PATH) as file:
        pmids = [int(x.removesuffix('\n')) for x in file.readlines() if x != '\n']
        print(f"{len(pmids)} pmids found in {PMIDS_PATH}")
        return [pmids[x:x + PMIDS_PER_LIST] for x in range(0, len(pmids), PMIDS_PER_LIST)]


def main():
    doc_pmids = get_pmids()

    s = Session.get()
    print(f"Quering for documents...")

    total_pmids = 0
    total_pmids_stored = 0

    for pmids in doc_pmids:
        q = s.query(Document.id).filter(Document.id.in_(pmids)).filter(Document.collection == 'PubMed').count()
        total_pmids += len(pmids)
        total_pmids_stored += q
        print(total_pmids, total_pmids_stored)
    s.remove()
    print(f"{total_pmids_stored} of {total_pmids} PM2020 (2019) documents stored in our db")


if __name__ == "__main__":
    main()
