import os

GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
RESOURCE_DIR = os.path.join(GIT_ROOT_DIR, "resources")
CONFIG_DIR = os.path.join(GIT_ROOT_DIR, "config")

BENCHMARK_DIR = os.path.join(RESOURCE_DIR, "benchmarks")

RELISH_BENCHMARK_JSON_FILE = os.path.join(BENCHMARK_DIR, "RELISH_v1.json")
RELISH_BENCHMARK_FILE = os.path.join(BENCHMARK_DIR, "RELISH_documents.txt")
PM2020_BENCHMARK_FILE = os.path.join(BENCHMARK_DIR, "trec_pm2020_documents.txt")
PM2020_TOPIC_FILE = os.path.join(BENCHMARK_DIR, "trec_pm2020_topics.xml")

PMIDS_DIR = os.path.join(RESOURCE_DIR, "pmids")

RELISH_PMIDS_FILE = os.path.join(PMIDS_DIR, "pmids_pm2018.txt")
TG2005_PMIDS_FILE = os.path.join(PMIDS_DIR, "pmids_tg2005.txt")
# DB Backend
BACKEND_CONFIG = os.path.join(CONFIG_DIR, "backend.json")
