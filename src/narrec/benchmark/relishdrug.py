import logging
import os.path

from tqdm import tqdm

from narrant.preprocessing.enttypes import DRUG
from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.relish import RelishBenchmark
from narrec.config import BENCHMKARK_QRELS_DIR


class RelishDrugBenchmark(RelishBenchmark):

    def __init__(self):
        self.documents_with_idx = []
        self.document_idx_ids_with_drugs = set()
        super().__init__(name="RELISH_DRUG")

    def get_index_name(self):
        # use the same index as relish
        return RelishBenchmark.NAME

    def load_benchmark_data(self):
        super().load_benchmark_data()
        # Keep only those input benchmark documents that have a drug in their graph
        print('Querying document content to retrieve subset of documents with drugs on their graphs...')
        doc_ids = [d[1] for d in self.iterate_over_document_entries()]
        retriever = DocumentRetriever()
        bench_docs = retriever.retrieve_narrative_documents(document_ids=doc_ids,
                                                            document_collection=self.document_collection)

        docid2docs = {d.id: d for d in bench_docs}
        doc_queries = list(self.iterate_over_document_entries())
        for q_idx, doc_id in tqdm(doc_queries, total=len(doc_queries)):
            try:
                input_doc = docid2docs[int(doc_id)]

                cond1 = DRUG in {s.subject_type for s in input_doc.extracted_statements}
                cond2 = DRUG in {s.object_type for s in input_doc.extracted_statements}
                if cond1 or cond2:
                    self.document_idx_ids_with_drugs.add((q_idx, doc_id))
            except KeyError:
                print(f'Document {doc_id} not known in our collection - skipping')

        self.topic2relevant_docs = {key: v for key, v in self.topic2relevant_docs.items()
                                    if key in self.document_idx_ids_with_drugs}
        self.topic2partially_relevant_docs = {key: v for key, v in self.topic2partially_relevant_docs.items()
                                              if key in self.document_idx_ids_with_drugs}
        self.topic2not_relevant_docs = {key: v for key, v in self.topic2not_relevant_docs.items()
                                        if key in self.document_idx_ids_with_drugs}

        self.topics = [key for key in self.topics
                       if key in self.document_idx_ids_with_drugs]

        self.documents_with_idx = [key for key in self.documents_with_idx
                                   if key in self.document_idx_ids_with_drugs]

        print(f'{len(self.document_idx_ids_with_drugs)} documents have drugs on their graphs')

    def get_qrel_path(self):
        super().get_qrel_path()
        path = os.path.join(BENCHMKARK_QRELS_DIR, f'{self.name}_qrels.txt')
        # Rewrite the Relish qrels file and only keep those query lines which
        # belong to benchmark input documents with drugs
        if not os.path.isfile(path):
            # open new qrel path
            with open(path, 'wt') as f_out:
                # read in Relish qrels
                relish_path = os.path.join(BENCHMKARK_QRELS_DIR, f'{RelishBenchmark.NAME}_qrels.txt')
                relevant_index_lines = {str(k) for k, _ in self.document_idx_ids_with_drugs}
                with open(relish_path, 'rt') as f_in:
                    for line in f_in:
                        comps = line.strip().split()
                        # filter that query belongs to RelishDrug benchmark
                        if comps[0] in relevant_index_lines:
                            f_out.write(line)

            RelishBenchmark.process_json_to_txt(path)
        return path


# for test purposes
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)
    benchmark = RelishBenchmark()
    logging.info(f'Benchmark has {len(benchmark.get_documents_for_baseline())} documents')
    print(benchmark.get_qrel_path())
