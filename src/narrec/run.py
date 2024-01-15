import os
from datetime import datetime

from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import BenchmarkType
from narrec.benchmark.relish import RelishBenchmark
from narrec.citation.graph import CitationGraph
from narrec.config import RESULT_DIR
from narrec.recommender.simple import RecommenderSimple


def load_document_ids_from_runfile(path_to_runfile):
    topic2docs = {}
    with open(path_to_runfile, 'rt') as f:
        for line in f:
            components = line.split('\t')
            topic_id = int(components[0])
            doc_id = components[2]
            score = float(components[4])

            if topic_id not in topic2docs:
                topic2docs[topic_id] = [(doc_id, score)]
            else:
                topic2docs[topic_id].append((doc_id, score))

    return topic2docs


def main():
    benchmarks = [RelishBenchmark()]
    retriever = DocumentRetriever()
    citation_graph = CitationGraph()
    first_stages = ["BM25"]
    recommenders = [RecommenderSimple()]

    for bench in benchmarks:
        for first_stage in first_stages:
            fs_path = os.path.join(RESULT_DIR, first_stage)
            fs_docs = load_document_ids_from_runfile(fs_path)

            if bench.type == BenchmarkType.REC_BENCHMARK:
                for topic in bench.topics:
                    documents = retriever.retrieve_narrative_documents(fs_docs, "PubMed")
                    docid2doc = {d.id: d for d in documents}

                    for recommender in recommenders:
                        start = datetime.now()
                        rec_docs = recommender.recommend_documents(docid2doc[topic], documents, citation_graph)

                        result_lines = []
                        if len(rec_docs) > 0:
                            max_score = rec_docs[0][1]
                            if max_score < 0.0:
                                raise ValueError(
                                    f'Max score {max_score} <= (score = {max_score} / ranker = {recommender.name})')

                            for rank, (doc_id, score) in enumerate(rec_docs):
                                if max_score > 0.0:
                                    norm_score = score / max_score
                                else:
                                    norm_score = 0.0

                                if norm_score > 1.0 or norm_score < 0.0:
                                    raise ValueError(
                                        f'Document {doc_id} received a score not in [0, 1] (score = {norm_score} / ranker = {recommender.name})')

                                result_line = f'{q.query_id}\tQ0\t{doc_id}\t{rank + 1}\t{norm_score}\t{recommender.name}'
                                result_lines.append(result_line)

                        time_taken = datetime.now() - start
                        print(f'{time_taken}s to compute {recommender.name}')

                        path = os.path.join(RESULT_DIR,
                                            f'{bench.name}_{topic}_{recommender.name}.txt')
                        with open(path, 'wt') as f:
                            f.write('\n'.join(result_lines))


            elif bench.type == BenchmarkType.IR_BENCHMARK:
                raise NotImplementedError
            else:
                raise NotImplementedError


if __name__ == '__main__':
    main()
