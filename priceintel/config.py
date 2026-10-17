"""Project paths. Override the data folder with the PRICEINTEL_DATA_DIR environment variable."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("PRICEINTEL_DATA_DIR", REPO_ROOT / "data"))
SQL_DIR = REPO_ROOT / "sql"
CONFIG_DIR = REPO_ROOT / "config"

MARKET_DB = DATA_DIR / "market_intel.db"
MARKET_MIGRATIONS = SQL_DIR / "market_intel"
SHOPS_FILE = CONFIG_DIR / "shops.json"

SECRET_DB = DATA_DIR / "secret_shop.db"
SECRET_MIGRATIONS = SQL_DIR / "secret_shop"
SECRET_SOURCES_FILE = CONFIG_DIR / "secret_sources.json"
