import json
import os
from collections import defaultdict
from typing import List

import matplotlib.pyplot as plt
import numpy
import pandas as pd
import pytrec_eval

from narrec.benchmark.benchmark import Benchmark, BenchmarkType, IRBenchmark
from narrec.config import RESULT_DIR, TOPIC_SCORES, SCORE_FREQUENCY
from narrec.run_config import BENCHMARKS, FIRST_STAGES, RECOMMENDER_NAMES

METRICS = {
    'recall_1000',
    'ndcg_cut_10',
    'ndcg_cut_20',
    'ndcg_cut_100',
    'bpref',
    'map_cut_1000',
    'P_10',
    'P_20',
    'P_100',
    'num_ret',
    'set_recall'
}

RESULT_MEASURES = {
 #   'num_ret': 'Retrieved',
    'set_recall': 'Recall',
 #   'recall_1000': 'Recall@1000',
    'ndcg_cut_10': 'nDCG@10',
    'ndcg_cut_20': 'nDCG@20',
 #   'ndcg_cut_100': 'nDCG@100',
    #   'map': 'MAP',
    #   'bpref': 'bpref',
    'P_10': 'P@10',
    'P_20': 'P@20',
    "bpref" : "bpref"
  #  "P_100": 'P@100'
}


def extract_run(run: dict, measure: str):
    run = sorted(run.items(), key=lambda x: str(x[0]))
    indices = [k for k, _ in run]
    values = [(v[measure],) for _, v in run]

    return {i: v[0] for i, v in zip(indices, values)}


def calculate_table_data(measures: List[tuple], results: List, relevant_topics: set):
    # calculate the mean scores of the given measures for each ranker
    max_m = {m[0]: 0.0 for m in measures}
    score_rows = defaultdict(dict)
    score_frequency = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for name, raw_run in results:
        s_row = dict()
        for measure, _ in measures:
            run = extract_run(raw_run, measure)
            # add missing scores
            for q in relevant_topics.difference(set(run.keys())):
                run.update({q: 0.0})
            for score in run.values():
                score_frequency[name][measure][round(score, 2)] += 1
            score = round(sum(run.values()) / len(run.keys()), 2)
            max_m[measure] = max(max_m[measure], score)
            s_row[measure] = score
        score_rows[name] = s_row
    return score_rows, max_m, score_frequency


def calculate_table_data_ir_benchmark(measures: List[tuple], results: List, relevant_topics: set):
    # an IR benchmark consists of each input queries X
    # each query X has Y documents rated
    # we used each document of Y as an input to our overall pipeline
    # we want to first average over the scores of a topic and then
    # calculate the mean scores of the given measures per topic
    max_m = {m[0]: 0.0 for m in measures}
    score_rows = defaultdict(dict)
    topic_scores = defaultdict(lambda: defaultdict(dict))
    score_frequency = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for name, raw_run in results:
        s_row = dict()
        for measure, _ in measures:
            run = extract_run(raw_run, measure)
            # add missing scores
            for q in relevant_topics.difference(set(run.keys())):
                run.update({q: 0.0})

            # collect the scores over all input document ids for a topic
            topic2score = dict()
            for r, s in run.items():
                r_q_id = IRBenchmark.get_query_id_from_doc_query_key(r)
                if r_q_id not in topic2score:
                    topic2score[r_q_id] = []
                topic2score[r_q_id].append(s)

            for t, scores in topic2score.items():
                mean = sum(scores) / len(scores)
                std_dev = numpy.std(scores)

                for score in scores:
                    score_frequency[name][measure][round(score, 2)] += 1

                topic_scores[name][measure][t] = {
                    'scores': scores,
                    'std': std_dev
                }
                #print(f'{name}\t{measure}\t{t}\t: {round(mean, 2)} +/- {round(std_dev, 2)} (no. of docs: {len(scores)})')


            # average the scores per topic
            topic2score = {t: sum(scores) / len(scores) for t, scores in topic2score.items()}
            # then average over all topics
            score = round(sum(topic2score.values()) / len(topic2score.keys()), 2)
            max_m[measure] = max(max_m[measure], score)
            s_row[measure] = score
        score_rows[name] = s_row
    return score_rows, max_m, topic_scores, score_frequency


def generate_diagram(input_json: str, output_dir: str):
    with open(input_json, 'r') as file:
        results = json.load(file)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for metric in METRICS:
        data = {run_name: res[metric] for run_name, res in results.items() if metric in res}
        df = pd.DataFrame(data)
        plt.figure()
        df.plot.bar(xlabel='Topic', ylabel=metric, figsize=(40, 10), width=1.0, edgecolor='black')
        plt.savefig(os.path.join(output_dir, f"{metric}.svg"), format="svg")
        plt.close('all')


def perform_evaluation_for_run(qrel, run_file: str):
    """
    Applys pytrec_eval to our given scenario
    Computes the previously defined metrics
    :param qrel: gold run file (given by benchmark)
    :param run_file: our actual produced run file by some method
    :return: None
    """
    print(f'Loading run file: {run_file}')
    with open(run_file, 'r') as f_run:
        run = pytrec_eval.parse_run(f_run)

    evaluator = pytrec_eval.RelevanceEvaluator(qrel, METRICS)
    return evaluator.evaluate(run)


def perform_evaluation(benchmark: Benchmark):
    print(f'Loading qrel file: {benchmark.get_qrel_path()}')
    with open(benchmark.get_qrel_path(), 'r') as f_qrel:
        qrel = pytrec_eval.parse_qrel(f_qrel)

    relevant_topics = {q for q in qrel}
    print(f'{len(relevant_topics)} relevant topics identified')

    results = list()
    for run_name in FIRST_STAGES:
        run_path = os.path.join(RESULT_DIR, f'{benchmark.name}_{run_name}.txt')
        if not os.path.isfile(run_path):
            print(f'Run file missing: {run_path}')
            continue
        results.append([run_name, perform_evaluation_for_run(qrel, run_path)])

        for recommender in RECOMMENDER_NAMES:
            run_path = os.path.join(RESULT_DIR, f'{benchmark.name}_{run_name}_{recommender}.txt')
            if os.path.isfile(run_path):
                results.append([f'{run_name}_{recommender}', perform_evaluation_for_run(qrel, run_path)])
            else:
                print(f'Run file missing: {run_path}')

    measures = [(k, v) for k, v in RESULT_MEASURES.items()]
    if benchmark.type == BenchmarkType.REC_BENCHMARK:
        score_rows, max_m, score_frequency = calculate_table_data(measures, results, relevant_topics)
    else:
        score_rows, max_m, topic_scores, score_frequency = calculate_table_data_ir_benchmark(measures, results, relevant_topics)
        with open(os.path.join(TOPIC_SCORES, f'{benchmark.name}_topic_scores.json'), 'w') as json_file:
            json.dump(topic_scores, json_file, indent=4)

    with open(os.path.join(SCORE_FREQUENCY, f'{benchmark.name}_score_frequency.json'), 'w') as json_file:
        json.dump(score_frequency, json_file, indent=4)
    print("--" * 60)
    print("Creating table content")
    print("--" * 60)
    # create tabular LaTeX code
    rows = []
    rows.append("% begin autogenerated")
    rows.append("\\toprule")
    rows.append(" & ".join(["Method", *(str(m[1]) for m in measures)]) + " \\\\")

    for name, scores in score_rows.items():
        row = f"{name.replace('FirstStage', '').split('-')[0].replace('_', ' ')} & "
        row += " & ".join(
            f"\\textbf{{{str(s)}}}" if max_m[m] == s else str(s) for m, s in scores.items())
        row += " \\\\"
        rows.append(row)

    rows.append("\\bottomrule")
    rows.append("% end autogenerated")

    print("\n".join(rows))
    print("--" * 60)

    print('\n\n\n')



def main():
    for benchmark in BENCHMARKS:
        benchmark.load_benchmark_data()
        perform_evaluation(benchmark)

if __name__ == '__main__':
    main()
