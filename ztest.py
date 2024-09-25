from todoist_api_python.api import TodoistAPI
from todoist_api.project import TodoistProject
from todoist_api.task import TodoistTask
from time import time
from typing import TYPE_CHECKING, Dict, List, Optional, Any
from gradescope_api.client import GradescopeClient
from gradescope_api.course import GradescopeCourse
from dotenv import load_dotenv
from datetime import datetime

import os

load_dotenv()
TODOIST_API_STRING = os.environ.get('TODOIST_API_KEY')
api = TodoistAPI(TODOIST_API_STRING)
client = GradescopeClient(email=os.environ.get("GRADESCOPE_USER"), password=os.environ.get("GRADESCOPE_PASSWORD"))

try:
    projects = api.get_projects()
except Exception as error:
    print(error)


project_names = [project.name.lower() for project in projects]
if('berkeley' in [project.name.lower() for project in projects]):
    berkeley_project_id = next((i for i, project in enumerate(projects) if project.name.lower() == 'berkeley'), None)
    berkeley_projects = projects[berkeley_project_id]
else:
    try:
        project = api.add_project(name="Berkeley")
        berkeley_projects = project
    except Exception as error:
        print(error)

project = TodoistProject(api,berkeley_projects.id,berkeley_projects.name)

gs_assignments = [x.get_assignments_list() for x in client.get_course_list() ]
flattened_list = [item for sublist in gs_assignments for item in sublist]
gs_todo_list = [task for task in flattened_list if task.status == 'No Submission']

todoist_tasklist = project.get_tasks()

result = [obj1 for obj1 in gs_todo_list if not any(obj1.assignment_name == obj2.name for obj2 in todoist_tasklist)]

toadd = []

for task in result:
    l_id = task.url
    l_comp = (task.status != 'No Submission')
    l_str = task.url
    l_due = task.due_date
    l_name = task.assignment_name
    toadd.append(TodoistTask(l_id,l_comp, l_str, l_due, l_name))

project.add_tasks(toadd)
