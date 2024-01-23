import os

GLOBAL_DB_DOCUMENT_COLLECTION = "PubMed"

GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
RESOURCE_DIR = os.path.join(GIT_ROOT_DIR, "resources")
CONFIG_DIR = os.path.join(GIT_ROOT_DIR, "config")
DATA_DIR = "/ssd2/kroll/recommender/"

RESULT_DIR = os.path.join(DATA_DIR, "results")
INDEX_DIR = os.path.join(DATA_DIR, "indexes")

if not os.path.isdir(RESULT_DIR):
    os.makedirs(RESULT_DIR, exist_ok=True)

if not os.path.isdir(INDEX_DIR):
    os.makedirs(INDEX_DIR, exist_ok=True)

BENCHMARK_DIR = os.path.join(RESOURCE_DIR, "benchmarks")

TG2005_TOPIC_FILE = os.path.join(BENCHMARK_DIR, "trec_genomics2005_topics.txt")
TG2005_BENCHMARK_FILE = os.path.join(BENCHMARK_DIR, "trec_genomics2005_documents.txt")
RELISH_BENCHMARK_JSON_FILE = os.path.join(BENCHMARK_DIR, "RELISH_v1.json")
RELISH_BENCHMARK_FILE = os.path.join(BENCHMARK_DIR, "RELISH_documents.txt")
PM2020_BENCHMARK_FILE = os.path.join(BENCHMARK_DIR, "trec_pm2020_documents.txt")
PM2020_TOPIC_FILE = os.path.join(BENCHMARK_DIR, "trec_pm2020_topics.xml")

TG2005_PMIDS_FILE = os.path.join(DATA_DIR, "pmids_tg2005.txt")
RELISH_PMIDS_FILE = os.path.join(DATA_DIR, "pmids_pm2018.txt")
PM2020_PMIDS_FILE = os.path.join(DATA_DIR, "pmids_pm2020.txt")
# DB Backend
BACKEND_CONFIG = os.path.join(CONFIG_DIR, "backend.json")
