from flask import Flask, jsonify, request, render_template_string
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
import webbrowser
import time
import secrets
from pathlib import Path

# Load environment variables
load_dotenv()
TODOIST_API_STRING = os.environ.get('TODOIST_API_KEY')
api = TodoistAPI(TODOIST_API_STRING)
gradescope_client = GradescopeClient(email=os.environ.get("GRADESCOPE_USER"), password=os.environ.get("GRADESCOPE_PASSWORD"))
canvas_client = CanvasAPI(os.environ.get('CANVAS_API_URL'), os.environ.get('CANVAS_API'))
PENSIEVE_COOKIE = os.environ.get("PENSIEVE_COOKIE")
# If cookie missing, prepare a short-lived token and open Pensieve + a local setup page
_PENSIEVE_SETUP_TOKEN = None
if not PENSIEVE_COOKIE:
    _PENSIEVE_SETUP_TOKEN = secrets.token_urlsafe(16)
    pensieve_url = "https://www.pensieve.co/student"
    try:
        print("PENSIEVE_COOKIE not set. Opening Pensieve in your default browser so you can sign in with Google.")
        print("After signing in, visit the local setup page that was opened and click the bookmarklet or paste the provided JS into the console to send your Pensieve cookie to the app.")
        # Open both the Pensieve site (where user signs in) and the local setup page
        webbrowser.open(pensieve_url, new=2)
        webbrowser.open("http://localhost:5001/pensieve_setup", new=2)
        # Small sleep so any startup logs appear after the browser is opened
        time.sleep(1)
    except Exception as e:
        print(f"Could not open browser automatically; please open {pensieve_url} and http://localhost:5001/pensieve_setup manually to sign in. Error: {e}")

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

    print("Fetching Todoist Projects...")

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
    print("Fetching Gradescope Courses...")
    gradescope_courses = gradescope_client.get_course_list()
    non_excluded_gradescope_courses = [course for course in gradescope_courses if course.course_id not in excluded_course_ids]

    # Further filter the Gradescope courses to match the active term
    active_term = gradescope_client.get_latest_term()
    filtered_gradescope_courses = [course for course in non_excluded_gradescope_courses if course.get_term() == active_term]

    # Get the list of Canvas courses
    print("Fetching Canvas Courses...")
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
    print(f"Fetched assignments for courses: {[course.course_name for course in combined_courses.values()]}")       

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
    print(f"Assignments after exclusion: {[task.assignment_name for task in gs_todo_list]}")

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
            l_url = f"{task.url}"
        l_str = f"{task._course.course_name} [{l_url}]"
        l_due = task.due_date
        l_name = task.assignment_name
        l_section = next((section for section in sections if section.name == task._course.course_name), None)
        toadd.append(TodoistTask(l_id, l_comp, l_str, l_due, l_name, [task._course.course_name], l_section))
        print(task.assignment_name)

    project.add_tasks(toadd)

    #print("Finished Update Cycle")

def schedule_sync():
    print("Attempting To Update...")
    sync_tasks()
    Timer(39.0, schedule_sync).start()  # Re-run every 10 seconds


def _write_env_var(key: str, value: str, env_path: str = ".env") -> None:
    """Write or update a single KEY=VALUE line in a .env file (creates file if missing).

    This is a simple helper — it preserves other lines and updates or appends the provided key.
    """
    p = Path(env_path)
    lines = []
    if p.exists():
        lines = p.read_text().splitlines()

    found = False
    new_lines = []
    for ln in lines:
        if ln.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(ln)

    if not found:
        new_lines.append(f"{key}={value}")

    p.write_text("\n".join(new_lines) + ("\n" if new_lines and not new_lines[-1].endswith("\n") else ""))


@app.route('/pensieve_setup')
def pensieve_setup():
    """Serve a tiny page with instructions and a bookmarklet / console snippet that posts document.cookie to the local receiver.

    The bookmarklet includes a short-lived token to help avoid open POST endpoints.
    """
    token = _PENSIEVE_SETUP_TOKEN or ""
    # The receiver endpoint on the local app
    receiver = "http://localhost:5001/pensieve_cookie"

    # Use a form-submit approach (works from https pages where fetch->http is blocked as mixed content).
    # This snippet creates a hidden form, appends cookie and token, and submits it.
    js_snippet = (
        "(function(){var f=document.createElement('form');f.method='POST';f.action='" + receiver + "';f.style.display='none';"
        "var i=document.createElement('input');i.name='cookie';i.value=document.cookie;f.appendChild(i);"
        "var t=document.createElement('input');t.name='token';t.value='" + token + "';f.appendChild(t);"
        "document.body.appendChild(f);f.submit();})();"
    )
    bookmarklet = "javascript:" + js_snippet

        html = """
        <html>
            <head><title>Pensieve setup</title></head>
            <body>
                <h2>Pensieve cookie setup</h2>
                <p>Steps:</p>
                <ol>
                    <li>Sign in to <a href="https://www.pensieve.co/student" target="_blank">Pensieve</a> with Google in the browser that opened.</li>
                    <li>On this browser, drag the link below to your bookmarks bar or create a new bookmark with the URL set to the 'bookmarklet' value.</li>
                    <li>While on any <strong>pensieve.co</strong> page after signing in, click the bookmark to send your cookie to this app.</li>
                </ol>
                <p><a href="%s">Send Pensieve cookie (bookmarklet)</a> — drag this to your bookmarks bar.</p>

                <h3>If bookmarklet cannot capture the cookie (HttpOnly)</h3>
                <p>Some auth cookies are HttpOnly and cannot be read by JavaScript. In that case, copy the cookie via DevTools:</p>
                <ol>
                    <li>Open DevTools → Network, reload the page, right-click any request to pensieve.co &gt; Copy &gt; <strong>Copy as cURL</strong>.</li>
                    <li>Paste the resulting <code>curl ...</code> text into the box below (or paste the Cookie header), then press <em>Submit cookie</em>.</li>
                </ol>

                <form method="POST" action="/pensieve_cookie">
                    <input type="hidden" name="token" value="%s" />
                    <p><label for="cookie">Paste cURL or Cookie header here:</label></p>
                    <p><textarea id="cookie" name="cookie" rows="6" style="width:90%%;"></textarea></p>
                    <p><button type="submit">Submit cookie</button></p>
                </form>

                <h3>Alternative (copy/paste in Console)</h3>
                <p>Open devtools &gt; Console on a pensieve page and paste the following, then press Enter:</p>
                <pre id="console">%s</pre>
                <p>Once the cookie is received, the server will store it in <code>.env</code> as <code>PENSIEVE_COOKIE</code>.</p>
            </body>
        </html>
        """ % (bookmarklet, token, js_snippet)

    return render_template_string(html)


@app.route('/pensieve_cookie', methods=['POST'])
def pensieve_cookie():
    """Receive a JSON POST with {cookie, token}. Validate and write to .env.

    Returns JSON status.
    """
    global _PENSIEVE_SETUP_TOKEN, PENSIEVE_COOKIE
    # Try JSON body first (bookmarklet/console may send JSON), otherwise fall back to form-encoded
    data = None
    cookie = None
    token = None
    try:
        data = request.get_json(silent=True)
    except Exception:
        data = None

    if data:
        cookie = data.get('cookie')
        token = data.get('token')
    else:
        # fallback to standard form-encoded POST (from the form-submit bookmarklet)
        cookie = request.form.get('cookie')
        token = request.form.get('token')
    # If the user pasted a full curl command, try to extract the Cookie header
    if cookie and 'curl ' in cookie and 'Cookie:' in cookie:
        # crude extraction: find "Cookie:" and then capture until the next quote or end
        try:
            import re

            m = re.search(r"Cookie:\s*'([^"]*)'", cookie)
            if not m:
                m = re.search(r'Cookie:\s*"([^\"]*)"', cookie)
            if not m:
                # fallback: locate 'Cookie:' and take the remainder of the line
                idx = cookie.find('Cookie:')
                part = cookie[idx + len('Cookie:'):]
                # split on space or quote
                part = part.strip()
                if part.startswith("'") or part.startswith('"'):
                    part = part[1:]
                # drop trailing quote if present
                part = part.split("'", 1)[0].split('"', 1)[0].strip()
                extracted = part
            else:
                extracted = m.group(1)

            cookie = extracted
        except Exception:
            pass
    if not cookie or not token:
        return jsonify({"ok": False, "error": "missing cookie or token"}), 400
    if _PENSIEVE_SETUP_TOKEN is None or token != _PENSIEVE_SETUP_TOKEN:
        return jsonify({"ok": False, "error": "invalid token"}), 403

    # Persist cookie to .env
    try:
        # Save the raw cookie string (caller may choose to store a subset later)
        _write_env_var('PENSIEVE_COOKIE', cookie)
        # Also set in-memory variable so runtime code can use it if needed
        PENSIEVE_COOKIE = cookie
        # Clear the token so bookmarklet cannot be reused
        _PENSIEVE_SETUP_TOKEN = None
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({"message": "Task sync app running!"})

# Start the synchronization when the app is initialized
schedule_sync()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

