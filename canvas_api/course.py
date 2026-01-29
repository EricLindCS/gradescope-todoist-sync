from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional
import re
import requests
from canvas_api.assignment import CanvasAssignment


if TYPE_CHECKING:
    from canvas_api.client import CanvasAPI
    
class CanvasCourse:
    def __init__(self, _client: CanvasAPI, course_id: str, course_name: str, term: Optional[str] = None) -> None:
        self._client = _client
        self.course_id = course_id
        self.course_name = course_name
        self.term = term

    def get_term(self) -> Optional[str]:
        if self.term:
            return self.term
        return "Not Found"

    def get_url(self) -> str:
        print("foo")

    def get_assignments_list(self) -> List[CanvasAssignment]:
    
        endpoint = f"{self._client.base_url}/courses/{self.course_id}/assignments"
        params = {
        'include[]': 'submission'
        }
        try:
            response = self._client.session.get(endpoint, headers=self._client.headers, params=params)
            response.raise_for_status()
            assignments = response.json()
            canvas_assignments = []
            
            for assignment in assignments:
                assignment_id = assignment['id']
                assignment_name = assignment['name']
                submission = assignment.get('submission')
                assignment_status = "No Submission" if submission is None or submission['workflow_state'] == "unsubmitted" or submission['submitted_at'] is None or submission['submission_type'] is None else True
                due_date = assignment.get('due_at')
                canvas_assignment = CanvasAssignment(self._client, self, assignment_id, assignment_name, due_date, assignment_status)
                canvas_assignments.append(canvas_assignment)

            return canvas_assignments

        except requests.exceptions.RequestException as e:
            print(f"Error fetching assignments for course {self.course_id}: {e}")
            return []