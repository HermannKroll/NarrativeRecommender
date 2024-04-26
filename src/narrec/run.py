import os
from datetime import datetime
from multiprocessing import Process

from tqdm import tqdm

from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import Benchmark
from narrec.citation.graph import CitationGraph
from narrec.config import RESULT_DIR, INDEX_DIR, GLOBAL_DB_DOCUMENT_COLLECTION
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.firststage.base import FirstStageBase
from narrec.firststage.fsconceptflex import FSConceptFlex
from narrec.firststage.fscoreflex import FSCoreFlex
from narrec.firststage.fsnodeflex import FSNodeFlex
from narrec.recommender.aligned_cores import AlignedCoresRecommender
from narrec.recommender.aligned_nodes import AlignedNodesRecommender
from narrec.recommender.coreoverlap import CoreOverlap
from narrec.recommender.equal import EqualRecommender
from narrec.recommender.graph_base_fallback_bm25 import GraphBaseFallbackBM25
from narrec.recommender.jaccard import Jaccard
from narrec.recommender.jaccard_combined import JaccardCombinedWeighted
from narrec.recommender.jaccard_concepts_weighted import JaccardConceptWeighted
from narrec.recommender.jaccard_graph_weighted import JaccardGraphWeighted
from narrec.recommender.statementoverlap import StatementOverlap
from narrec.run_config import BENCHMARKS, DO_RECOMMENDATION, MULTIPROCESSING, LOAD_FULL_IDF_CACHE, \
    ADD_GRAPH_BASED_BM25_FALLBACK_RECOMMENDERS, RERUN_FIRST_STAGES, FS_DOCUMENT_CUTOFF_HARD
from narrec.scoring.BM25Scorer import BM25Scorer


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
                                  result_path: str, write_results=True, verbose=True, progress=False):
    if verbose:
        print(f'Creating first stage runfile for benchmark: {benchmark.name} with stage: {first_stage.name}')
    result_lines = []

    if verbose:
        print('Retrieve document contents...')
    doc_ids = [d[1] for d in benchmark.iterate_over_document_entries()]
    input_docs = retriever.retrieve_narrative_documents(document_ids=doc_ids,
                                                        document_collection=benchmark.document_collection)
    docid2docs = {d.id: d for d in input_docs}

    if verbose:
        print('Perform first stage retrieval')
    doc_queries = list(benchmark.iterate_over_document_entries())
    if MULTIPROCESSING and not progress:
        iter_obj = doc_queries
    else:
        iter_obj = tqdm(doc_queries, total=len(doc_queries))

    for q_idx, doc_id in iter_obj:
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
            if verbose:
                print(f'Document {doc_id} not known in our collection - skipping')

    if write_results:
        print(f'Results will be written to {result_path}')
        with open(result_path, 'wt') as f:
            f.write('\n'.join([l for l in result_lines]))


def process_benchmark(bench: Benchmark):
    corpus = DocumentCorpus(collections=[GLOBAL_DB_DOCUMENT_COLLECTION])
    if LOAD_FULL_IDF_CACHE:
        corpus.load_all_support_into_memory()

    retriever = DocumentRetriever()
    core_extractor = NarrativeCoreExtractor(corpus=corpus)
    bm25_scorer = BM25Scorer(None)

    citation_graph = CitationGraph()

    recommenders = [EqualRecommender(), AlignedNodesRecommender(corpus), AlignedCoresRecommender(corpus),
                    StatementOverlap(core_extractor), Jaccard(), CoreOverlap(extractor=core_extractor),
                    JaccardGraphWeighted(corpus), JaccardConceptWeighted(corpus), JaccardCombinedWeighted(corpus)]

    if ADD_GRAPH_BASED_BM25_FALLBACK_RECOMMENDERS:
        for r in recommenders.copy():
            recommenders.append(GraphBaseFallbackBM25(bm25scorer=bm25_scorer, graph_recommender=r))

    bench.load_benchmark_data()
    index_path = os.path.join(INDEX_DIR, bench.get_index_name())
    bm25_scorer.set_index(index_path)

    first_stages = [FSConceptFlex(core_extractor, bench),
                    FSCoreFlex(core_extractor, bench),
                    FSNodeFlex(core_extractor, bench)]
    # FSConceptPlus(core_extractor, bench),
    #                 FSConcept(core_extractor, bench),
    #                 FSCore(core_extractor, bench),
    #                 FSNode(core_extractor, bench),
    #                 PubMedRecommender(bench),
    #                 BM25Abstract(index_path),
    #                 BM25Title(index_path),
    #                 Perfect(bench)]

    for first_stage in first_stages:
        fs_path = os.path.join(RESULT_DIR, f'{bench.name}_{first_stage.name}.txt')
        if not os.path.isfile(fs_path) or RERUN_FIRST_STAGES:
            # create first stage data
            run_first_stage_for_benchmark(retriever, bench, first_stage, fs_path)
        # next load the documents for this first stage
        print(f'Loading first stage runfile: {fs_path}')
        fs_docs = load_document_ids_from_runfile(fs_path)
        fs_topic2doc2scores = {t: {doc: score for doc, score in pair}
                               for t, pair in fs_docs.items()}

        recommender2result_lines = dict()

        if DO_RECOMMENDATION:
            # don't print in multi processing setting
            if MULTIPROCESSING:
                iter_obj = fs_docs.items()
                print('Disable progress bar for multiprocess setting')
            else:
                iter_obj = tqdm(fs_docs.items(), desc="Evaluating topics")

            count = 0
            for topicid, retrieved_docs in iter_obj:
                count += 1
                if len(retrieved_docs) >= FS_DOCUMENT_CUTOFF_HARD:
                    print(f'No of retrieved documents exceed {FS_DOCUMENT_CUTOFF_HARD} - cutting list (benchmark: {bench.name} / first stage: {first_stage.name})')
                    retrieved_docs = retrieved_docs[:FS_DOCUMENT_CUTOFF_HARD]

                if MULTIPROCESSING:
                    if count % 250 == 0:
                        print(f'{bench.name}-{first_stage.name}: Processed {count} of {len(fs_docs.items())} topics')

                # get the input ids for each doc
                topic2doc = {str(top): doc for top, doc in bench.iterate_over_document_entries()}

                # Retrieve the input document
                input_doc = retriever.retrieve_narrative_documents([topic2doc[topicid]],
                                                                   GLOBAL_DB_DOCUMENT_COLLECTION)[0]

                # Retrieve the documents to score
                retrieved_doc_ids = [d[0] for d in retrieved_docs]
                documents = retriever.retrieve_narrative_documents(retrieved_doc_ids,
                                                                   GLOBAL_DB_DOCUMENT_COLLECTION)
                # set first stage scores in documents
                for doc in documents:
                    # get scores
                    doc.set_first_stage_score(fs_topic2doc2scores[topicid][doc.id])

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


def main():
    if MULTIPROCESSING:
        print('Using multiprocessing architecture...')
        processes = []
        for benchmark in BENCHMARKS:
            print(f'Initialize process for benchmark: {benchmark.name}')
            processes.append(Process(target=process_benchmark, args=(benchmark,)))

        print('Starting all processes')
        for p in processes:
            p.start()

        print('Waiting for process to finish...')
        for p in processes:
            p.join()

        print('All processes were finished')

    else:
        for benchmark in BENCHMARKS:
            process_benchmark(benchmark)


if __name__ == '__main__':
    main()
