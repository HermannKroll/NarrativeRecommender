import json
import logging
import os.path

from narrec.benchmark.benchmark import Benchmark, BenchmarkType
from narrec.config import RELISH_BENCHMARK_JSON_FILE, RELISH_PMIDS_FILE, BENCHMKARK_QRELS_DIR


class RelishBenchmark(Benchmark):

    NAME = "RELISH"

    def __init__(self, name="RELISH"):
        self.documents_with_idx = []
        super().__init__(name=name, path_to_document_ids=RELISH_PMIDS_FILE, type=BenchmarkType.REC_BENCHMARK)

    def iterate_over_document_entries(self):
        for idx, doc_id in self.topic2relevant_docs:
            yield idx, doc_id

    def load_benchmark_data(self):
        # A relish data entry looks like this
        # {
        #     "uid": "5b02e9e1fdb55aa7f94c340b",
        #     "pmid": "29360039",
        #     "response": {
        #         "relevant": [
        #             "17901128", "18452557", "18455718", "18824165", "18832393",
        #             "18848538", "19074029", "19275872", "19426560", "19481073",
        #             "19652666", "19861495", "20215346", "20237281", "20308281",
        #             "20542628", "21223962", "21536023", "22659080", "22718906",
        #             "23097490", "23136387", "23161803", "23385791", "23493057",
        #             "24166500", "24284065", "25159185", "25446028", "25557916",
        #             "25947138", "26341559", "26375880", "26657765", "26719333",
        #             "27015931", "27633990", "27807028", "28483978", "28552735",
        #             "28969468", "29253534", "29355736", "29501879"
        #         ],
        #         "partial": [
        #             "18599349", "19737974", "21319228", "21879738", "22235335",
        #             "22569336", "23226572", "24165979", "25506591", "25621495",
        #             "28526413", "28558797", "29155277", "29581031", "29618525"
        #         ],
        #         "irrelevant": [
        #             "24521094"
        #         ]
        #     },
        #     "experience": "phd-post-gt10",
        #     "is_anonymous": true
        # },
        logging.info(f"Loading Relish benchmark data from {RELISH_BENCHMARK_JSON_FILE}")
        self.topic2relevant_docs.clear()
        self.topic2partially_relevant_docs.clear()
        self.topic2not_relevant_docs.clear()
        with open(RELISH_BENCHMARK_JSON_FILE, 'rt') as f:
            relish_data = json.load(f)

        count = 0
        rated_documents = set()
        for idx, rating in enumerate(relish_data):
            count += 1
            doc_id = int(rating["pmid"])
            key = idx, doc_id
            self.topics.append(doc_id)
            self.documents_with_idx.append((idx, doc_id))
            if key in self.topic2relevant_docs:
                logging.warning(f'Duplicated rating for PMID {key}')
            else:
                self.topic2relevant_docs[key] = set()
                self.topic2partially_relevant_docs[key] = set()
                self.topic2not_relevant_docs[key] = set()

            for doc_id in rating["response"]["relevant"]:
                self.topic2relevant_docs[key].add(int(doc_id))
                rated_documents.add(int(doc_id))
            for doc_id in rating["response"]["partial"]:
                self.topic2partially_relevant_docs[key].add(int(doc_id))
                rated_documents.add(int(doc_id))
            for doc_id in rating["response"]["irrelevant"]:
                self.topic2not_relevant_docs[key].add(int(doc_id))
                rated_documents.add(int(doc_id))

        logging.info(f'Benchmark has {count} rated document queries')
        logging.info(f'Benchmark has {len(rated_documents)} distinct and rated documents')
        logging.info('Relish data loaded')

    def get_qrel_path(self):
        path = os.path.join(BENCHMKARK_QRELS_DIR, f'{self.name}_qrels.txt')
        if not os.path.isfile(path):
            RelishBenchmark.process_json_to_txt(path)
        return path

    @staticmethod
    def process_json_to_txt(output_path: str):
        with open(RELISH_BENCHMARK_JSON_FILE, 'r') as json_file:
            data = json.load(json_file)

        output_lines = []

        for idx, entry in enumerate(data):
            doc_key = f'{idx}'
            relevant = set(entry["response"]["relevant"])
            partial = set(entry["response"]["partial"])
            irrelevant = set(entry["response"]["irrelevant"])

            assert len(relevant.intersection(partial)) == 0
            assert len(relevant.intersection(irrelevant)) == 0
            assert len(partial.intersection(irrelevant)) == 0

            # Process relevant entries
            output_lines.extend(f'{doc_key}\t0\t{rel_id}\t2' for rel_id in relevant)

            # Process partial entries
            output_lines.extend(f'{doc_key}\t0\t{part_id}\t1' for part_id in partial)

            # Process irrelevant entries
            output_lines.extend(f'{doc_key}\t0\t{irrel_id}\t0' for irrel_id in irrelevant)

        with open(output_path, 'w') as txt_file:
            txt_file.write('\n'.join(output_lines))

        logging.info(f'Document file created successfully.')


# for test purposes
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)
    benchmark = RelishBenchmark()
    logging.info(f'Benchmark has {len(benchmark.get_documents_for_baseline())} documents')
    print(benchmark.get_qrel_path())
