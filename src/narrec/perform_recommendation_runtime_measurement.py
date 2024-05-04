import json
import os
from datetime import datetime

import numpy
from tqdm import tqdm

from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import Benchmark
from narrec.citation.graph import CitationGraph
from narrec.config import RESULT_DIR, INDEX_DIR, GLOBAL_DB_DOCUMENT_COLLECTION, \
    RUNTIME_MEASUREMENT_RECOMMENDATION_RESULT_DIR
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.firststage.fsconceptflex import FSConceptFlex
from narrec.recommender.bm25 import BM25Recommender
from narrec.recommender.coreoverlap import CoreOverlap
from narrec.recommender.graph_base_fallback_bm25 import GraphBaseFallbackBM25
from narrec.run import load_document_ids_from_runfile
from narrec.run_config import BENCHMARKS, LOAD_FULL_IDF_CACHE, NO_PERFORMANCE_MEASUREMENTS
from narrec.scoring.BM25Scorer import BM25Scorer


def perform_benchmark_first_stage_runtime_measurement(bench: Benchmark):
    citation_graph = CitationGraph()
    corpus = DocumentCorpus(collections=[GLOBAL_DB_DOCUMENT_COLLECTION])
    if LOAD_FULL_IDF_CACHE:
        corpus.load_all_support_into_memory()

    index_path = os.path.join(INDEX_DIR, bench.get_index_name())
    core_extractor = NarrativeCoreExtractor(corpus=corpus)
    retriever = DocumentRetriever()
    bench.load_benchmark_data()

    first_stage = FSConceptFlex(extractor=core_extractor, benchmark=bench)

    recommender_coreoverlap = CoreOverlap(extractor=core_extractor)

    bm25_scorer = BM25Scorer(index_path)
    recommenders = [recommender_coreoverlap,
                    GraphBaseFallbackBM25(bm25scorer=bm25_scorer, graph_recommender=recommender_coreoverlap),
                    BM25Recommender(bm25scorer=bm25_scorer)]

    print('==' * 60)
    print(f'Measuring runtime on benchmark: {bench.name}')
    print('==' * 60)
    print('Perform first stage runtime measurement...')
    path = os.path.join(RUNTIME_MEASUREMENT_RECOMMENDATION_RESULT_DIR, f'{bench.name}_recommendation.json')
    if os.path.isfile(path):
        print(f'Runtimes exists - skipping: {path}')
        return

    print(f'Measuring runtime for first stage: {first_stage.name}')

    fs_path = os.path.join(RESULT_DIR, f'{bench.name}_{first_stage.name}.txt')
    # next load the documents for this first stage
    print(f'Loading first stage runfile: {fs_path}')
    fs_docs = load_document_ids_from_runfile(fs_path)
    # get the input ids for each doc
    topic2doc = {str(top): doc for top, doc in bench.iterate_over_document_entries()}

    recommender2times = dict()
    for r in recommenders:
        recommender2times[r.name] = list()

    for topicid, retrieved_docs in tqdm(fs_docs.items(), desc="Evaluating topics"):
        # Retrieve the input document
        input_doc = retriever.retrieve_narrative_documents([topic2doc[topicid]],
                                                           GLOBAL_DB_DOCUMENT_COLLECTION)[0]

        # Retrieve the documents to score
        retrieved_doc_ids = [d[0] for d in retrieved_docs]
        documents = retriever.retrieve_narrative_documents(retrieved_doc_ids,
                                                           GLOBAL_DB_DOCUMENT_COLLECTION)
        for recommender in recommenders:

            times = []
            for i in range(0, NO_PERFORMANCE_MEASUREMENTS):
                time_start = datetime.now()
                rec_docs = recommender.recommend_documents(input_doc, documents, citation_graph)
                time_taken = datetime.now() - time_start

                # first run is cold start
                if i > 0:
                    times.append(time_taken.total_seconds())

            # first run is cold start -
            recommender2times[recommender.name].append((sum(times) / len(times)))

    result_dict = dict()
    for recommender in recommenders:
        times = recommender2times[recommender.name]
        result_dict[recommender.name] = {
            "mean": sum(times) / len(times),
            "std": numpy.std(times)
        }

    print(f'Writing runtime measurement results to: {path}')
    with open(path, 'wt') as f:
        json.dump(result_dict, f, indent=4)


def main():
    for bench in BENCHMARKS:
        perform_benchmark_first_stage_runtime_measurement(bench)


if __name__ == '__main__':
    main()
