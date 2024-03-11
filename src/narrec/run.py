import os
from datetime import datetime

from tqdm import tqdm

from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import Benchmark
from narrec.citation.graph import CitationGraph
from narrec.config import RESULT_DIR, INDEX_DIR, GLOBAL_DB_DOCUMENT_COLLECTION
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.firststage.base import FirstStageBase
from narrec.firststage.bm25abstract import BM25Abstract
from narrec.firststage.fscore import FSCore
from narrec.firststage.fscore_overlap import FSCoreOverlap
from narrec.firststage.perfect import Perfect
from narrec.firststage.pubmed import PubMedRecommender
from narrec.recommender.aligned_cores import AlignedCoresRecommender
from narrec.recommender.aligned_nodes import AlignedNodesRecommender
from narrec.recommender.equal import EqualRecommender
from narrec.recommender.jaccard import Jaccard
from narrec.recommender.jaccard_weighted import JaccardWeighted
from narrec.recommender.statementoverlap import StatementOverlap
from narrec.run_config import BENCHMARKS


def load_document_ids_from_runfile(path_to_runfile):
    topic2docs = {}
    with open(path_to_runfile, 'rt') as f:
        for line in f:
            components = line.split('\t')
            topic_id = str(components[0])
            doc_id = int(components[2])
            score = float(components[4])

            assert len(topic_id) > 0
            assert int(doc_id) >= 0
            assert 0.0 <= score <= 1.0

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
            first_stage.set_current_topic(q_idx)
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
    benchmarks = BENCHMARKS
    corpus = DocumentCorpus(collections=[GLOBAL_DB_DOCUMENT_COLLECTION])
    core_extractor = NarrativeCoreExtractor(corpus=corpus)
    retriever = DocumentRetriever()
    citation_graph = CitationGraph()
    recommenders = [EqualRecommender(),
                    AlignedNodesRecommender(corpus), AlignedCoresRecommender(corpus),
                    StatementOverlap(core_extractor), Jaccard(), JaccardWeighted(corpus)]
    DO_RECOMMENDATION = True

    for bench in benchmarks:
        bench.load_benchmark_data()
        index_path = os.path.join(INDEX_DIR, bench.get_index_name())
        first_stages = [FSCore(core_extractor, bench),
                        FSCoreOverlap(core_extractor, bench, index_path, retriever),
                        PubMedRecommender(bench),
                        BM25Abstract(index_path),
                        Perfect(bench)]
        # FSCorePlusAbstractBM25(core_extractor, bench, index_path),
        # FSCorePlusTitleBM25(core_extractor, bench, index_path),
        # BM25Title(index_path),, BM25Yake(index_path)]

        for first_stage in first_stages:

            fs_path = os.path.join(RESULT_DIR, f'{bench.name}_{first_stage.name}.txt')
            if not os.path.isfile(fs_path):
                # create first stage data
                run_first_stage_for_benchmark(retriever, bench, first_stage, fs_path)
            # next load the documents for this first stage
            print(f'Loading first stage runfile: {fs_path}')
            fs_docs = load_document_ids_from_runfile(fs_path)

            recommender2result_lines = dict()

            if DO_RECOMMENDATION:
                for topicid, retrieved_docs in tqdm(fs_docs.items(), desc="Evaluating topics"):
                    # get the input ids for each doc
                    topic2doc = {str(top): doc for top, doc in bench.iterate_over_document_entries()}

                    # Retrieve the input document
                    input_doc = retriever.retrieve_narrative_documents([topic2doc[topicid]],
                                                                       GLOBAL_DB_DOCUMENT_COLLECTION)[0]

                    # Retrieve the documents to score
                    retrieved_doc_ids = [d[0] for d in retrieved_docs]
                    documents = retriever.retrieve_narrative_documents(retrieved_doc_ids,
                                                                       GLOBAL_DB_DOCUMENT_COLLECTION)

                    # only apply recommender if first stage returned a result
                    if len(documents) > 0:
                        for recommender in recommenders:

                            if recommender.name not in recommender2result_lines:
                                recommender2result_lines[recommender.name] = list()

                            start = datetime.now()
                            rec_docs = recommender.recommend_documents(input_doc, documents, citation_graph)
                            assert len(rec_docs) == len(documents)

                            if len(rec_docs) > 0:
                                max_score = rec_docs[0][1]
                                if max_score < 0.0:
                                    raise ValueError(f'Max score {max_score} <= (score = {max_score} /'
                                                     f' ranker = {recommender.name})')

                                for rank, (doc_id, score) in enumerate(rec_docs):
                                    if max_score > 0.0:
                                        norm_score = score / max_score
                                    else:
                                        norm_score = 0.0

                                    if norm_score < 0.0 or norm_score > 1.0:
                                        raise ValueError(f'Document {doc_id} received a score not in (score = '
                                                         f'{norm_score} / ranker = {recommender.name})')

                                    result_line = f'{topicid}\tQ0\t{doc_id}\t{rank + 1}\t{norm_score}\t{recommender.name}'
                                    recommender2result_lines[recommender.name].append(result_line)

                                time_taken = datetime.now() - start
                                # print(f'{time_taken}s to compute {recommender.name}')

                for recommender in recommenders:
                    path = os.path.join(RESULT_DIR, f'{bench.name}_{first_stage.name}_{recommender.name}.txt')
                    print(f'Writing results to {path}')
                    with open(path, 'wt') as f:
                        if recommender.name in recommender2result_lines:
                            f.write('\n'.join(recommender2result_lines[recommender.name]))


if __name__ == '__main__':
    main()
