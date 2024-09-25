from todoist_api_python.api import TodoistAPI
from project import TodoistProject
from task import TodoistTask
from time import time
from typing import Any, Optional
from typing import TYPE_CHECKING, Dict, List, Optional



from dotenv import load_dotenv

import os

load_dotenv()
TODOIST_API_STRING = os.environ.get('TODOIST_API_KEY')
api = TodoistAPI(TODOIST_API_STRING)

try:
    projects = api.get_projects()
    #print(projects)
except Exception as error:
    print(error)

project_names = [project.name.lower() for project in projects]
#print(project_names)
"""
if('berkeley' in [project.name.lower() for project in projects]):
    berkeley_project_id = (project.name for project in projects if 'berkeley' in project.name.lower())
    print(berkeley_project_id)
else:
    try:
        project = api.add_project(name="Berkeley")
    
    except Exception as error:
        print(error)
    berkeley_project_id = project.id
"""

berkeley_projects = projects[1]
"""
try:
    tasks = api.get_tasks(project_id=berkeley_project_id)
    print(tasks)
except Exception as error:
    print(error)
"""

project = TodoistProject(api,berkeley_projects.id,berkeley_projects.name)
#print(project.p_id, project.name, project.client)
#print(project.get_tasks()[0].name)
#[print(task_.name) for task_ in project.get_tasks()]

project.add_tasks([TodoistTask("test Task", False, "test desc", "Tomorrow", "testing")])

#Due(date='2024-09-25', is_recurring=False, string='Sep 25', datetime=None, timezone=None)