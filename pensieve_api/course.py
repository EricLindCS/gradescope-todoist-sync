from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from bs4 import BeautifulSoup
from pensieve_api.assignment import PensieveAssignment
from pensieve_api.errors import check_response

if TYPE_CHECKING:
    from pensieve_api.client import PensieveClient


class PensieveCourse:
    def __init__(self, _client: "PensieveClient", course_id: str, course_name: str, base_path: Optional[str] = None) -> None:
        self._client = _client
        self.course_id = course_id
        self.course_name = course_name
        # optional path fragment discovered when listing courses
        self.base_path = base_path or f"/student/classes/{course_id}"

    def get_term(self) -> Optional[str]:
        url = self._client.get_base_url() + self.base_path
        response = self._client.session.get(url=url, timeout=20)
        check_response(response, "failed to get course page")

        soup = BeautifulSoup(response.content, "html.parser")
        # Try to find a term in the header; fallback to None
        header = soup.find(lambda tag: tag.name in ["h1", "h2", "h3"] and "term" in (tag.get("class") or []))
        if header:
            return header.get_text(strip=True)
        # Fallback: attempt to parse any element containing 'SP' or 'Fall' etc.
        text = soup.get_text(separator=" ")
        for token in ("Spring", "Fall", "Summer", "Winter", "SP", "FA", "SU", "WI"):
            if token in text:
                # crude extraction; callers should verify
                return token
        return None

    def get_url(self) -> str:
        return self._client.get_base_url() + self.base_path

    def get_assignments_list(self) -> List[PensieveAssignment]:
        # Pensieve shows student assignments at a path like /student/classes/<id>/my-assignments
        assignments_path = self.base_path.rstrip("/") + "/my-assignments"
        url = self._client.get_base_url() + assignments_path
        response = self._client.session.get(url=url, timeout=20)
        check_response(response, "failed to get assignments")

        soup = BeautifulSoup(response.content, "html.parser")

        # Attempt a few strategies to find assignment rows
        results = []

        # Strategy 1: look for elements with class containing 'assignment'
        candidates = soup.find_all(class_=lambda c: c and "assign" in c.lower())

        # Strategy 2 fallback: any table row or list item that contains the word 'Due'
        if not candidates:
            candidates = soup.find_all(["tr", "li", "div"], string=lambda s: s and "Due" in s)

        seen = set()
        for cand in candidates:
            # Walk up to a parent that likely contains a name + due info
            container = cand
            # try to extract link + name
            link = container.find("a")
            if link:
                name = link.get_text(strip=True)
                href = link.get("href")
                url = href if href.startswith("http") else self._client.get_base_url() + href
            else:
                # fallback: text of the container
                name = container.get_text(" ", strip=True)
                url = self.get_url()

            # crude check for due date
            due = None
            time_tag = container.find("time")
            if time_tag and time_tag.get("datetime"):
                due = time_tag.get("datetime")

            # Avoid duplicates
            key = (name, due)
            if key in seen or not name:
                continue
            seen.add(key)

            # Status is unknown for Pensieve at this level
            results.append(PensieveAssignment(self._client, self, name, url, status="Unknown", released_date=None, due_date=due, late_due_date=None))

        return results
