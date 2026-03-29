# Listen AI - Social Listening Platform

A lightweight multi-service social listening platform with:

- Streamlit frontend dashboard
- Node.js gateway for auth and API orchestration
- Python NLP service for sentiment analysis
- Go statistics service for keyword and trend analytics
- SQLite database for post storage

## Architecture

- `frontend` (Python/Streamlit): user input and dashboard rendering
- `gateway` (Node.js): authentication and request routing/composition
- `nlp` (Python/FastAPI): sentiment detection from post text
- `stat` (Go): mentions, trends, top keywords, post retrieval
- `db` (SQLite): stored under `./data/listenai.db`

## Dataset Setup (Required)

Before starting services, make sure dataset files are ready.

1. Check the data setup guide in `data/README.md`.
2. Download the dataset (Google Drive placeholder link currently) and import it into SQLite.

## API Summary

### Gateway

- `POST /auth/login`
- `POST /api/dashboard` (Bearer token required)

### Stat

- `POST /stats`
- `GET /health`

### NLP

- `POST /sentiment`
- `GET /health`

## Run all services with Task

From project root:

```bash
task up
```

Notes:

- `task up` runs a cleanup step first, then starts `stat`, `nlp`, `gateway`, and `frontend` together.
- If `task` is not installed, install go-task first:

```bash
brew install go-task
```