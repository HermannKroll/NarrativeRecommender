METRICS = [
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


def perform_evaluation_report(qrel_file: str, run_file: str, output: str):
    """
    Applys pytrec_eval to our given scenario
    Computes the previously defined metrics
    :param qrel_file: gold run file (given by benchmark)
    :param run_file: our actual produced run file by some method
    :param output: write report results as a JSON to this path
    :return: None
    """
    pass
