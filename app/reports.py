"""Task 1 & 2: get_issues_by_year / get_merge_requests_by_year"""

import re

from gitlab_client import GitLabClient

YEAR_PATTERN = re.compile(r"^\d{4}$")


class InvalidYearError(ValueError):
    pass


def _validate_year(year) -> int:
    year_str = str(year)
    if not YEAR_PATTERN.match(year_str):
        raise InvalidYearError(f"'{year}' is not a valid 4-digit year")

    year_int = int(year_str)
    if year_int < 2000 or year_int > 2100:
        raise InvalidYearError(f"'{year}' is outside the supported year range")

    return year_int


def _year_bounds(year: int) -> tuple[str, str]:
    # created_before = Jan 1 of next year, avoids edge cases at Dec 31 23:59:59
    start = f"{year}-01-01T00:00:00Z"
    end = f"{year + 1}-01-01T00:00:00Z"
    return start, end


def get_issues_by_year(year, project_id_or_path: str | None = None) -> list:
    validated_year = _validate_year(year)
    created_after, created_before = _year_bounds(validated_year)

    client = GitLabClient()
    return client.get_issues(created_after, created_before, project_id_or_path)


def get_merge_requests_by_year(year, project_id_or_path: str | None = None) -> list:
    validated_year = _validate_year(year)
    created_after, created_before = _year_bounds(validated_year)

    client = GitLabClient()
    return client.get_merge_requests(created_after, created_before, project_id_or_path)