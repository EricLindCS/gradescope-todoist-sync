from flask import Flask, jsonify
from threading import Timer
from todoist_api_python.api import TodoistAPI
from todoist_api.project import TodoistProject
from todoist_api.task import TodoistTask
from gradescope_api.client import GradescopeClient
from dotenv import load_dotenv
from datetime import datetime
import os

# Load environment variables
load_dotenv()
TODOIST_API_STRING = os.environ.get('TODOIST_API_KEY')
api = TodoistAPI(TODOIST_API_STRING)
client = GradescopeClient(email=os.environ.get("GRADESCOPE_USER"), password=os.environ.get("GRADESCOPE_PASSWORD"))

app = Flask(__name__)

def sync_tasks():

    print("Attempting To Update...")

    try:
        projects = api.get_projects()
    except Exception as error:
        print(error)
        return

    project_names = [project.name.lower() for project in projects]
    
    if 'berkeley' in project_names:
        berkeley_project_id = next((i for i, project in enumerate(projects) if project.name.lower() == 'berkeley'), None)
        berkeley_projects = projects[berkeley_project_id]
    else:
        try:
            project = api.add_project(name="Berkeley")
            berkeley_projects = project
        except Exception as error:
            print(error)
            return

    project = TodoistProject(api, berkeley_projects.id, berkeley_projects.name)

    # Fetch Gradescope assignments
    gs_assignments = [x.get_assignments_list() for x in client.get_course_list()]
    flattened_list = [item for sublist in gs_assignments for item in sublist]
    gs_todo_list = [task for task in flattened_list if task.status == 'No Submission']

    # Fetch Todoist tasks
    todoist_tasklist = project.get_tasks()

    # Compare and create new tasks if needed
    existant_result = [obj1 for obj1 in gs_todo_list if any(obj1.assignment_name == obj2.name for obj2 in todoist_tasklist)]
    no_result = [obj1 for obj1 in gs_todo_list if not any(obj1.assignment_name == obj2.name for obj2 in todoist_tasklist)]

    

    toadd = []
    for task in no_result:
        l_id = task.url
        l_comp = (task.status != 'No Submission')
        l_str = f"{task._course.course_name} [https://www.gradescope.com{task.url}]"
        l_due = task.due_date
        l_name =  task.assignment_name
        toadd.append(TodoistTask(l_id, l_comp, l_str, l_due, l_name))

    project.add_tasks(toadd)

def schedule_sync():
    sync_tasks()
    Timer(10.0, schedule_sync).start()  # Re-run every 10 seconds

@app.route('/')
def home():
    return jsonify({"message": "Task sync app running!"})

# Start the synchronization when the app is initialized
schedule_sync()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
