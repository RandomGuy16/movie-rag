import os
import dotenv
from pathlib import Path


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