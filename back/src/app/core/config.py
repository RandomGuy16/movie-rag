import dotenv
from pathlib import Path
from sqlalchemy import URL
from sqlalchemy.engine.url import make_url


# package dir
PACKAGE_DIR = Path(__file__).resolve()


# this function finds the project root
def find_project_root(start: Path) -> Path:
    """Walk up until we find pyproject.toml"""
    for p in (start, *start.parents):
        if (p / "pyproject.toml").exists() or (p / "requirements.txt").exists():
            return p
    return start


PROJECT_ROOT = find_project_root(PACKAGE_DIR)
SRC_DIR = PROJECT_ROOT / "src"
WEB_DIR = PROJECT_ROOT / "web"
DOTENV_PATH = PROJECT_ROOT / ".env"

dotenv.load_dotenv(DOTENV_PATH)

GEMINI_API_KEY = dotenv.get_key(dotenv_path=DOTENV_PATH, key_to_get="GEMINI_API_KEY")
HUGGING_FACE_API_KEY = dotenv.get_key(dotenv_path=DOTENV_PATH, key_to_get="HUGGING_FACE_API_KEY")
DATABASE_URL = dotenv.get_key(dotenv_path=DOTENV_PATH, key_to_get="DATABASE_URL")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
HUGGING_FACE_API_URL = f"https://router.huggingface.co/hf-inference/models/{EMBEDDING_MODEL}/pipeline/feature-extraction"


def _normalize_db_url(raw: str | None) -> URL | None:
    """Build an async-friendly SQLAlchemy URL from an arbitrary .env value.

    Accepts any of: ``postgresql://``, ``postgres://``, ``postgresql+psycopg://``,
    ``postgresql+asyncpg://``. Always returns a URL object pinned to the
    ``psycopg`` driver for the async engine (DBAPI = psycopg v3), since
    psycopg2 is not installed and ``create_async_engine`` defaults to it
    when no driver is specified in the URL.
    """
    if not raw:
        return None

    parsed = make_url(raw)
    # Normalize ``postgres://`` (Heroku-style) to ``postgresql://`` first.
    if parsed.drivername == "postgres":
        parsed = parsed.set(drivername="postgresql")

    # If the URL already names a driver, respect it.
    if "+" in parsed.drivername:
        return parsed

    return parsed.set(drivername="postgresql+psycopg")


DATABASE_URL = _normalize_db_url(DATABASE_URL)