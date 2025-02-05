from flask import Flask, jsonify
from threading import Timer
from todoist_api_python.api import TodoistAPI
from todoist_api.project import TodoistProject
from todoist_api.task import TodoistTask
from gradescope_api.client import GradescopeClient
from canvas_api.client import CanvasAPI
from canvas_api.course import CanvasCourse
from dotenv import load_dotenv
from datetime import datetime
import os
import requests

# Load environment variables
load_dotenv()
TODOIST_API_STRING = os.environ.get('TODOIST_API_KEY')
api = TodoistAPI(TODOIST_API_STRING)
gradescope_client = GradescopeClient(email=os.environ.get("GRADESCOPE_USER"), password=os.environ.get("GRADESCOPE_PASSWORD"))
canvas_client = CanvasAPI(os.environ.get('CANVAS_API_URL'), os.environ.get('CANVAS_API'))
EXCLUSION_URL = "https://raw.githubusercontent.com/EricLindCS/gradescope-todoist-sync/refs/heads/main/assignmentexclusion.txt"

app = Flask(__name__)

def fetch_exclusion_list(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return {line.strip() for line in response.text.splitlines()}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exclusion list: {e}")
        return set()

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

    # Get the list of Gradescope courses and filter out excluded ones
    gradescope_courses = gradescope_client.get_course_list()
    non_excluded_gradescope_courses = [course for course in gradescope_courses if course.course_id not in excluded_course_ids]

    # Further filter the Gradescope courses to match the active term
    active_term = gradescope_client.get_latest_term()
    filtered_gradescope_courses = [course for course in non_excluded_gradescope_courses if course.get_term() == active_term]

    # Get the list of Canvas courses
    canvas_courses_list = canvas_client.get_courses()
    non_excluded_canvas_courses = [course for course in canvas_courses_list if course.course_id not in excluded_course_ids]
    canvas_courses = [course for course in non_excluded_canvas_courses if course.get_term() == active_term]


    # Combine courses, giving priority to Gradescope courses in case of duplicates
    combined_courses = {course.course_name: course for course in filtered_gradescope_courses}
    for course in canvas_courses:
        if course.course_name not in combined_courses or True:
            combined_courses[course.course_name] = course


    # Get assignments for the combined courses
    gs_assignments = [course.get_assignments_list() for course in combined_courses.values()]        

    flattened_list = [item for sublist in gs_assignments for item in sublist]

    gs_todo_list = [task for task in flattened_list if task.status == 'No Submission']

    #Get Todoist Tasks
    todoist_tasklist = project.get_tasks()

    # Add tasks with 'Delete' label to exclusion file
    with open('assignmentexclusion.txt', 'a') as f:
        for task in todoist_tasklist:
            if 'Delete' in task.labels:
                f.write(f"{task.name}\n")
                print("Excluded Task::" + task.name)

                try:
                    is_success = api.close_task(task.id)
                    print("Closed Task: " + task.name + " " + "Success: " + str(is_success))
                except Exception as error:
                    print("Failed To Close Task:" + task.name + " - " + error)


    #excluded_assignment_names = fetch_exclusion_list(EXCLUSION_URL)
    with open('assignmentexclusion.txt', 'r') as f:
        excluded_assignment_names = {line.strip() for line in f}

    gs_todo_list = [task for task in gs_todo_list if task.assignment_name not in excluded_assignment_names]

    # Compare and create new tasks if needed
    # Compare and create new tasks if needed
    existant_result = [obj1 for obj1 in flattened_list if any(obj1.assignment_name == obj2.name and obj1._course.course_name in obj2.labels for obj2 in todoist_tasklist)]
    no_result = [obj1 for obj1 in gs_todo_list if not any(obj1.assignment_name == obj2.name and obj1._course.course_name in obj2.labels for obj2 in todoist_tasklist)]

    for task in existant_result:
        if task.status != 'No Submission':
            tast = next((todoist_task for todoist_task in todoist_tasklist if task.assignment_name == todoist_task.name), None)
            try:
                is_success = api.close_task(tast.id)
                print("Closed Task: " + tast.name + " " + "Success: " + str(is_success))
            except Exception as error:
                print("Failed To Close Task:" + tast.name + " - " + error)

    # Add Sections
    sections = project.get_sections()
    no_sec_found = [course for course in combined_courses.values() if all(section.name != course.course_name for section in sections) and course.get_assignments_list() != []]
    for sectoadd in no_sec_found:
        project.add_section(sectoadd.course_name)

    # Remove sections that don't have an active course associated with them
    active_course_names = [course.course_name for course in combined_courses.values()]
    for section in sections:
        if section.name not in active_course_names:
            project.remove_section(section.id)

    # Final Sections List
    sections = project.get_sections()

    toadd = []
    for task in no_result:
        l_id = task.url
        l_comp = (task.status != 'No Submission')
        if isinstance(task._course, CanvasCourse):
            l_url = f"https://bcourses.berkeley.edu/courses/{task._course.course_id}/assignments/{task.assignment_id}"
        else:
            l_url = f"https://www.gradescope.com{task.url}"
        l_str = f"{task._course.course_name} [{l_url}]"
        l_due = task.due_date
        l_name = task.assignment_name
        l_section = next((section for section in sections if section.name == task._course.course_name), None)
        toadd.append(TodoistTask(l_id, l_comp, l_str, l_due, l_name, [task._course.course_name], l_section))
        print(task.assignment_name)

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
