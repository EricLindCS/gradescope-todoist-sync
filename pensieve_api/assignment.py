from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pensieve_api.client import PensieveClient
    from pensieve_api.course import PensieveCourse


class PensieveAssignment:
    def __init__(self, _client: "PensieveClient", _course: "PensieveCourse", assignment_name: str, url: str, status: Optional[str] = None, released_date: Optional[str] = None, due_date: Optional[str] = None, late_due_date: Optional[str] = None) -> None:
        self._client = _client
        self._course = _course
        self.assignment_name = assignment_name
        self.url = url
        self.status = status or ""
        self.released_date = released_date
        self.due_date = due_date
        self.late_due_date = late_due_date

    def get_url(self) -> str:
        return self.url

    def __repr__(self) -> str:  # helpful when debugging
        return f"PensieveAssignment(name={self.assignment_name!r}, due={self.due_date!r})"
