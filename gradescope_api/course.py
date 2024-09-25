from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict, List, Optional

from bs4 import BeautifulSoup
from gradescope_api.errors import check_response
from gradescope_api.student import GradescopeStudent
from gradescope_api.assignment import GradescopeAssignment
from gradescope_api.utils import get_url_id

if TYPE_CHECKING:
    from gradescope_api.client import GradescopeClient


class GradescopeCourse:
    def __init__(self, _client: GradescopeClient, course_id: str) -> None:
        self._client = _client
        self.course_id = course_id
        self.roster: List[GradescopeStudent] = []

    def get_url(self) -> str:
        return self._client.get_base_url() + f"/courses/{self.course_id}"

    def get_roster(self) -> List[GradescopeStudent]:
        if self.roster:
            return self.roster

        url = self._client.get_base_url() + f"/courses/{self.course_id}/memberships"
        response = self._client.session.get(url=url, timeout=20)
        check_response(response, "failed to get roster")

        soup = BeautifulSoup(response.content, "html.parser")
        for row in soup.find_all("tr", class_="rosterRow"):
            nameButton = row.find("button", class_="js-rosterName")
            role = row.find("option", selected=True).text
            if nameButton and role == "Student":
                user_id = nameButton["data-url"].split("?user_id=")[1]
                editButton = row.find("button", class_="rosterCell--editIcon")
                if editButton:
                    data_email = editButton["data-email"]
                    data_cm: Dict = json.loads(editButton["data-cm"])
                    self.roster.append(
                        GradescopeStudent(
                            _client=self._client,
                            user_id=user_id,
                            full_name=data_cm.get("full_name"),
                            first_name=data_cm.get("first_name"),
                            last_name=data_cm.get("last_name"),
                            sid=data_cm.get("sid"),
                            email=data_email,
                        )
                    )

        return self.roster

    def get_student(self, sid: Optional[str] = None, email: Optional[str] = None) -> Optional[GradescopeStudent]:
        assert sid or email
        roster = self.get_roster()
        for student in roster:
            if sid != None and student.sid == sid:
                return student
            if email != None and student.email == email:
                return student
        return None

    def get_assignment(
        self, assignment_id: Optional[str] = None, assignment_url: Optional[str] = None
    ) -> Optional[GradescopeAssignment]:
        assert assignment_id or assignment_url
        assignment_id = assignment_id or get_url_id(url=assignment_url, kind="assignments")
        return GradescopeAssignment(_client=self._client, _course=self, assignment_id=assignment_id)

    def get_assignments_list(self) -> List[Dict]:
        """
        Fetch all assignments for the course and return a list of dictionaries containing
        the assignment's name, status, release date, due date, and late due date.
        """
        url = self._client.get_base_url() + f"/courses/{self.course_id}/"
        response = self._client.session.get(url=url, timeout=20)
        #check_response(response, "failed to get roster")
        
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        
        assignments_table = soup.find("table", {"id": "assignments-student-table"})
        
        # List to hold all the assignments
        assignments = []
        
        

        # Loop through the rows of the table
        for row in assignments_table.find("tbody").find_all("tr"):
            assignment = {}
            
            # Extract assignment name
            name_cell = row.find("th", {"class": "table--primaryLink"})
            assignment_name = name_cell.get_text(strip=True)
            assignment_url = name_cell.find("a")["href"]
            assignment["name"] = assignment_name
            assignment["url"] = f"https://www.gradescope.com{assignment_url}"
            
            # Extract status
            status_cell = row.find("td", {"class": "submissionStatus"})
            assignment["status"] = status_cell.get_text(strip=True)
            
            # Extract due date and other time-related information
            time_details = row.find("div", {"class": "submissionTimeChart submissionTimeChart-neutral"})

            if time_details is not None:
                opened_date = time_details.find('time', {'class': 'submissionTimeChart--releaseDate'}).get('datetime')
                due_date = time_details.find_all('time', {'class': 'submissionTimeChart--dueDate'})[0].get('datetime')
                late_due_date = time_details.find_all('time', {'class': 'submissionTimeChart--dueDate'})[1].get('datetime')

                assignment["release_date"] = opened_date
                assignment["due_date"] = due_date
                assignment["late_due_date"] = late_due_date
            else:
                assignment["release_date"] = None
                assignment["due_date"] = None
                assignment["late_due_date"] = None

            assignments.append(assignment)
        
        return assignments
