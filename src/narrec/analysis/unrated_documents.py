import os
from typing import List

import pytrec_eval

from narrec.config import RESULT_DIR
from narrec.run_config import BENCHMARKS, RECOMMENDER_NAMES, FIRST_STAGES

TOP_K = 20


def get_top_k_scored_documents(documents2score: dict, k: int) -> List[str]:
    doc_list = [(d, score) for d, score in documents2score.items()]
    doc_list.sort(key=lambda x: x[1], reverse=True)
    return [d[0] for d in doc_list[:k]]


def main():
    for benchmark in BENCHMARKS:
        benchmark.load_benchmark_data()

        documents_to_review = list()
        run2unrated_document_lists = dict()

        print(f'Loading qrel file: {benchmark.get_qrel_path()}')
        with open(benchmark.get_qrel_path(), 'r') as f_qrel:
            qrel = pytrec_eval.parse_qrel(f_qrel)

        results = list()
        for first_stage in FIRST_STAGES:
            run_path = os.path.join(RESULT_DIR, f'{benchmark.name}_{first_stage}.txt')
            if not os.path.isfile(run_path):
                print(f'Run file missing: {run_path}')
                continue

            print(f'Loading run file: {run_path}')
            with open(run_path, 'r') as f_run:
                run = pytrec_eval.parse_run(f_run)
            results.append([first_stage, run])

            for recommender in RECOMMENDER_NAMES:
                run_path = os.path.join(RESULT_DIR, f'{benchmark.name}_{first_stage}_{recommender}.txt')
                if os.path.isfile(run_path):
                    print(f'Loading run file: {run_path}')
                    with open(run_path, 'r') as f_run:
                        run = pytrec_eval.parse_run(f_run)
                    results.append([f'{first_stage}_{recommender}', run])
                else:
                    print(f'Run file missing: {run_path}')

        print('--' * 60)
        for run_name, run in results:
            for topic, _ in benchmark.iterate_over_document_entries():
                missing_documents = list()
                wrongly_retrieved = list()
                correctly_retrieved = list()
                for docid in get_top_k_scored_documents(run[topic], TOP_K):
                    if docid not in qrel[topic]:
                        missing_documents.append(docid)
                    elif docid in qrel[topic] and qrel[topic][docid] == 0:
                        wrongly_retrieved.append(docid)
                    elif docid in qrel[topic] and qrel[topic][docid] in [1, 2]:
                        correctly_retrieved.append(docid)

                if run_name not in run2unrated_document_lists:
                    run2unrated_document_lists[run_name] = list()

                run2unrated_document_lists[run_name].append(missing_documents)
                documents_to_review.extend([(d, topic) for d in missing_documents])
                #  print(f'Topic: {topic}')
                #  print(f'Retrieved number of documents: {len(run[topic])}')
                #  print(f'Retrieved unrated documents: {missing_documents}')
                #  print(f'Wrongly retrieved documents: {wrongly_retrieved}')
                #  print(f'Correctly retrieved documents: {correctly_retrieved}')

        print('--' * 60)

        print('--' * 60)
        print(f'Benchmark name: {benchmark.name}')
        print('--' * 60)
        print()

        print(f'{len(documents_to_review)} documents to review:')
        for run_name, unrated_doc_lists in run2unrated_document_lists.items():
            avg = sum(len(l) for l in unrated_doc_lists) / len(unrated_doc_lists)
            print(f'{run_name}: avg no of unrated documents:  {round(avg, 2)}')


if __name__ == "__main__":
    main()
