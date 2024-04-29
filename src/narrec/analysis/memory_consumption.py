import sys

from tqdm import tqdm

from narraint.backend.database import SessionExtended
from narraint.backend.models import TagInvertedIndex


def main():
    session = SessionExtended.get()
    cache_concept2support = dict()
    print("Empty dict", sys.getsizeof(cache_concept2support), "bytes")
    total = session.query(TagInvertedIndex).count()
    q = session.query(TagInvertedIndex.entity_id,
                      TagInvertedIndex.document_collection,
                      TagInvertedIndex.support)
    for row in tqdm(q, desc="Loading db data...", total=total):
        if row.document_collection == "PubMed":
            if row.entity_id in cache_concept2support:
                cache_concept2support[row.entity_id] += row.support
            else:
                cache_concept2support[row.entity_id] = row.support
    print("Number of entries", len(cache_concept2support))
    size = sys.getsizeof(cache_concept2support)
    print("Final dict", size, "bytes")
    print("MB (rounded, 2)", round(size / 1024 / 1024, 2))
    print("Number of entries", len(cache_concept2support.keys()))


if __name__ == '__main__':
    main()
