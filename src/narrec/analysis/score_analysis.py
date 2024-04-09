import os
import json
from tabulate import tabulate

from narrec.config import SCORE_FREQUENCY

MIN_SCORE = 0.0
MAX_SCORE = 1.0

FIRST_STAGES = [
    "Perfect",
    "BM25Abstract",
    "FSCore",
    "FSConcept",
    # "FSCoreOverlap",
    "PubMedRecommender"
]

RECOMMENDER_NAMES = [
    # "EqualRecommender",
    # "StatementOverlap",
    "JaccardCombinedWeighted",
    # "JaccardGraphWeighted",
    # "JaccardConceptWeighted",
    "AlignedNodesRecommender",
    "AlignedCoresRecommender",
    "AlignedNodesFallbackRecommender",
    "AlignedCoresFallbackRecommender"
]

BENCHMARKS = [
    "PM2020",
    # "Genomics2005",
    "RELISH",
    # "RELISH_DRUG"
]

RESULT_MEASURES = [
    # 'num_ret',
    'recall_1000',
    # 'ndcg_cut_10',
    'ndcg_cut_20',
    # 'ndcg_cut_100',
    # 'P_10',
    'P_20',
    # 'P_100'
]


def calculate_scores(data):
    total_sum = sum(data.values())
    limited_sum = 0
    count_within_range = 0
    for score, count in data.items():
        score_float = float(score)
        if MIN_SCORE <= score_float <= MAX_SCORE:
            limited_sum += score_float * count
            count_within_range += count
    percentage = (count_within_range / total_sum) * 100
    limited_average = limited_sum / count_within_range if count_within_range > 0 else 0
    return count_within_range, total_sum, percentage, limited_average


def compare_results():
    results_table = []
    for bm in BENCHMARKS:
        for rm in RESULT_MEASURES:
            table = []
            header = ["Method", f"Scores ({MIN_SCORE}-{MAX_SCORE})", "Percentage",
                      f"Average Score ({MIN_SCORE}-{MAX_SCORE})"]
            covered_first_stages = []
            for fs in FIRST_STAGES:
                for rn in RECOMMENDER_NAMES:
                    file_path = os.path.join(SCORE_FREQUENCY, f"{bm}_score_frequency.json")
                    with open(file_path, 'r') as file:
                        try:
                            data = json.load(file)
                            if fs not in covered_first_stages:
                                covered_first_stages.append(fs)
                                first_stage_values = data[fs][rm]
                                fs_limited_sum, fs_total_sum, fs_percentage, fs_average = calculate_scores(
                                    first_stage_values)
                                table.append([fs, f"{fs_limited_sum}/{fs_total_sum}", "{:.2f}%".format(fs_percentage),
                                              "{:.2f}".format(fs_average)])
                            score_values = data[f"{fs}_{rn}"][rm]
                            limited_sum, total_sum, percentage, average = calculate_scores(score_values)
                            method_name = f"{fs}_{rn}"
                            table.append(
                                [method_name, f"{limited_sum}/{total_sum}", "{:.2f}%".format(percentage),
                                 "{:.2f}".format(average)])
                        except Exception as e:
                            print("Error at calculating scores: ", e)
            results_table.append((bm, rm, header, table))

    return results_table


def main():
    result_tables = compare_results()
    for bm, rm, header, table in result_tables:
        print()
        print(f"Benchmark: {bm}, Measure: {rm}")
        print(tabulate(table, headers=header, tablefmt="pretty"))
        print()


if __name__ == "__main__":
    main()
