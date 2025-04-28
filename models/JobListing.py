from datetime import datetime
from typing import Optional, List

import numpy as np
from pydantic import BaseModel

from utils.db import db_connect
from utils.embedding_model import model
from utils.helpers import html_to_markdown, resolve_email

_COLUMNS = "id, hn_id, hn_user, job_text, inserted_at, updated_at, applied_at, status"


class JobModel(BaseModel):
    id: int
    hn_id: Optional[int]
    hn_user: Optional[str]
    job_text: str
    inserted_at: datetime
    updated_at: Optional[datetime]
    applied_at: Optional[datetime]
    status: Optional[str]


def get_job_by_id(job_id: int) -> Optional[JobModel]:
    """Retrieve a job by ID as a JobModel."""
    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT {_COLUMNS} FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()

    if row:
        return _format_job_model(dict(row))
    return None


def get_all_jobs(search: Optional[str] = None) -> List[JobModel]:
    """Retrieve all jobs as JobModel instances, optionally filtered by semantic search."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            if search:
                # Embed the search query
                query_vector = model.encode(search)

                # Fetch jobs with embeddings
                cursor.execute(
                    f"SELECT {_COLUMNS}, embedding FROM jobs WHERE embedding IS NOT NULL"
                )
                rows = cursor.fetchall()
                if not rows:
                    return []

                # Convert rows to dicts and extract embeddings
                job_dicts = [dict(row) for row in rows]
                embeddings = np.stack([
                    np.frombuffer(job.pop("embedding"), dtype=np.float32)
                    for job in job_dicts
                ])

                # Compute L2 distances in a vectorized manner
                distances = np.linalg.norm(embeddings - query_vector, axis=1)

                top_idx = np.argpartition(distances, 20)[:30]
                top_sorted = top_idx[np.argsort(distances[top_idx])]
                top_jobs = [job_dicts[i] for i in top_sorted]

                return [_format_job_model(job) for job in top_jobs]

            # No search: return all jobs
            cursor.execute(f"SELECT {_COLUMNS} FROM jobs")
            rows = cursor.fetchall()
            return [_format_job_model(dict(row)) for row in rows] if rows else []

    except Exception as ex:
        print(f"Error fetching jobs: {ex}")
        return []


def _format_job_model(job: dict) -> JobModel:
    """Format a row dictionary into a JobModel instance."""
    job_text = html_to_markdown(resolve_email(job.get("job_text", "")))

    inserted_at = job.get("inserted_at")
    if isinstance(inserted_at, str):
        inserted_at = datetime.fromisoformat(inserted_at)
    elif not inserted_at:
        inserted_at = datetime.now().replace(microsecond=0)
    updated_at = job.get("updated_at")
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    applied_at = job.get("applied_at")
    if isinstance(applied_at, str):
        applied_at = datetime.fromisoformat(applied_at)

    return JobModel(
        id=job.get("id", 0),
        hn_id=job.get("hn_id"),
        hn_user=job.get("hn_user"),
        job_text=job_text,
        inserted_at=inserted_at,
        updated_at=updated_at,
        applied_at=applied_at,
        status=job.get("status", "n/a"),
    )
