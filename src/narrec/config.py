import os

GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
RESOURCE_DIR = os.path.join(GIT_ROOT_DIR, "resources")
CONFIG_DIR = os.path.join(GIT_ROOT_DIR, "config")

RELISH_BENCHMARK_FILE = os.path.join(RESOURCE_DIR, "RELISH_v1.json.gz")


# DB Backend
BACKEND_CONFIG = os.path.join(CONFIG_DIR, "backend.json")
