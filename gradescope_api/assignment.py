from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

import pytz
from bs4 import BeautifulSoup
from dateutil.parser import parse

from gradescope_api.errors import GradescopeAPIError, check_response

if TYPE_CHECKING:
    from gradescope_api.client import GradescopeClient
    from gradescope_api.course import GradescopeCourse

class GradescopeAssignment:
    def __init__(self, _client: GradescopeClient, _course: GradescopeCourse, assignment_name: str, url: str, status: str, released_date:str, due_date: str, late_due_date: str) -> None:
        self._client = _client
        self._course = _course
        self.assignment_name = assignment_name
        self.url = url
        self.status = status
        self.released_date = released_date
        self.due_date = due_date
        self.late_due_date = late_due_date

    def get_url(self) -> str:
        return self._course.get_url() + f"/assignments/{self.assignment_id}"
