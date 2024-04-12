from narrec.benchmark.genomics2005 import Genomics2005
from narrec.benchmark.pm2020 import PM2020Benchmark
from narrec.benchmark.relish import RelishBenchmark
from narrec.benchmark.relishdrug import RelishDrugBenchmark

ADD_GRAPH_BASED_BM25_FALLBACK_RECOMMENDERS = True

FIRST_STAGES = [
    "Perfect",
    "BM25Title",
    "BM25Abstract",
    # "BM25Yake",
    "FSConcept",
    "FSCore",
    #  "FSCoreOverlap",
    # "FSCorePlusAbstractBM25",
    # "FSCorePlusTitleBM25",
    "PubMedRecommender"
]

RECOMMENDER_NAMES = [
    "EqualRecommender",
    "StatementOverlap",
    "JaccardCombinedWeighted",
    "JaccardGraphWeighted",
    "JaccardConceptWeighted",
    "AlignedNodesRecommender",
    "AlignedCoresRecommender",
    "AlignedNodesRecommender",
    "AlignedCoresRecommender",
    "CoreOverlap"
]

if ADD_GRAPH_BASED_BM25_FALLBACK_RECOMMENDERS:
    for r in RECOMMENDER_NAMES.copy():
        RECOMMENDER_NAMES.append(f'{r}_BM25Fallback')

BENCHMARKS = [
    PM2020Benchmark(),
    Genomics2005(),
    RelishBenchmark(),
    RelishDrugBenchmark()

]

CONFIDENCE_WEIGHT = 0.5
TFIDF_WEIGHT = 0.5
CORE_TOP_K = 10

assert CONFIDENCE_WEIGHT + TFIDF_WEIGHT == 1.0

NARRATIVE_CORE_THRESHOLD = 0.0
NODE_SIMILARITY_THRESHOLD = 0.3

GRAPH_WEIGHT = 0.6
BM25_WEIGHT = 0.4

assert GRAPH_WEIGHT + BM25_WEIGHT == 1.0

MULTIPROCESSING = False
LOAD_FULL_IDF_CACHE = True
DO_RECOMMENDATION = True
JUDGED_DOCS_ONLY_FLAG = True

# Experimental Configuration (because first stage will always find input doc)
FS_DOCUMENT_CUTOFF = 1001

print('--' * 60)
print(f'Confidence weight : {CONFIDENCE_WEIGHT}')
print(f'TF-IDF weight     : {TFIDF_WEIGHT}')
print(f'Core threshold    : {NARRATIVE_CORE_THRESHOLD}')
print(f'Document FS cutoff: {FS_DOCUMENT_CUTOFF}')
print(f'Node similarity t.: {NODE_SIMILARITY_THRESHOLD}')
print('--' * 60)
