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
    def __init__(self, _client: GradescopeClient, course_id: str, course_name: str) -> None:
        self._client = _client
        self.course_id = course_id
        self.course_name = course_name

    def get_url(self) -> str:
        return self._client.get_base_url() + f"/courses/{self.course_id}"

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
        
        tablerows = assignments_table.find("tbody").find_all("tr")

        if tablerows is not None:

            for row in assignments_table.find("tbody").find_all("tr"):

                assignment = {}
                
                # Extract assignment name
                name_cell = row.find("th", {"class": "table--primaryLink"})

                if name_cell is not None:

                    assignment_name = name_cell.get_text(strip=True)
            
                    if(name_cell.find("a") is not None):

                        assignment_url = name_cell.find("a")["href"]

                        assignment["name"] = assignment_name
                        assignment["url"] = f"https://www.gradescope.com{assignment_url}"
                        
                        # Extract status
                        status_cell = row.find("td", {"class": "submissionStatus"})
                        assignment["status"] = status_cell.get_text(strip=True)
                        #print(row)
                        #print()
                        # Extract due date and other time-related information
                        if(row.find("div", {"class": "submissionTimeChart submissionTimeChart-neutral"}) is not None):
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

                            #print("Sub", assignment_name, assignment["due_date"], name_cell)

                            assignments.append(assignment)
                        else:
                            time_details = row.find("div", {"class": "progressBar--caption"})

                            if time_details is not None:
                                opened_date = time_details.find('time', {'class': 'submissionTimeChart--releaseDate'}).get('datetime')
                                due_date = time_details.find_all('time', {'class': 'submissionTimeChart--dueDate'})[0].get('datetime')
                                if(len(time_details.find_all('time', {'class': 'submissionTimeChart--dueDate'}))> 1):
                                    late_due_date = time_details.find_all('time', {'class': 'submissionTimeChart--dueDate'})[1].get('datetime')
                                else:
                                    late_due_date = None

                                assignment["release_date"] = opened_date
                                assignment["due_date"] = due_date
                                assignment["late_due_date"] = late_due_date

                            else:
                                assignment["release_date"] = None
                                assignment["due_date"] = None
                                assignment["late_due_date"] = None

                            #print("Sub", assignment_name, assignment["due_date"], name_cell)

                            assignments.append(assignment)
                    
                    else:

                        # Else case: when there's a button for submission
                        assignment_url = name_cell.find("button")["data-post-url"]
                        assignment["name"] = assignment_name
                        assignment["url"] = f"https://www.gradescope.com{assignment_url}"

                        # Extract status
                        status_cell = row.find("td", {"class": "submissionStatus"})
                        assignment["status"] = status_cell.get_text(strip=True) if status_cell else "Unknown"

                        # Extract due date and other time-related information
                        time_details = row.find("div", {"class": "submissionTimeChart"})
                        if time_details is not None:
                            release_time = time_details.find('time', {"class": "submissionTimeChart--releaseDate"})
                            due_time = time_details.find('time', {"class": "submissionTimeChart--dueDate"})

                            assignment["release_date"] = release_time.get("datetime") if release_time else None
                            assignment["due_date"] = due_time.get("datetime") if due_time else None
                            # Assign late_due_date (if available)
                            late_due_date = row.find_all('td', class_="hidden-column")
                            assignment["late_due_date"] = late_due_date[1].get_text() if len(late_due_date) > 1 else None

                        else:
                            # Handle the else case for time details
                            assignment["release_date"] = None
                            assignment["due_date"] = None
                            assignment["late_due_date"] = None

                        assignments.append(assignment)
                        
                        #print("NoSub", assignment_name, assignment["due_date"], name_cell)

        return assignments
