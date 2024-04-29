import json
import os

from narrec.config import RUNTIME_MEASUREMENT_RESULT_DIR
from narrec.run_config import BENCHMARKS

FIRST_STAGE_NAMES = [
    "BM25Title",
    "BM25Abstract",
    "FSConcept",
    "FSConceptFlex",
    "FSNode",
    "FSNodeFlex",
    "FSCore",
    "FSCoreFlex"
]


def analyse_times():
    rows = []
    rows.append('Benchmark\tFirst Stage\tTime 0\tTime 1\tTime 2\tTime3\t'
                'Time Avg.\tTime Std.\tBenchmark Docs\tTime per Doc\tTime per Doc Std')

    rows_to_print = []
    for benchmark in BENCHMARKS:
        benchmark.load_benchmark_data()
        for fs_name in FIRST_STAGE_NAMES:
            path = os.path.join(RUNTIME_MEASUREMENT_RESULT_DIR, f'{benchmark.name}_{fs_name}.json')
            if not os.path.isfile(path):
                print(f'Runtime file missing: {path}')
                continue

            print(f'reading runtime measurement results to: {path}')
            with open(path, 'rt') as f:
                data = json.load(f)

            no_documents = len(list(benchmark.iterate_over_document_entries()))

            seconds_per_doc = float(data["mean"]) / no_documents
            seconds_per_doc_std = float(data["std"]) / no_documents

            data_row = [benchmark.name, fs_name,
                        data["seconds_run_0"], data["seconds_run_1"], data["seconds_run_2"], data["seconds_run_3"],
                        data["mean"], data["std"],
                        no_documents, seconds_per_doc, seconds_per_doc_std]

            rows_to_print.append(f'{benchmark.name} & {fs_name} & {round(seconds_per_doc, 1)}s')

            rows.append('\t'.join([str(r) for r in data_row]))

    result_path = os.path.join(RUNTIME_MEASUREMENT_RESULT_DIR, "runtime_report.csv")
    print(f'Writing results to {result_path}')
    with open(result_path, 'wt') as f:
        f.write('\n'.join([r for r in rows]))

    print(f'Short report:')
    print('\n'.join([r for r in rows_to_print]))

def main():
    analyse_times()


if __name__ == "__main__":
    main()
