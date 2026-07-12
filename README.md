# GitLab Yearly Report Service
A small read-only reporting service that integrates with the GitLab REST API v4
and returns issues / merge requests created in a given year - either for a
single project or across the entire GitLab instance (per token permissions).

## Architecture
app/
  gitlab_client.py      #Talks to Gitlab: auth, pagination, error mapping
  reports.py            #Task1 and Task2: get_issues_by_year or get_merge_request_by_year
  main.py               #Task3: FastAPI HTTP layer
Dockerfile              #Task4
requirements.txt

The design separates three layers:
1. **GitLab access** (gitlab_client.py) - the only file that knows about HTTP,
   auth headers, and pagination.
2. **Business logic** (reports.py) - plain functions, no web framework involved.
3. **Delivery** (main.py) - a thin HTTP adapter that calls into the business logic.

## Configuration
The service is configured entirely through environment variables:
| Variable       | Required | Description                                      |
|----------------|----------|---------------------------------------------------|
| GITLAB_URL   | Yes      | Base URL of the GitLab instance, e.g. https://gitlab.com |
| GITLAB_TOKEN | Yes      | Personal or project access token with read_api scope |
If either variable is missing, the service fails with a 500 and a clear
error message on the first request (see Error Handling below).

## Running locally (without Docker)
bash
pip install -r requirements.txt
export GITLAB_URL="https://gitlab.com"
export GITLAB_TOKEN="glpat-xxxxxxxxxxxx"
cd app
uvicorn main:app --host 0.0.0.0 --port 8080

## Running with Docker
bash
docker build -t gitlab_yrs .
docker run --rm -p 8080:8080 \
  -e GITLAB_URL="https://gitlab.com" \
  -e GITLAB_TOKEN="glpat-xxxxxxxxxxxx" \
  gitlab_yrs

The service is then available at http://localhost:8080.

## API Reference

### GET /health
bash
curl http://localhost:8080/health
# {"status":"ok"}

### GET /issues?year=2026
All issues created in 2026 across the whole instance (per token permissions):
bash
curl "http://localhost:8080/issues?year=2026"

### GET /issues?year=2026&project=mygroup%2Fmy-project
Issues created in 2026 for a single project (note the path is URL-encoded,
/ becomes %2F):
bash
curl "http://localhost:8080/issues?year=2026&project=mygroup%2Fmy-project"

A numeric project ID also works:
bash
curl "http://localhost:8080/issues?year=2026&project=123"

### GET /merge-requests?year=2026[&project=...]
Same pattern as /issues:
bash
curl "http://localhost:8080/merge-requests?year=2026&project=mygroup%2Fmy-project"

> **Note:** querying merge requests / issues across the *entire* gitlab.com
> instance (no project filter) can be slow or time out, since gitlab.com is
> a massive public instance. Against a real company GitLab instance (fewer
> projects) this is expected to work well. If GitLab itself times out, the
> service returns 504 Gateway Timeout.

## Error Handling
| Scenario                   | Status | Verified |
|----------------------------|--------|----------|
| Missing year             | 400    | ✅ |
| Invalid year format        | 400    | ✅ |
| GITLAB_TOKEN missing     | 500    | ✅ |
| GitLab project not found   | 404    | ✅ |
| GitLab authentication failed | 401  | ✅ |
| GitLab permission denied   | 403    | - |
| GitLab upstream timeout    | 504    | ✅ |
Example:
bash
curl "http://localhost:8080/issues?year=abcd"
# 400 {"detail":"'abcd' is not a valid 4-digit year"}

## Testing
Tested manually against a real GitLab.com project
(nataly_vaknin-group/nataly_vaknin-project) with real issues and a real
merge request, using a Personal Access Token with read_api scope.
