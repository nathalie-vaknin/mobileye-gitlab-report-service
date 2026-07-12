"""Task 3: HTTP layer over reports.py"""

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from gitlab_client import GitLabConfigError, GitLabAuthError, GitLabPermissionError, GitLabNotFoundError, GitLabUpstreamError
from reports import get_issues_by_year, get_merge_requests_by_year, InvalidYearError

app = FastAPI(
    title="GitLab Yearly Report Service",
    description="Read-only reporting service for GitLab issues and merge requests, grouped by year.",
)


@app.exception_handler(InvalidYearError)
async def invalid_year_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(GitLabConfigError)
async def config_error_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(GitLabAuthError)
async def auth_error_handler(request, exc):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(GitLabPermissionError)
async def permission_error_handler(request, exc):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(GitLabNotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(GitLabUpstreamError)
async def upstream_error_handler(request, exc):
    return JSONResponse(status_code=504, content={"detail": str(exc)})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/issues")
async def issues(
    year: str | None = Query(None, description="4-digit year, e.g. 2025"),
    project: str | None = Query(None, description="Project ID or URL-encoded path"),
):
    if year is None:
        raise InvalidYearError("year query parameter is required")

    result = get_issues_by_year(year, project)
    return {"year": year, "project": project, "count": len(result), "issues": result}


@app.get("/merge-requests")
async def merge_requests(
    year: str | None = Query(None, description="4-digit year, e.g. 2025"),
    project: str | None = Query(None, description="Project ID or URL-encoded path"),
):
    if year is None:
        raise InvalidYearError("year query parameter is required")

    result = get_merge_requests_by_year(year, project)
    return {"year": year, "project": project, "count": len(result), "merge_requests": result}