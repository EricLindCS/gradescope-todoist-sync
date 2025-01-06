from todoist_api.section import TodoistSection
class TodoistTask:
    def __init__(self, id: str, is_completed: bool, description: str, due:str, name:str, section: TodoistSection = None) -> None:
        self.id = id
        self.is_completed = is_completed
        self.description = description
        self.due = due
        self.name = name
        self.section = section

