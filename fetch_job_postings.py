import logging
import argparse

import numpy as np
import requests
from bs4 import BeautifulSoup
from typing import Tuple, Optional
import html

from utils.db import backup_db_file, db_init, db_connect
from utils.embedding_model import model
from utils.helpers import is_hacker_news_url

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def load_url(url: str, session: Optional[requests.Session] = None) -> str:
    """Load the content of a URL using an optional session for reuse."""
    session = session or requests.Session()
    response = session.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.text


def get_all_comments(soup: BeautifulSoup):
    """Return all top-level comments (job postings) from the parsed HTML."""
    return soup.find_all("tr", class_="athing comtr")


def is_reply(item) -> bool:
    """Return True if an item is a reply (indented comment)."""
    indent = item.find("td", attrs={"indent": True})
    return bool(indent and int(indent["indent"]) > 0)


def parse_from_comment(item):
    """Parse the comment and extract the job details"""

    comment = str(item.find("div", class_="commtext"))

    user = item.find("a", class_="hnuser")
    hn_user = None
    if user:
        hn_user = user.get_text()

    span = item.find("span", class_="age")
    hn_id = None
    if span:
        url = span.find("a")
        if url:
            url = url.get("href")
            hn_id = url.split("=")[-1]

    return comment, hn_user, hn_id


def parse_jobs(url: str) -> Tuple[int, int]:
    """
    Fetch job postings from a Hacker News page and store them in the database.
    Returns a tuple of (existing_count, new_count).
    """
    try:
        if not is_hacker_news_url(url):
            logging.error("Invalid Hacker News URL: %s", url)
            return 0, 0

        # Backup and initialize database
        backup_db_file()
        db_init()

        # Fetch and parse the page
        session = requests.Session()
        page_content = load_url(url, session)
        soup = BeautifulSoup(page_content, "html.parser")

        exist_count = 0
        new_count = 0
        update_rows = []
        insert_rows = []

        # Store in database
        with db_connect() as conn:
            cursor = conn.cursor()
            for item in get_all_comments(soup):
                if is_reply(item):
                    continue
                comment, hn_user, hn_id = parse_from_comment(item)
                if not hn_id:
                    continue
                cursor.execute("SELECT 1 FROM jobs WHERE hn_id = ?", (hn_id,))
                if cursor.fetchone():
                    exist_count += 1
                    full_text = html.unescape(comment)
                    embedding = model.encode(full_text)
                    embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
                    update_rows.append((comment, embedding_blob, hn_id))
                else:
                    new_count += 1
                    full_text = html.unescape(comment)
                    embedding = model.encode(full_text)
                    embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
                    insert_rows.append((hn_id, hn_user, comment, embedding_blob))
            if update_rows:
                cursor.executemany(
                    "UPDATE jobs SET job_text = ?, embedding = ? WHERE hn_id = ?", update_rows
                )
            if insert_rows:
                cursor.executemany(
                    """
                    INSERT INTO jobs (hn_id, hn_user, job_text, inserted_at, embedding)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                    """,
                    insert_rows
                )
            conn.commit()

        logging.info("Existing jobs: %d, New jobs added: %d", exist_count, new_count)
        return exist_count, new_count
    except requests.RequestException as e:
        logging.error("Network error fetching URL %s: %s", url, e)
        return 0, 0
    except Exception as e:
        logging.error("Unexpected error in parse_jobs: %s", e, exc_info=True)
        return 0, 0


def main():
    parser = argparse.ArgumentParser(description="Fetch Hacker News job postings.")
    parser.add_argument("-u", "--url", required=True, help="Hacker News page URL")
    args = parser.parse_args()
    parse_jobs(args.url)


if __name__ == "__main__":
    main()
