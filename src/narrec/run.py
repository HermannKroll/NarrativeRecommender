import os
from datetime import datetime

from tqdm import tqdm

from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import BenchmarkType, Benchmark
from narrec.benchmark.relish import RelishBenchmark
from narrec.citation.graph import CitationGraph
from narrec.config import RESULT_DIR, INDEX_DIR, GLOBAL_DB_DOCUMENT_COLLECTION
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.firststage.base import FirstStageBase
from narrec.firststage.bm25abstract import BM25Abstract
from narrec.firststage.bm25title import BM25Title
from narrec.firststage.bm25yake import BM25Yake
from narrec.firststage.fscore import FSCore
from narrec.firststage.fscoreplusabstractbm25 import FSCorePlusAbstractBM25
from narrec.firststage.fscoreplustitlebm25 import FSCorePlusTitleBM25
from narrec.recommender.simple import RecommenderSimple


def load_document_ids_from_runfile(path_to_runfile):
    topic2docs = {}
    with open(path_to_runfile, 'rt') as f:
        for line in f:
            components = line.split('\t')
            topic_id = int(components[0])
            doc_id = int(components[2])
            score = float(components[4])

            if topic_id not in topic2docs:
                topic2docs[topic_id] = [(doc_id, score)]
            else:
                topic2docs[topic_id].append((doc_id, score))

    return topic2docs


def run_first_stage_for_benchmark(retriever: DocumentRetriever, benchmark: Benchmark, first_stage: FirstStageBase,
                                  result_path: str):
    print(f'Creating first stage runfile for benchmark: {benchmark.name} with stage: {first_stage.name}')
    result_lines = []

    print('Retrieve document contents...')
    doc_ids = [d[1] for d in benchmark.iterate_over_document_entries()]
    input_docs = retriever.retrieve_narrative_documents(document_ids=doc_ids,
                                                        document_collection=benchmark.document_collection)
    docid2docs = {d.id: d for d in input_docs}

    print('Perform first stage retrieval')
    doc_queries = list(benchmark.iterate_over_document_entries())
    for q_idx, doc_id in tqdm(doc_queries, total=len(doc_queries)):
        try:
            input_doc = docid2docs[int(doc_id)]
            retrieved_docs = first_stage.retrieve_documents_for(input_doc)

            for rank, (fs_docid, score) in enumerate(retrieved_docs):
                if int(fs_docid) == input_doc.id:
                    continue

                result_line = f'{q_idx}\tQ0\t{fs_docid}\t{rank + 1}\t{score}\t{first_stage.name}'
                result_lines.append(result_line)
        except KeyError:
            print(f'Document {doc_id} not known in our collection - skipping')

    print(f'Results will be written to {result_path}')
    with open(result_path, 'wt') as f:
        f.write('\n'.join([l for l in result_lines]))


def main():
    benchmarks = [RelishBenchmark()]
    corpus = DocumentCorpus(collections=[GLOBAL_DB_DOCUMENT_COLLECTION])
    core_extractor = NarrativeCoreExtractor(corpus=corpus)
    retriever = DocumentRetriever()
    citation_graph = CitationGraph()
    recommenders = [RecommenderSimple()]
    DO_RECOMMENDATION = False

    for bench in benchmarks:
        index_path = os.path.join(INDEX_DIR, bench.name)
        first_stages = [FSCore(core_extractor, bench),
                    #    FSCorePlusAbstractBM25(core_extractor, bench, index_path),
                    #    FSCorePlusTitleBM25(core_extractor, bench, index_path),
                        BM25Title(index_path), BM25Abstract(index_path),
                        BM25Yake(index_path)]

        for first_stage in first_stages:
            if bench.type == BenchmarkType.REC_BENCHMARK:
                fs_path = os.path.join(RESULT_DIR, f'{bench.name}_{first_stage.name}.txt')
                if not os.path.isfile(fs_path):
                    # create first stage data
                    run_first_stage_for_benchmark(retriever, bench, first_stage, fs_path)
                # next load the documents for this first stage
                print(f'Loading first stage runfile: {fs_path}')
                fs_docs = load_document_ids_from_runfile(fs_path)

                for input_docid, retrieved_docs in fs_docs.items():

                    if DO_RECOMMENDATION:
                        # Retrieve the input document
                        input_doc = \
                            retriever.retrieve_narrative_documents([input_docid], GLOBAL_DB_DOCUMENT_COLLECTION)[0]

                        # Retrieve the documents to score
                        retrieved_doc_ids = [d[0] for d in retrieved_docs]
                        documents = retriever.retrieve_narrative_documents(retrieved_doc_ids,
                                                                           GLOBAL_DB_DOCUMENT_COLLECTION)

                        for recommender in recommenders:
                            start = datetime.now()
                            rec_docs = recommender.recommend_documents(input_doc, documents, citation_graph)

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

                                    result_line = f'{input_docid}\tQ0\t{doc_id}\t{rank + 1}\t{norm_score}\t{recommender.name}'
                                    result_lines.append(result_line)

                            time_taken = datetime.now() - start
                            print(f'{time_taken}s to compute {recommender.name}')

                            path = os.path.join(RESULT_DIR,
                                                f'{bench.name}_{input_docid}_{recommender.name}.txt')
                            with open(path, 'wt') as f:
                                f.write('\n'.join(result_lines))


            elif bench.type == BenchmarkType.IR_BENCHMARK:
                raise NotImplementedError

                # Idea: for each topic, get all relevant documents
                # Select one of these documents
                # perform the recommendation step
                # results = []
                # for relevant_document in relevant:
                #     # Do recommendation
                #     scores = []
                #
                #     # Needs to implement a first stage
                #     # recommended_documents = recommender.recommend_documents(relevant_document, )
                #
                #     results.append((relevant_document, scores))
                #
                #     pass

                # Average over scores

                # Todo: implement some statistics here

            else:
                raise NotImplementedError


if __name__ == '__main__':
    main()
