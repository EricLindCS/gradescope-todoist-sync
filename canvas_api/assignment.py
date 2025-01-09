from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from canvas_api.client import CanvasAPI
    from canvas_api.course import CanvasCourse

class CanvasAssignment:
    def __init__(self, _client: 'CanvasAPI', _course: 'CanvasCourse', assignment_id: str, assignment_name: str, due_date: Optional[str], status: bool) -> None:
        self._client = _client
        self._course = _course
        self.assignment_id = assignment_id
        self.assignment_name = assignment_name
        self.due_date = due_date
        self.status = status
        self.url = ""