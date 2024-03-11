import logging

from narrec.benchmark.benchmark import IRBenchmark
from narrec.config import TG2005_PMIDS_FILE, TG2005_TOPIC_FILE, TG2005_BENCHMARK_FILE


class TrecGen2005Topic:

    def __init__(self, number, task):
        self.query_id = int(number)
        self.task = task

    def __str__(self):
        return f'<{self.query_id} task={self.task}>'

    def __repr__(self):
        return str(self)

    @staticmethod
    def parse_topics(path_to_file=TG2005_TOPIC_FILE):
        with open(path_to_file) as file:
            topics = []
            for line in file:
                number, task = line.lstrip('<').split('>', 1)
                topics.append(TrecGen2005Topic(number, task.strip()))
        return topics


class Genomics2005(IRBenchmark):

    def __init__(self):
        self.topics: [TrecGen2005Topic] = []
        super().__init__(name="Genomics2005", path_to_document_ids=TG2005_PMIDS_FILE)

    def load_benchmark_data(self):
        logging.info(f'Loading Benchmark data from {TG2005_BENCHMARK_FILE}...')
        eval_topics = set()
        rated_documents = set()
        with open(TG2005_BENCHMARK_FILE, 'rt') as f:
            for line in f:
                q_id, _, pmid, rating = line.split()
                q_id = int(q_id)
                pmid = int(pmid)
                rating = int(rating)
                eval_topics.add(q_id)
                # First add sets
                if q_id not in self.topic2relevant_docs:
                    self.topic2relevant_docs[q_id] = set()
                    self.topic2partially_relevant_docs[q_id] = set()
                    self.topic2not_relevant_docs[q_id] = set()
                # add based on rating
                if rating == 2:
                    # relevant
                    self.topic2relevant_docs[q_id].add(pmid)
                    rated_documents.add(pmid)
                elif rating == 1:
                    self.topic2partially_relevant_docs[q_id].add(pmid)
                    rated_documents.add(pmid)
                elif rating == 0:
                    self.topic2not_relevant_docs[q_id].add(pmid)
                    rated_documents.add(pmid)
                else:
                    raise ValueError(f'Rating value {rating} not supported')

        logging.info(f'Benchmark has {len(rated_documents)} distinct and rated documents')
        self.topics = TrecGen2005Topic.parse_topics()
        self.topics = [t for t in self.topics if t.query_id in eval_topics]

        # will extend the topic dictionaries
        super().load_benchmark_data()

def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)
    benchmark = Genomics2005()
    for t in benchmark.topics:
        print(
            f'{t} => {len(benchmark.topic2relevant_docs[t.query_id])} relevant docs / {len(benchmark.topic2not_relevant_docs[t.query_id])} not relevant docs')

    print()
    logging.info(f'TG2005 has {len(benchmark.topics)} relevant topics')
    logging.info(f'TG2005 has {len(benchmark.get_documents_for_baseline())} considered documents')


if __name__ == '__main__':
    main()
