import pytrec_eval
import json


METRICS_OLD = [
    "recall@1000",
    "ndcg@10",
    "ndcg@20",
    "ndcg@100",
    "bpref",
    "map@1000",
    "precision@10",
    "precision@20",
    "precision@100"
]

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


def perform_evaluation_report(qrel_file: str, run_file: str, output: str):
    """
    Applys pytrec_eval to our given scenario
    Computes the previously defined metrics
    :param qrel_file: gold run file (given by benchmark)
    :param run_file: our actual produced run file by some method
    :param output: write report results as a JSON to this path
    :return: None
    """
    #print(pytrec_eval.supported_measures)
    with open(qrel_file, 'r') as f_qrel:
        qrel = pytrec_eval.parse_qrel(f_qrel)

    with open(run_file, 'r') as f_run:
        run = pytrec_eval.parse_run(f_run)

    evaluator = pytrec_eval.RelevanceEvaluator(qrel, METRICS)
    results = evaluator.evaluate(run)

    with open(output, 'w') as f_out:
        json.dump(results, f_out, indent=4)