from __future__ import annotations

import os
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from pensieve_api.course import PensieveCourse
from pensieve_api.errors import check_response, AuthError


USER_AGENT = "pensieve-api"
BASE_URL = "https://www.pensieve.co"


class PensieveClient:
    def __init__(self, session_cookie: Optional[str] = None) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        # Allow the caller to provide a cookie string or read from env var
        cookie = session_cookie or os.environ.get("PENSIEVE_COOKIE")
        if not cookie:
            raise AuthError("Pensieve requires a Google-authenticated session cookie. Set PENSIEVE_COOKIE env var or pass session_cookie to PensieveClient.")

        # Add cookie header to session
        self.session.headers.update({"Cookie": cookie})

    def get_base_url(self) -> str:
        return BASE_URL + "/student"

    def get_course(self, course_url: Optional[str] = None, course_id: Optional[str] = None) -> PensieveCourse:
        if course_url:
            # derive id from url path
            course_id = course_url.rstrip("/").split("/")[-1]
            base_path = "/" + "/".join(course_url.split("/student")[-1].lstrip("/").split("/"))
            return PensieveCourse(_client=self, course_id=course_id, course_name=course_id, base_path=base_path)
        if course_id:
            return PensieveCourse(_client=self, course_id=course_id, course_name=course_id)
        raise ValueError("Either course_url or course_id must be provided")

    def get_course_list(self) -> List[PensieveCourse]:
        # Try to list classes from the student's classes page
        url = self.get_base_url()
        response = self.session.get(url=url, timeout=20)
        check_response(response, "failed to get classes list")

        soup = BeautifulSoup(response.content, "html.parser")
        print(soup.prettify())
        courses = []

        # Look for links to /student/classes/<id>
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/student/classes/" in href:
                # extract id from href
                try:
                    cid = href.rstrip("/").split("/student/classes/")[-1].split("/")[0]
                except Exception:
                    continue
                name = a.get_text(strip=True) or cid
                # Ensure we don't add duplicates
                if not any(c.course_id == cid for c in courses):
                    base_path = "/" + "/".join(href.split("/student")[-1].lstrip("/").split("/"))
                    courses.append(PensieveCourse(self, cid, name, base_path=base_path))

        return courses
