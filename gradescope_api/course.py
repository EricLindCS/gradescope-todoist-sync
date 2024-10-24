from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict, List, Optional

from bs4 import BeautifulSoup
from gradescope_api.errors import check_response
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

    def get_assignments_list(self) -> List[GradescopeAssignment]:
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

                a_client = self._client
                a_course = self
                a_assignment_name = None
                a_url = None
                a_status = None
                a_released_date = None
                a_due_date = None
                a_late_due_date = None
                
                # Extract assignment name
                name_cell = row.find("th", {"class": "table--primaryLink"})

                if name_cell is not None:

                    assignment_name = name_cell.get_text(strip=True)
            
                    if(name_cell.find("a") is not None):

                        a_url = name_cell.find("a")["href"]

                        a_assignment_name = assignment_name
                        
                        status_cell = row.find("td", {"class": "submissionStatus"})
                        a_status = status_cell.get_text(strip=True)
                 
                        if(row.find("div", {"class": "submissionTimeChart submissionTimeChart-neutral"}) is not None):
                            time_details = row.find("div", {"class": "submissionTimeChart submissionTimeChart-neutral"})

                            if time_details is not None:
                                opened_date = time_details.find('time', {'class': 'submissionTimeChart--releaseDate'}).get('datetime')
                                due_date = time_details.find_all('time', {'class': 'submissionTimeChart--dueDate'})[0].get('datetime')
                                late_due_date = time_details.find_all('time', {'class': 'submissionTimeChart--dueDate'})[1].get('datetime')

                                a_released_date = opened_date
                                a_due_date = due_date
                                a_late_due_date = late_due_date
                            else:
                                a_released_date = None
                                a_due_date = None
                                a_late_due_date = None
                            
                        else:
                            time_details = row.find("div", {"class": "progressBar--caption"})

                            if time_details is not None:
                                opened_date = time_details.find('time', {'class': 'submissionTimeChart--releaseDate'}).get('datetime')
                                due_date = time_details.find_all('time', {'class': 'submissionTimeChart--dueDate'})[0].get('datetime')
                                if(len(time_details.find_all('time', {'class': 'submissionTimeChart--dueDate'}))> 1):
                                    late_due_date = time_details.find_all('time', {'class': 'submissionTimeChart--dueDate'})[1].get('datetime')
                                else:
                                    late_due_date = None

                                a_released_date = opened_date
                                a_due_date = due_date
                                a_late_due_date = late_due_date

                            else:
                                a_released_date = None
                                a_due_date = None
                                a_late_due_date = None
                    
                    else:

                        try:
                            a_url = name_cell.find("button")["data-post-url"]
                        except:
                            #Temp soltuion for quiz 8
                            print("AAAAA")
                            continue
                            a_url = ""

                        a_assignment_name = assignment_name
                        #a_url = f"https://www.gradescope.com{a_url}"

                        # Extract status
                        status_cell = row.find("td", {"class": "submissionStatus"})
                        a_status = status_cell.get_text(strip=True) if status_cell else "Unknown"

                        # Extract due date and other time-related information
                        time_details = row.find("div", {"class": "submissionTimeChart"})
                        if time_details is not None:

                            release_time = time_details.find('time', {"class": "submissionTimeChart--releaseDate"})
                            due_time = time_details.find('time', {"class": "submissionTimeChart--dueDate"})

                            a_released_date = release_time.get("datetime") if release_time else None
                            a_due_date = due_time.get("datetime") if due_time else None
                            # Assign late_due_date (if available)
                            late_due_date = row.find_all('td', class_="hidden-column")
                            a_late_due_date = late_due_date[1].get_text() if len(late_due_date) > 1 else None

                        else:
                            # Handle the else case for time details
                            a_released_date = None
                            a_due_date = None
                            a_late_due_date = None

                assignments.append(GradescopeAssignment(a_client, a_course, a_assignment_name, a_url, a_status, a_released_date, a_due_date, a_late_due_date))
                        
        return assignments
