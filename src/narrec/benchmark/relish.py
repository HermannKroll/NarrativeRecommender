import gzip
import json
import logging

from narrec.benchmark.benchmark import Benchmark
from narrec.config import RELISH_BENCHMARK_FILE


class RelishBenchmark(Benchmark):

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
        with gzip.open(RELISH_BENCHMARK_FILE, 'rt') as f:
            relish_data = json.load(f)

        for rating in relish_data:
            pmid = int(rating["pmid"])
            if pmid in self.doc2recommended:
                logging.warning(f'Duplicated rating for PMID {pmid}')
            else:
                self.doc2recommended[pmid] = set()
                self.doc2not_recommended[pmid] = set()

            for doc_id in rating["response"]["relevant"]:
                self.doc2recommended[pmid].add(int(doc_id))

            # Todo: how should we treat partially relevant documents?
            for doc_id in rating["response"]["partial"]:
                self.doc2recommended[pmid].add(int(doc_id))

            for doc_id in rating["response"]["irrelevant"]:
                self.doc2not_recommended[pmid].add(int(doc_id))

        logging.info('Relish data loaded')


# for test purposes
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)
    benchmark = RelishBenchmark()
    benchmark.load_benchmark_data()
