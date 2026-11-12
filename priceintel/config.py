"""Project paths. Override the data folder with the PRICEINTEL_DATA_DIR environment variable."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("PRICEINTEL_DATA_DIR", REPO_ROOT / "data"))
SQL_DIR = REPO_ROOT / "sql"
CONFIG_DIR = REPO_ROOT / "config"

MARKET_DB = DATA_DIR / "market_intel.db"
MARKET_MIGRATIONS = SQL_DIR / "market_intel"
QUERIES_DIR = SQL_DIR / "queries"
SNAPSHOT_DIR = DATA_DIR.parent / "data" / "snapshots"
SHOPS_FILE = CONFIG_DIR / "shops.json"
# Versioned, price-independent category rules (ADR-006); tagged before any analysis run.
CATEGORY_RULES_FILE = CONFIG_DIR / "category_rules.v1.json"

# The collection window the Module Leader approved on 2026-11-03. One definition, used by the
# pipeline, the documentation and the scheduled workflow, so they cannot drift apart.
APPROVED_WINDOW_START = "2026-11-09"
APPROVED_WINDOW_END = "2026-12-06"

SECRET_DB = DATA_DIR / "secret_shop.db"
SECRET_MIGRATIONS = SQL_DIR / "secret_shop"
SECRET_SOURCES_FILE = CONFIG_DIR / "secret_sources.json"
