from time import time
from typing import Any, Optional
from bs4 import BeautifulSoup
import requests
from requests import Response
from gradescope_api.course import GradescopeCourse
from typing import TYPE_CHECKING, Dict, List, Optional

from gradescope_api.errors import check_response
from gradescope_api.utils import get_url_id

USER_AGENT = "gradescope-api"
BASE_URL = "https://gradescope.com"

class GradescopeClient:
    def __init__(self, email: str, password: str) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._log_in(email=email, password=password)

    def get_base_url(self) -> str:
        return BASE_URL

    def _get_token(
        self, url: str, action: Optional[Any] = None, meta: Optional[Any] = None, content: Optional[Any] = None
    ) -> str:
        """
        Return the Gradescope authenticity token.
        """
        if not content:
            response = self.session.get(url, timeout=20)
            content = response.content

        soup = BeautifulSoup(content, "html.parser")
        form = None
        if action:
            form = soup.find("form", {"action": action})
        elif meta:
            return soup.find("meta", {"name": meta})["content"]
        else:
            form = soup.find("form")

        return form.find("input", {"name": "authenticity_token"})["value"]

    def submit_form(
        self,
        url: str,
        referer_url: Optional[str] = None,
        data: Optional[Any] = None,
        files: Optional[Any] = None,
        header_token: Optional[Any] = None,
        json: Optional[Any] = None,
    ) -> Response:
        if not referer_url:
            referer_url = url
        headers = {"Host": "www.gradescope.com", "Origin": "https://www.gradescope.com", "Referer": referer_url}
        if header_token is not None:
            headers["X-CSRF-Token"] = header_token
        return self.session.post(url, data=data, json=json, files=files, headers=headers, timeout=20)

    def _log_in(self, email: str, password: str):
        url = BASE_URL + "/login"
        token = self._get_token(url)
        payload = {
            "utf8": "✓",
            "authenticity_token": token,
            "session[email]": email,
            "session[password]": password,
            "session[remember_me]": 1,
            "commit": "Log In",
            "session[remember_me_sso]": 0,
        }
        response = self.submit_form(url=url, data=payload)
        check_response(response, error="failed to log in")

    def get_course(self, course_url: Optional[str] = None, course_id: Optional[str] = None):
        course_id = course_id or get_url_id(course_url, "courses")
        return GradescopeCourse(_client=self, course_id=course_id, course_name="N/A")
    
    def get_course_list(self) -> List[GradescopeCourse]:
        """
        Fetch all assignments for the course and return a list of dictionaries containing
        the assignment's name, status, release date, due date, and late due date.
        """
        url = BASE_URL
        response = self.session.get(url=url, timeout=20)
        #check_response(response, "failed to get roster")
        
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        courses = soup.find_all('a', class_='courseBox')
        
        # Extract course names and links
        course_data = []

        if courses is not None:
            for course in courses:
                course_name = course.find('h3', class_='courseBox--shortname').text
                course_link = course['href']
                course_number = course_link.split('/')[-1]
                courseobject = GradescopeCourse(_client=self, course_id=course_number, course_name=course_name)
                course_data.append(courseobject)

        return course_data

    def get_term_list(self) -> List[str]:
        url = BASE_URL
        response = self.session.get(url=url, timeout=20)
        # check_response(response, "failed to get terms")
        
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract terms
        terms = soup.find_all('div', class_='courseList--term')
        term_list = [term.text for term in terms]

        return term_list
    
    def get_latest_term(self) -> Optional[str]:
        term_list = self.get_term_list()
        if term_list:
            return term_list[0]  # Assuming the latest term is the first in the list, CHECK LATER
        return None