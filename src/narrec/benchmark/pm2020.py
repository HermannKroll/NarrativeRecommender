import logging
from xml.etree import ElementTree

from narrec.benchmark.benchmark import Benchmark, BenchmarkType
from narrec.config import PM2020_TOPIC_FILE, PM2020_BENCHMARK_FILE, PM2020_PMIDS_FILE

DRUG = "Drug"
CHEMICAL = "Chemical"
DISEASE = "Disease"
TARGET = "Target"
GENE = "Gene"


class PrecMed2020Topic:

    def __init__(self, number, disease, gene, treatment):
        self.query_id = int(number)
        self.disease = disease
        self.gene = gene
        self.treatment = treatment

    def __str__(self):
        return f'<{self.query_id} disease={self.disease} gene={self.gene} treatment={self.treatment}>'

    def __repr__(self):
        return str(self)

    def get_query_components(self) -> [str]:
        yield from [[(self.disease, [DISEASE])], [(self.gene, [GENE, TARGET])], [(self.treatment, [DRUG, CHEMICAL])]]

    def get_benchmark_string(self):
        return f'{self.disease} {self.gene} {self.treatment}'

    @staticmethod
    def parse_topics(path_to_file=PM2020_TOPIC_FILE):
        with open(path_to_file) as file:
            root = ElementTree.parse(file).getroot()

        if root is None:
            return

        topics = []
        for topic in root.findall('topic'):
            number = topic.get('number')
            disease = topic.find('disease').text.strip()
            gene = topic.find('gene').text.strip()
            treatment = topic.find('treatment').text.strip()
            topics.append(PrecMed2020Topic(number, disease, gene, treatment))
        return topics


class PM2020Benchmark(Benchmark):

    def __init__(self):
        self.topics: [PrecMed2020Topic] = []
        super().__init__(name="PM2020", path_to_document_ids=PM2020_PMIDS_FILE, type=BenchmarkType.REC_BENCHMARK)

    def get_qrel_path(self):
        return PM2020_BENCHMARK_FILE

    def load_benchmark_data(self):
        logging.info(f'Loading Benchmark data from {PM2020_BENCHMARK_FILE}...')
        eval_topics = set()
        rated_documents = set()
        with open(PM2020_BENCHMARK_FILE, 'rt') as f:
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
        self.topics = PrecMed2020Topic.parse_topics()
        self.topics = [t for t in self.topics if t.query_id in eval_topics]

    def __str__(self):
        return f'<{self.name}>'

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)

    benchmark = PM2020Benchmark()
    for t in benchmark.topics:
        print(
            f'{t} => {len(benchmark.topic2relevant_docs[t.query_id])} relevant docs / {len(benchmark.topic2not_relevant_docs[t.query_id])} not relevant docs')

    print()
    logging.info(f'PM2020 has {len(benchmark.topics)} relevant topics')
    logging.info(f'PM2020 has {len(benchmark.get_documents_for_baseline())} considered documents')
