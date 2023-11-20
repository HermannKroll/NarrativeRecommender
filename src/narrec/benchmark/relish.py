import json
import logging

from narrec.benchmark.benchmark import Benchmark, BenchmarkMode
from narrec.config import RELISH_BENCHMARK_FILE
from narrec.recommender.base import RecommenderBase


class RelishBenchmark(Benchmark):

    def __init__(self):
        super().__init__()
        self.doc2recommended = {}
        self.doc2partial_recommended = {}
        self.doc2not_recommended = {}
        self.documents_with_idx = []
        self.load_benchmark_data()

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
        logging.info(f"Loading Relish benchmark data from {RELISH_BENCHMARK_FILE}")
        self.doc2recommended.clear()
        self.doc2not_recommended.clear()
        with open(RELISH_BENCHMARK_FILE, 'rt') as f:
            relish_data = json.load(f)

        for idx, rating in enumerate(relish_data):
            doc_id = int(rating["pmid"])
            key = idx, doc_id
            self.documents_with_idx.append((idx, doc_id))
            if key in self.doc2recommended:
                logging.warning(f'Duplicated rating for PMID {key}')
            else:
                self.doc2recommended[key] = set()
                self.doc2partial_recommended[key] = set()
                self.doc2not_recommended[key] = set()

            for doc_id in rating["response"]["relevant"]:
                self.doc2recommended[key].add(int(doc_id))
            for doc_id in rating["response"]["partial"]:
                self.doc2partial_recommended[key].add(int(doc_id))
            for doc_id in rating["response"]["irrelevant"]:
                self.doc2not_recommended[key].add(int(doc_id))

        logging.info('Relish data loaded')

    def get_evaluation_data_for_topic(self, idx: int, docid: int, mode: BenchmarkMode):
        key = (idx, docid)
        if mode == BenchmarkMode.RELEVANT_VS_IRRELEVANT:
            return self.doc2recommended[key], self.doc2not_recommended[key]
        elif mode == BenchmarkMode.RELEVANT_PARTIAL_VS_IRRELEVANT:
            relevant = set()
            relevant.update(self.doc2recommended[key])
            relevant.update(self.doc2partial_recommended[key])
            return relevant, self.doc2not_recommended[key]
        elif mode == BenchmarkMode.RELEVANT_VS_PARTIAL_IRRELEVANT:
            irrelevant = set()
            irrelevant.update(self.doc2partial_recommended[key])
            irrelevant.update(self.doc2not_recommended[key])
            return self.doc2recommended[key], irrelevant
        else:
            raise ValueError(f'Enum value {mode} unknown and not supported')

    def perform_evaluation(self, recommender: RecommenderBase, mode: BenchmarkMode):
        for idx, docid in self.documents_with_idx:
            relevant, irrelevant = self.get_evaluation_data_for_topic(idx, docid, mode)


# for test purposes
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)
    benchmark = RelishBenchmark()
    benchmark.load_benchmark_data()
