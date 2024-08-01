import os
from typing import Set

import pytrec_eval

from narrec.benchmark.benchmark import Benchmark
from narrec.config import RESULT_DIR
from narrec.run_config import BENCHMARKS


def jaccard(document_ids_a: Set[int], document_ids_b: Set[int]) -> float:
    return len(document_ids_a.intersection(document_ids_b)) / len(document_ids_a.union(document_ids_b))

def retrieve_top_k_documents(doc2score, k: int):
    docs_with_score = sorted([(k, v) for k, v in doc2score.items()], key=lambda item: item[1], reverse=True)[:k]
    # return just the documents
    return set([x[0] for x in docs_with_score])

def eval_jaccard_for_benchmark(benchmark: Benchmark):
    p_xgrec = os.path.join(RESULT_DIR, f'{benchmark.name}_FSConceptFlex_CoreOverlap_BM25Fallback.txt')
    p_pubmed = os.path.join(RESULT_DIR, f'{benchmark.name}_PubMedRecommender.txt')
    p_bm25 = os.path.join(RESULT_DIR, f'{benchmark.name}_BM25Abstract.txt')

    print(f'Loading run file: {p_xgrec}')
    with open(p_xgrec, 'r') as f_run:
        run_xgrec = pytrec_eval.parse_run(f_run)

    print(f'Loading run file: {p_pubmed}')
    with open(p_pubmed, 'r') as f_run:
        run_pubmed = pytrec_eval.parse_run(f_run)

    print(f'Loading run file: {p_bm25}')
    with open(p_bm25, 'r') as f_run:
        run_bm25 = pytrec_eval.parse_run(f_run)

    print(f'Loading qrel file: {benchmark.get_qrel_path()}')
    with open(benchmark.get_qrel_path(), 'r') as f_qrel:
        qrel = pytrec_eval.parse_qrel(f_qrel)

    relevant_topics = {q for q in qrel}

    k_values_to_report = [5, 10, 20, 100]

    jaccards_xgrec_pubmed = {k : [] for k in k_values_to_report}
    jaccards_xgrec_bm25 = {k : [] for k in k_values_to_report}
    for topic in relevant_topics:
        for k in k_values_to_report:
            xgrec_docs = retrieve_top_k_documents(run_xgrec[topic], k)
            pubmed_docs = retrieve_top_k_documents(run_pubmed[topic], k)
            bm25_docs = retrieve_top_k_documents(run_bm25[topic], k)

            if len(xgrec_docs) > 0:
                if len(pubmed_docs) > 0:
                    jaccards_xgrec_pubmed[k].append(jaccard(xgrec_docs, pubmed_docs))
                else:
                    jaccards_xgrec_pubmed[k].append(0.0)

                if len(bm25_docs) > 0:
                    jaccards_xgrec_bm25[k].append(jaccard(xgrec_docs, bm25_docs))
                else:
                    jaccards_xgrec_bm25[k].append(0.0)
            else:
                jaccards_xgrec_pubmed[k].append(0.0)
                jaccards_xgrec_bm25[k].append(0.0)
    print('Averaging jaccard scores...')
    # compute the average
    jaccards_xgrec_pubmed_avg = dict()
    jaccards_xgrec_bm25_avg = dict()
    for k in k_values_to_report:
        jaccards_xgrec_pubmed_avg[k] = sum(jaccards_xgrec_pubmed[k]) / len(jaccards_xgrec_pubmed[k])
        jaccards_xgrec_bm25_avg[k] = sum(jaccards_xgrec_bm25[k]) / len(jaccards_xgrec_bm25[k])

    print('XGRec vs. PubMed:  ' + ' & '.join([str(round(jaccards_xgrec_pubmed_avg[k], 2)) for k in k_values_to_report]))
    print('XGRec vs. BM25:  ' + ' & '.join([str(round(jaccards_xgrec_bm25_avg[k], 2)) for k in k_values_to_report]))

def main():
    for benchmark in BENCHMARKS:
        benchmark.load_benchmark_data()
        eval_jaccard_for_benchmark(benchmark)


if __name__ == '__main__':
    main()
