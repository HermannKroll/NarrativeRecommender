import os

from tqdm import tqdm

from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import BenchmarkType, Benchmark
from narrec.benchmark.relish import RelishBenchmark
from narrec.citation.graph import CitationGraph
from narrec.config import RESULT_DIR, INDEX_DIR, GLOBAL_DB_DOCUMENT_COLLECTION
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.recommender.simple import RecommenderSimple


def analyze_benchmark(retriever: DocumentRetriever, benchmark: Benchmark):
    print(f'Analyzing benchmark: {benchmark.name}')
    result_lines = []

    print('Retrieve document contents...')
    doc_ids = [d[1] for d in benchmark.iterate_over_document_entries()]
    input_docs = retriever.retrieve_narrative_documents(document_ids=doc_ids,
                                                        document_collection=benchmark.document_collection)
    docid2docs = {d.id: d for d in input_docs}

    print('Perform first stage retrieval')

    graph_size2count = {}
    count_less_5 = 0
    count_less_10 = 0
    doc_queries = list(benchmark.iterate_over_document_entries())
    for q_idx, doc_id in tqdm(doc_queries, total=len(doc_queries)):
        try:
            input_doc = docid2docs[int(doc_id)]

            doc_graph_size = len(input_doc.graph)

            if doc_graph_size not in graph_size2count:
                graph_size2count[doc_graph_size] = 0
            graph_size2count[doc_graph_size] += 1

            if doc_graph_size < 5:
                count_less_5 += 1

            if doc_graph_size < 10:
                count_less_10 += 1

        except KeyError:
            print(f'Document {doc_id} not known in our collection - skipping')

    graph_size2count = sorted([(k, v) for k, v in graph_size2count.items()], key=lambda x: x[0])
    for size, count in graph_size2count:
        print(f'graph of {size}: {count}')

    print()
    print('Less than 5 edges : ', count_less_5)
    print('Less than 10 edges: ', count_less_10)


def main():
    benchmarks = [RelishBenchmark()]
    corpus = DocumentCorpus(collections=[GLOBAL_DB_DOCUMENT_COLLECTION])
    core_extractor = NarrativeCoreExtractor(corpus=corpus)
    retriever = DocumentRetriever()
    citation_graph = CitationGraph()
    recommenders = [RecommenderSimple()]
    DO_RECOMMENDATION = False

    for bench in benchmarks:
        index_path = os.path.join(INDEX_DIR, bench.name)
        analyze_benchmark(retriever, bench)


if __name__ == '__main__':
    main()
