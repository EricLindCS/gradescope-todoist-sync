from todoist_api_python.api import TodoistAPI

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

berkeley_project_id = projects[1].id
print(berkeley_project_id)

try:
    tasks = api.get_tasks(project_id=berkeley_project_id)
    print(tasks)
except Exception as error:
    print(error)




#print(projects)
#[print(project.id) for project in projects]
#project_names = [project['name'].lower() for project in projects]
#a = 'berkele1y' in [project.name.lower() for project in projects]
#print(a)