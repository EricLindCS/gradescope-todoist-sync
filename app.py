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

    project = TodoistProject(api, berkeley_projects.id, berkeley_projects.name)

    # Fetch Gradescope assignments
    # Read course IDs to exclude from courseexclusion.txt
    with open('courseexclusion.txt', 'r') as f:
        excluded_course_ids = {line.strip() for line in f}

    # Get the list of courses and filter out excluded ones
    courses = client.get_course_list()
    non_excluded_courses = [course for course in courses if course.course_id not in excluded_course_ids]

    # Further filter the courses to match the active term
    active_term = client.get_latest_term()
    filtered_courses = [course for course in non_excluded_courses if course.get_term() == active_term]

    # Get assignments for the filtered courses
    gs_assignments = [course.get_assignments_list() for course in filtered_courses]
    flattened_list = [item for sublist in gs_assignments for item in sublist]
    gs_todo_list = [task for task in flattened_list if task.status == 'No Submission']

    # Fetch Todoist tasks
    todoist_tasklist = project.get_tasks()

    # Compare and create new tasks if needed
    existant_result = [obj1 for obj1 in flattened_list if any(obj1.assignment_name == obj2.name for obj2 in todoist_tasklist)]
    no_result = [obj1 for obj1 in gs_todo_list if not any(obj1.assignment_name == obj2.name for obj2 in todoist_tasklist)]

    
    for task in existant_result:
        if(task.status != 'No Submission'):
            tast = next((todoist_task for todoist_task in todoist_tasklist if task.assignment_name == todoist_task.name), None)
            try:
                is_success = api.close_task(tast.id)
                print("Closed Task: " + tast.name + " " + is_success)
            except Exception as error:
                print(error)

    #Add Sections
    sections = project.get_sections()
    no_sec_found = [course for course in filtered_courses if all(section.name != course.course_name for section in sections)]  
    for sectoadd in no_sec_found:
        project.add_section(sectoadd.course_name)  
    #project_sections = [section for section in sections if any(section.name == course.course_name for course in courses) else ]

    # Remove sections that don't have an active course associated with them
    active_course_names = [course.course_name for course in filtered_courses]
    for section in sections:
        if section.name not in active_course_names:
            project.remove_section(section.id)

    #Final Sections List
    sections = project.get_sections()

    toadd = []
    for task in no_result:
        l_id = task.url
        l_comp = (task.status != 'No Submission')
        l_str = f"{task._course.course_name} [https://www.gradescope.com{task.url}]"
        l_due = task.due_date
        l_name =  task.assignment_name
        l_section = next((section for section in sections if section.name == task._course.course_name), None)
        toadd.append(TodoistTask(l_id, l_comp, l_str, l_due, l_name, l_section))

    project.add_tasks(toadd)

    print("Finished Update Cycle")

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
