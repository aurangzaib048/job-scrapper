# Job Scraper

A web application that scrapes and displays job postings from Hacker News "Who is hiring?" threads with semantic search capabilities.


Key features include:
- Automatic scraping of job postings from Hacker News
- Semantic search using embeddings for more intelligent matching
- Email deobfuscation to make contact information more readable
- Simple and clean web interface

## Installation

### Prerequisites

- Python 3.12 or higher

### Setup

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Web Application

Start the web server:
```
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then open your browser and navigate to `http://localhost:8000` to access the application.

### Scraping Job Postings

You can scrape job postings in two ways:

1. Through the web interface:
   - Click the "Start Scraping HN Jobs" button on the home page

2. Using the command line:
   ```
   python -m src.fetch_job_postings --url <hacker-news-thread-url>
   ```
   
   Example:
   ```
   python -m src.fetch_job_postings --url https://news.ycombinator.com/item?id=43547611
   ```

### Searching for Jobs

The application provides a search box on the main page. Enter your search terms and click "Search" to find relevant job postings. 
The search uses semantic matching, so it will find jobs that are conceptually related to your search terms, even if they don't contain the exact words.

## Features

### Semantic Search

The application uses the SentenceTransformer model to convert job postings and search queries into vector embeddings, allowing for semantic search that understands the meaning behind your search terms rather than just matching keywords.

### Email Deobfuscation

Many job postings on Hacker News contain obfuscated email addresses to prevent scraping (e.g., "name dot domain at domain"). The application automatically deobfuscates these email addresses to make them more readable.


## Project Structure

```
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── main.py                     # Main FastAPI application
├── fetch_job_postings.py       # Script for scraping job postings
├── data/                       # Database and backups
├── models/                     # Data models
│   └── JobListing.py           # Job listing model
└── utils/                      # Utility functions
    ├── db.py                   # Database utilities
    ├── embedding_model.py      # Semantic search model
    ├── helpers.py              # Helper functions
    └── cache.py                # Caching utilities
```

### API Endpoints

| Method | Path                       | Description                                                                            |
| ------ |----------------------------|----------------------------------------------------------------------------------------|
| GET    | `/`                        | Serves the main web interface (HTML) with job listings and a search box.               |
| GET    | `/scrape` | Triggers scraping of the specified Hacker News updates the database.                   |
| GET    | `/search?search=<term>`    | Performs a semantic search and returns job postings semantically related to the search term. |
| GET    | `/jobs/{hn_id}`            | Retrieves details of a single job posting by its ID.                                   |
| GET    | `/docs`                    | Serves the interactive API documentation (Swagger UI and ReDoc) for exploring and testing the API. |


#### Example Usage
- **Trigger scraping via API:**
  ```bash
  curl "http://localhost:8000/api/scrape?url=https://news.ycombinator.com/item?id=43547611"
  ```
- **Search for jobs by keyword:**
  ```bash
  curl "http://localhost:8000/api/search?search=python backend"
  ```


## Technologies Used

- [FastAPI](https://fastapi.tiangolo.com/): Web framework for building the API
- [Pydantic](https://pydantic-docs.helpmanual.io/): Data validation and settings management
- [SQLite](https://www.sqlite.org/): Database for storing job listings
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/): HTML parsing for scraping
- [SentenceTransformers](https://www.sbert.net/): Neural network model for semantic search
- [html2text](https://github.com/Alir3z4/html2text): Converting HTML to Markdown
- [NumPy](https://numpy.org/): Scientific computing for vector operations
