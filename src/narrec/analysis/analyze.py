from tqdm import tqdm

from narrant.entitylinking.enttypes import DRUG
from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import Benchmark
from narrec.config import GLOBAL_DB_DOCUMENT_COLLECTION
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.run_config import BENCHMARKS, LOAD_FULL_IDF_CACHE


def analyze_benchmark(retriever: DocumentRetriever, benchmark: Benchmark):
    print(f'Analyzing benchmark: {benchmark.name}')
    result_lines = []

    print('Retrieve document contents...')
    doc_ids = [d[1] for d in benchmark.iterate_over_document_entries()]
    input_docs = retriever.retrieve_narrative_documents(document_ids=doc_ids,
                                                        document_collection=benchmark.document_collection)
    docid2docs = {d.id: d for d in input_docs}

    corpus = DocumentCorpus(collections=[GLOBAL_DB_DOCUMENT_COLLECTION])
    if LOAD_FULL_IDF_CACHE:
        corpus.load_all_support_into_memory()

    core_extractor = NarrativeCoreExtractor(corpus=corpus)

    graph_size2count = {}
    concept_count2count = {}
    count_has_drug = 0
    count_has_drug_in_graph = 0
    no_docs = 0
    doc_queries = list(benchmark.iterate_over_document_entries())
    for q_idx, doc_id in tqdm(doc_queries, total=len(doc_queries)):
        no_docs += 1
        try:
            input_doc = docid2docs[int(doc_id)]

            core = core_extractor.extract_narrative_core_from_document(input_doc)
            if core:
                doc_graph_size = len(core.statements)
            else:
                doc_graph_size = 0

            if doc_graph_size not in graph_size2count:
                graph_size2count[doc_graph_size] = 0
            graph_size2count[doc_graph_size] += 1

            concept_core = core_extractor.extract_concept_core(input_doc)
            if concept_core:
                concept_count = len(concept_core.concepts)
            else:
                concept_count = 0

            if concept_count not in concept_count2count:
                concept_count2count[concept_count] = 0
            concept_count2count[concept_count] += 1

            if DRUG in {t.ent_type for t in input_doc.tags}:
                count_has_drug += 1

            cond1 = DRUG in {s.subject_type for s in input_doc.extracted_statements}
            cond2 = DRUG in {s.object_type for s in input_doc.extracted_statements}
            if cond1 or cond2:
                count_has_drug_in_graph += 1

        except KeyError:
            print(f'Document {doc_id} not known in our collection - skipping')

    ranges_to_repot = [(0, 5), (0, 10), (5, 10000000), (10, 10000000)]
    print(f'Count of documents is: {no_docs}')
    for r_min, r_max in ranges_to_repot:
        sum_concepts = 0
        sum_graph_size = 0
        for i in range(r_min, r_max + 1):
            if i in graph_size2count:
                sum_graph_size += graph_size2count[i]

            if i in concept_count2count:
                sum_concepts += concept_count2count[i]

        ratio_con = 100 * round(sum_concepts / no_docs, 2)
        ratio_graph = 100 * round(sum_graph_size / no_docs, 2)
        print(f'Documents with concept count in range {r_min} - {r_max} - Sum: {sum_concepts} ({ratio_con}%)')
        print(f'Documents with graph size    in range {r_min} - {r_max} - Sum: {sum_graph_size} ({ratio_graph}%)')

    print()
    print('Has a drug concept  : ', count_has_drug)
    print('Has a drug statement: ', count_has_drug_in_graph)


def main():
    retriever = DocumentRetriever()

    for bench in BENCHMARKS:
        bench.load_benchmark_data()
        analyze_benchmark(retriever, bench)


if __name__ == '__main__':
    main()
