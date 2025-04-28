import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from markdown import markdown

from fetch_job_postings import parse_jobs
from models import JobListing
from utils.db import db_init
from utils.helpers import format_dt, get_hn_link_comment

app = FastAPI(
    title="Who Is Hiring?",
    description="A simple web app to scrape and display job postings from Hacker News.",
    version="1.0",
)
db_init()


class SearchForm(BaseModel):
    search: str = Field(json_schema_extra={"placeholder": "Search..."})


@app.get("/health", response_class=HTMLResponse)
async def healthcheck():
    return HTMLResponse(content="""
      <html>
        <head><title>Health Check</title></head>
        <body>
          <h1>OK</h1>
        </body>
      </html>
      """)


@app.get("/", response_class=HTMLResponse)
async def users_table(
    request: Request,
    search: str | None = None,
) -> HTMLResponse:
    """
    Show a table of all jobs, returning pure HTML instead of FastUI components.
    """

    # Fetch jobs
    jobs = JobListing.get_all_jobs(search=search)

    # Build table rows
    if jobs and len(jobs) > 0:
        table_rows = ""
        for job in jobs:
            inserted_at = format_dt(job.inserted_at)
            job_html = markdown(job.job_text)
            table_rows += f"""
                <tr>
                    <td><a href="/job/{job.id}">{job.id}</a></td>
                    <td>{job_html}</td>
                    <td>{job.status}</td>
                    <td>{inserted_at}</td>
                </tr>
            """
        table_html = f"""
            <table border="1" cellpadding="5" cellspacing="0">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Job Text</th>
                        <th>Status</th>
                        <th>Inserted At</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        """
    else:
        table_html = "<p>No jobs found matching criteria.</p>"

    # Render the final HTML
    html_content = f"""
    <html>
        <head>
            <title>Job Listings</title>
        </head>
        <body>
            <h2>Jobs listings (ALL)</h2>

            <form method="get" action="/">
                <input type="text" name="search" placeholder="Search..." value="{search or ''}">
                <button type="submit">Search</button>
                <a href="/">Clear Filters</a>
            </form>

            <div style="margin-top: 20px;">
                <a href="/scrape">
                    <button type="button">Start Scraping HN Jobs</button>
                </a>
            </div>

            <div style="margin-top: 20px;">
                <p>{len(jobs) if jobs else 0} jobs match the criteria.</p>
            </div>

            <div style="margin-top: 20px;">
                {table_html}
            </div>
        </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@app.get("/job/{job_id}", response_class=HTMLResponse)
async def job_profile(job_id: int) -> HTMLResponse:
    """
    Job detail page, returning HTML directly instead of FastUI components.
    """

    try:
        job = JobListing.get_job_by_id(job_id)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Job not found")

    # Format data
    inserted_at = format_dt(job.inserted_at)
    updated_at = format_dt(job.updated_at)
    applied_at = format_dt(job.applied_at)
    hn_user_link = (
        f'<a href="/user/{job.hn_user}">{job.hn_user}</a>' if job.hn_user else "N/A"
    )
    hn_id_link = (
        f'<a href="{get_hn_link_comment(job.hn_id)}" target="_blank">{job.hn_id}</a>'
        if job.hn_id
        else "N/A"
    )

    # Render HTML
    html_content = f"""
    <html>
        <head>
            <title>Job Details</title>
        </head>
        <body>
            <h2>Job Details</h2>
            <a href="/">Back to Listings</a>
            <div style="margin-top: 20px;">
                <p><strong>Job Text:</strong></p>
                <div style="border: 1px solid #ccc; padding: 10px;">
                    {markdown(job.job_text)}
                </div>
                <p><strong>Inserted At:</strong> {inserted_at}</p>
                <p><strong>Updated At:</strong> {updated_at}</p>
                <p><strong>Applied At:</strong> {applied_at}</p>
                <p><strong>HN User:</strong> {hn_user_link}</p>
                <p><strong>HN ID:</strong> {hn_id_link}</p>
            </div>
        </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@app.get("/scrape", response_class=HTMLResponse)
async def scrape_jobs(
    request: Request, background_tasks: BackgroundTasks
) -> HTMLResponse:
    """
    Trigger scraping of jobs and allow user to manually navigate back.
    """

    try:
        background_tasks.add_task(
            parse_jobs, "https://news.ycombinator.com/item?id=43547611"
        )
        scraping_message = "Scraping started successfully! The scraping process is running in the background."
    except Exception as e:
        print(f"Error adding background task: {e}")
        scraping_message = f"Error starting scraping: {e}"

    html_content = f"""
    <html>
        <head>
            <title>Scrape Jobs</title>
        </head>
        <body>
            <h2>Scraping Status</h2>
            <p>{scraping_message}</p>

            <div style="margin-top: 20px;">
                <a href="/">
                    <button type="button">Back to Home</button>
                </a>
            </div>
        </body>
    </html>
    """

    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
