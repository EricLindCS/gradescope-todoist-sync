from todoist_api.task import TodoistTask
import requests
from requests import Response
from todoist_api_python.api import TodoistAPI
from typing import TYPE_CHECKING, Dict, List, Optional

class TodoistProject:
    def __init__(self, _client: TodoistAPI, project_id: str, name: str) -> None:
        self.p_id = project_id
        self.name = name
        self.client = _client
    
    def get_tasks(self) -> List[TodoistTask]:

        try:
            tasks = self.client.get_tasks(project_id=self.p_id)
        except Exception as error:
            print(error)
            return []
        
        tasklist = []
        
        for task in tasks:
            t_id = task.id
            t_is_completed = task.is_completed
            t_description = task.description
            t_due = "Tomorrow" #REPLACE REPLACE REPLACE
            t_name = task.content
            
            tasklist.append(TodoistTask(t_id,t_is_completed,t_description,t_due,t_name))

        return tasklist
    
    def add_tasks(self, tasks: List[TodoistTask]):
        for task in tasks:
            try:
                exptask = self.client.add_task(
                    project_id=self.p_id,
                    content=task.name,
                    description=task.description,
                    due_string=task.due,
                    due_lang="en",
                )
                print(exptask)
            except Exception as error:
                print(error)
    