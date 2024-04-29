import json
import os
from datetime import datetime

import numpy

from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import Benchmark
from narrec.config import RESULT_DIR, INDEX_DIR, GLOBAL_DB_DOCUMENT_COLLECTION, RUNTIME_MEASUREMENT_RESULT_DIR
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.firststage.bm25abstract import BM25Abstract
from narrec.firststage.bm25title import BM25Title
from narrec.firststage.fsconcept import FSConcept
from narrec.firststage.fsconceptflex import FSConceptFlex
from narrec.firststage.fscore import FSCore
from narrec.firststage.fscoreflex import FSCoreFlex
from narrec.firststage.fsnode import FSNode
from narrec.firststage.fsnodeflex import FSNodeFlex
from narrec.run import run_first_stage_for_benchmark
from narrec.run_config import BENCHMARKS, LOAD_FULL_IDF_CACHE, NO_PERFORMANCE_MEASUREMENTS


def perform_benchmark_first_stage_runtime_measurement(bench: Benchmark):
    corpus = DocumentCorpus(collections=[GLOBAL_DB_DOCUMENT_COLLECTION])
    if LOAD_FULL_IDF_CACHE:
        corpus.load_all_support_into_memory()

    index_path = os.path.join(INDEX_DIR, bench.get_index_name())
    core_extractor = NarrativeCoreExtractor(corpus=corpus)
    retriever = DocumentRetriever()
    bench.load_benchmark_data()

    first_stages = [FSConceptFlex(core_extractor, bench),
                    FSCoreFlex(core_extractor, bench),
                    FSNodeFlex(core_extractor, bench),
                    FSConcept(core_extractor, bench),
                    FSCore(core_extractor, bench),
                    FSNode(core_extractor, bench),
                    BM25Abstract(index_path),
                    BM25Title(index_path)]
    print('==' * 60)
    print(f'Measuring runtime on benchmark: {bench.name}')
    print('==' * 60)
    print('Perform first stage runtime measurement...')
    for first_stage in first_stages:
        path = os.path.join(RUNTIME_MEASUREMENT_RESULT_DIR, f'{bench.name}_{first_stage.name}.json')
        if os.path.isfile(path):
            print(f'Runtimes exists - skipping: {path}')
            continue

        print(f'Measuring runtime for first stage: {first_stage.name}')
        fs_path = os.path.join(RESULT_DIR, f'performance_{bench.name}_{first_stage.name}.txt')
        result_dict = dict()
        times = []
        for i in range(0, NO_PERFORMANCE_MEASUREMENTS):
            time_start = datetime.now()
            run_first_stage_for_benchmark(retriever, bench, first_stage, fs_path, write_results=False, verbose=False,
                                          progress=True)
            time_taken = datetime.now() - time_start

            result_dict[f'run_{i}'] = str(time_taken)
            result_dict[f'seconds_run_{i}'] = time_taken.total_seconds()
            # first run is cold start
            if i > 0:
                times.append(time_taken.total_seconds())

            print(f'Elapsed time: {str(time_taken)}')

        # first run is cold start
        result_dict["mean"] = sum(times) / len(times)
        result_dict["std"] = numpy.std(times)

        print(f'Writing runtime measurement results to: {path}')
        with open(path, 'wt') as f:
            json.dump(result_dict, f, indent=4)


def main():
    for bench in BENCHMARKS:
        perform_benchmark_first_stage_runtime_measurement(bench)


if __name__ == '__main__':
    main()
