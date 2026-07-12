"""Wrapper around the GitLab REST API v4 - auth, pagination, error mapping."""

import os
import urllib.parse
import requests


class GitLabClientError(Exception):
    pass


class GitLabAuthError(GitLabClientError):
    """Token invalid -> 401"""
    pass


class GitLabPermissionError(GitLabClientError):
    """Token valid, no permission -> 403"""
    pass


class GitLabNotFoundError(GitLabClientError):
    """Project/resource doesn't exist -> 404"""
    pass


class GitLabUpstreamError(GitLabClientError):
    """GitLab itself timed out or is unavailable -> 504"""
    pass


class GitLabConfigError(GitLabClientError):
    """Missing env vars -> 500"""
    pass


class GitLabClient:
    def __init__(self):
        self.base_url = os.environ.get("GITLAB_URL")
        self.token = os.environ.get("GITLAB_TOKEN")

        if not self.base_url or not self.token:
            raise GitLabConfigError(
                "GITLAB_URL and GITLAB_TOKEN environment variables are required"
            )

        self.base_url = self.base_url.rstrip("/")
        self.api_root = f"{self.base_url}/api/v4"

        self.session = requests.Session()
        self.session.headers.update({"PRIVATE-TOKEN": self.token})

    def _get_all_pages(self, path: str, params: dict) -> list:
        # GitLab paginates list endpoints - loop until X-Next-Page is empty,
        # otherwise we'd silently only get the first 20-100 results.
        results = []
        page = 1
        params = dict(params)
        params["per_page"] = 100

        while True:
            params["page"] = page
            url = f"{self.api_root}/{path}"
            response = self.session.get(url, params=params, timeout=30)

            self._raise_for_status(response)
            results.extend(response.json())

            next_page = response.headers.get("X-Next-Page")
            if not next_page:
                break
            page = int(next_page)

        return results

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        if response.status_code == 401:
            raise GitLabAuthError("GitLab authentication failed (invalid token)")
        if response.status_code == 403:
            raise GitLabPermissionError("GitLab permission denied for this token")
        if response.status_code == 404:
            raise GitLabNotFoundError("GitLab resource not found")
        if response.status_code in (408, 502, 503, 504):
            raise GitLabUpstreamError(
                f"GitLab upstream error ({response.status_code}) - try again or narrow the query with a project filter"
            )
        response.raise_for_status()

    @staticmethod
    def _encode_project_path(project_id_or_path: str) -> str:
        # "group/project" needs the "/" encoded as %2F or GitLab treats it as a route.
        return urllib.parse.quote(str(project_id_or_path), safe="")

    def get_issues(self, created_after: str, created_before: str,
                   project_id_or_path: str | None = None) -> list:
        params = {
            "created_after": created_after,
            "created_before": created_before,
            "scope": "all",  # default scope is "assigned to me" - not what we want
        }

        if project_id_or_path:
            encoded = self._encode_project_path(project_id_or_path)
            return self._get_all_pages(f"projects/{encoded}/issues", params)

        return self._get_all_pages("issues", params)

    def get_merge_requests(self, created_after: str, created_before: str,
                            project_id_or_path: str | None = None) -> list:
        params = {
            "created_after": created_after,
            "created_before": created_before,
            "scope": "all",
        }

        if project_id_or_path:
            encoded = self._encode_project_path(project_id_or_path)
            return self._get_all_pages(f"projects/{encoded}/merge_requests", params)

        return self._get_all_pages("merge_requests", params)