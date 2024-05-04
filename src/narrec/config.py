import os

GLOBAL_DB_DOCUMENT_COLLECTION = "PubMed"

GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
RESOURCE_DIR = os.path.join(GIT_ROOT_DIR, "resources")
CONFIG_DIR = os.path.join(GIT_ROOT_DIR, "config")
DATA_DIR = "/ssd2/kroll/recommender/"

RESULT_DIR = os.path.join(DATA_DIR, "results")
INDEX_DIR = os.path.join(DATA_DIR, "indexes")
BENCHMKARK_QRELS_DIR = os.path.join(DATA_DIR, "benchmark_qrels")
DIAGRAM_DIR = os.path.join(DATA_DIR, "diagrams")

TOPIC_SCORES = os.path.join(DIAGRAM_DIR, "topic_scores")
SCORE_FREQUENCY = os.path.join(DIAGRAM_DIR, "score_frequency")

if not os.path.isdir(TOPIC_SCORES):
    os.makedirs(TOPIC_SCORES, exist_ok=True)

if not os.path.isdir(SCORE_FREQUENCY):
    os.makedirs(SCORE_FREQUENCY, exist_ok=True)

if not os.path.isdir(RESULT_DIR):
    os.makedirs(RESULT_DIR, exist_ok=True)

if not os.path.isdir(INDEX_DIR):
    os.makedirs(INDEX_DIR, exist_ok=True)

if not os.path.isdir(BENCHMKARK_QRELS_DIR):
    os.makedirs(BENCHMKARK_QRELS_DIR, exist_ok=True)

if not os.path.isdir(DIAGRAM_DIR):
    os.makedirs(DIAGRAM_DIR, exist_ok=True)

BENCHMARK_DIR = os.path.join(RESOURCE_DIR, "benchmarks")

TG2005_TOPIC_FILE = os.path.join(BENCHMARK_DIR, "trec_genomics2005_topics.txt")
TG2005_BENCHMARK_FILE = os.path.join(BENCHMARK_DIR, "trec_genomics2005_documents.txt")
RELISH_BENCHMARK_JSON_FILE = os.path.join(BENCHMARK_DIR, "RELISH_v1.json")
PM2020_BENCHMARK_FILE = os.path.join(BENCHMARK_DIR, "trec_pm2020_documents.txt")
PM2020_TOPIC_FILE = os.path.join(BENCHMARK_DIR, "trec_pm2020_topics.xml")

TG2005_PMIDS_FILE = os.path.join(DATA_DIR, "pmids_tg2005.txt")
RELISH_PMIDS_FILE = os.path.join(DATA_DIR, "pmids_pm2018.txt")
PM2020_PMIDS_FILE = os.path.join(DATA_DIR, "pmids_pm2020.txt")
# DB Backend
BACKEND_CONFIG = os.path.join(CONFIG_DIR, "backend.json")

ANALYSIS_DIR = os.path.join(DATA_DIR, "analysis")
if not os.path.isdir(ANALYSIS_DIR):
    os.makedirs(ANALYSIS_DIR, exist_ok=True)

RUNTIME_MEASUREMENT_RESULT_DIR = os.path.join(ANALYSIS_DIR, "firststage_runtimes")
if not os.path.isdir(RUNTIME_MEASUREMENT_RESULT_DIR):
    os.makedirs(RUNTIME_MEASUREMENT_RESULT_DIR, exist_ok=True)

RUNTIME_MEASUREMENT_RECOMMENDATION_RESULT_DIR = os.path.join(ANALYSIS_DIR, "recommendation_runtimes")
if not os.path.isdir(RUNTIME_MEASUREMENT_RECOMMENDATION_RESULT_DIR):
    os.makedirs(RUNTIME_MEASUREMENT_RECOMMENDATION_RESULT_DIR, exist_ok=True)
