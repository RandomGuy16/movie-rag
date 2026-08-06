import os
import sys
import zipfile
from pathlib import Path

from app.core.config import PROJECT_ROOT


DATASET_NAME = "tmdb/tmdb-movie-metadata"
TARGET_DIR = PROJECT_ROOT / "raw"
TARGET_FILE = TARGET_DIR / "tmdb_5000_movies.csv"

KAGGLE_DIR = Path.home() / ".kaggle"
KAGGLE_JSON = KAGGLE_DIR / "kaggle.json"
ACCESS_TOKEN_FILE = KAGGLE_DIR / "access_token"


def detect_credentials() -> str | None:
    """Return a description of the auth source, or None if no credentials are found.

    Order of precedence:
      1. KAGGLE_API_TOKEN env var (single-token API, replaces username+key)
      2. ~/.kaggle/access_token file (single-token API)
      3. KAGGLE_USERNAME + KAGGLE_KEY env vars (legacy username+key)
      4. ~/.kaggle/kaggle.json file (legacy username+key)
    """
    if os.getenv("KAGGLE_API_TOKEN"):
        return "env KAGGLE_API_TOKEN"
    if ACCESS_TOKEN_FILE.exists():
        return f"file {ACCESS_TOKEN_FILE}"
    if os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"):
        return "env KAGGLE_USERNAME + KAGGLE_KEY"
    if KAGGLE_JSON.exists():
        return f"file {KAGGLE_JSON}"
    return None


def fetch_dataset() -> None:
    """Download the TMDB 5000 movies CSV from Kaggle into back/raw/."""
    creds = detect_credentials()
    if creds is None:
        print("ERROR: no Kaggle credentials found.")
        print("Set up one of:")
        print("  - ~/.kaggle/access_token (new single-token API)")
        print("  - KAGGLE_API_TOKEN env var")
        print("  - ~/.kaggle/kaggle.json (legacy username + key)")
        print("Generate a token at https://www.kaggle.com/settings/account")
        sys.exit(1)
    print(f"Using Kaggle credentials from {creds}")

    # The kaggle package reads kaggle.json on import; fix perms if it exists.
    if KAGGLE_JSON.exists():
        os.chmod(KAGGLE_JSON, 0o600)
    if ACCESS_TOKEN_FILE.exists():
        os.chmod(ACCESS_TOKEN_FILE, 0o600)

    try:
        import kaggle
    except ImportError:
        print("ERROR: the 'kaggle' package is not installed.")
        print("Install it with: uv add kaggle")
        sys.exit(1)

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    if TARGET_FILE.exists():
        print(f"Already present at {TARGET_FILE}, skipping download.")
        return

    print(f"Downloading {DATASET_NAME} from Kaggle to {TARGET_DIR}...")
    zip_path = TARGET_DIR / "tmdb-movie-metadata.zip"
    kaggle.api.dataset_download_files(DATASET_NAME, path=TARGET_DIR, quiet=False)

    zip_candidates = list(TARGET_DIR.glob("*.zip"))
    if zip_candidates:
        with zipfile.ZipFile(zip_candidates[0]) as zf:
            zf.extractall(TARGET_DIR)
        zip_candidates[0].unlink()

    if not TARGET_FILE.exists():
        print(f"ERROR: expected {TARGET_FILE} not found after extraction.")
        print(f"Contents of {TARGET_DIR}:")
        for p in TARGET_DIR.iterdir():
            print(f"  {p.name}")
        sys.exit(1)

    print(f"Downloaded {TARGET_FILE} ({TARGET_FILE.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    fetch_dataset()
