import pytrec_eval
import json
import os
import pandas as pd
import matplotlib.pyplot as plt


METRICS = {
    'recall_1000',
    'ndcg_cut_10',
    'ndcg_cut_20',
    'ndcg_cut_100',
    'bpref',
    'map_cut_1000',
    'P_10',
    'P_20',
    'P_100'
}


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


def perform_evaluation_report(qrel_file: str, run_file: str, output: str):
    """
    Applys pytrec_eval to our given scenario
    Computes the previously defined metrics
    :param qrel_file: gold run file (given by benchmark)
    :param run_file: our actual produced run file by some method
    :param output: write report results as a JSON to this path
    :return: None
    """
    print(f'Loading qrel file: {qrel_file}')
    with open(qrel_file, 'r') as f_qrel:
        qrel = pytrec_eval.parse_qrel(f_qrel)

    print(f'Loading run file: {run_file}')
    with open(run_file, 'r') as f_run:
        run = pytrec_eval.parse_run(f_run)

    evaluator = pytrec_eval.RelevanceEvaluator(qrel, METRICS)
    results = evaluator.evaluate(run)

    print(results)

   # with open(output, 'w') as f_out:
   #     json.dump(results, f_out, indent=4)

   # generate_diagram(output, os.path.dirname(output))

def main():
    perform_evaluation_report("/home/kroll/NarrativeRecommender/resources/benchmarks/RELISH_documents.txt",
                              "/ssd2/kroll/recommender/results/BM25Title.txt", None)



if __name__ == '__main__':
    main()