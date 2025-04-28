import sqlite3
from datetime import datetime
from pathlib import Path
import shutil
from functools import lru_cache


@lru_cache(maxsize=1)
def get_db_path() -> Path:
    """
    Get the path to the SQLite database.
    """
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "data" / "hn_jobs.db"


# Ensure data directory exists
db_file = get_db_path()
db_file.parent.mkdir(parents=True, exist_ok=True)


def backup_db_file(backup_dir: "Optional[Path]" = None) -> str:
    """
    Backup the SQLite database file.
    """
    db_path = get_db_path()
    if backup_dir is None:
        backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{db_path.name}_{timestamp}.bak"

    if db_path.exists():
        shutil.copy(db_path, backup_path)
        return f"Database backup created at {backup_path}"
    return "No database to backup"


def db_connect() -> sqlite3.Connection:
    """
    Connect to the SQLite database with optimized pragma settings.
    """
    conn = sqlite3.connect(
        get_db_path(),
        timeout=30,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    conn.row_factory = sqlite3.Row
    # PRAGMA settings
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def db_init() -> str:
    """
    Initialize the SQLite database.
    """
    db_path = get_db_path()
    if db_path.exists():
        return "Database already exists"

    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hn_id INTEGER UNIQUE,
                hn_user TEXT,
                job_text TEXT NOT NULL,
                inserted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                applied_at TIMESTAMP,
                status TEXT,
                embedding BLOB
            )
            """
        )
        conn.commit()

    return "Database created"
