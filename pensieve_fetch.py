#!/usr/bin/env python3
"""Fetch courses and assignments from Pensieve using the local `pensieve_api` module.

Usage:
  python3 pensieve_fetch.py
  python3 pensieve_fetch.py <course_id_or_url>

Requires PENSIEVE_COOKIE to be set in the environment or in a .env file.
"""
from dotenv import load_dotenv
import os
import sys

load_dotenv()

cookie = os.environ.get("PENSIEVE_COOKIE")
if not cookie:
    print("PENSIEVE_COOKIE not set. Run the app setup to generate it or set PENSIEVE_COOKIE in .env")
    sys.exit(1)


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        from pensieve_api.client import PensieveClient
    except Exception as e:
        print("Could not import pensieve_api.client:", e)
        sys.exit(2)

    try:
        client = PensieveClient(session_cookie=cookie)
    except Exception as e:
        print("Failed to instantiate PensieveClient:", e)
        sys.exit(3)

    if arg:
        # If arg looks like a URL, try to derive course id from it and fetch that course
        if arg.startswith("http://") or arg.startswith("https://"):
            course = client.get_course(course_url=arg)
            courses = [course]
        else:
            # treat as course id
            course = client.get_course(course_id=arg)
            courses = [course]
    else:
        courses = client.get_course_list()

    if not courses:
        print("No Pensieve courses found")
        return

    for c in courses:
        print(f"Course: {c.course_name} (id={c.course_id})")
        try:
            assns = c.get_assignments_list()
        except Exception as e:
            print(f"  Failed to fetch assignments for {c.course_name}: {e}")
            continue

        if not assns:
            print("  (no assignments found)")
            continue

        for a in assns:
            print(f"  - {a.assignment_name} | due={a.due_date} | status={a.status} | url={a.url}")


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""Fetch a Pensieve page and print the HTML to stdout.

Usage:
  python3 pensieve_fetch.py [url_or_path]

If the argument starts with http(s) it will be used as the full URL. Otherwise it is treated
as a path under https://www.pensieve.co (default: /student/classes/data100_sp26/my-assignments).

Requires PENSIEVE_COOKIE to be set in the environment or in a .env file.
"""
from dotenv import load_dotenv
import os
import sys
import requests

load_dotenv()

PENSIEVE_BASE = "https://www.pensieve.co"
cookie = os.environ.get("PENSIEVE_COOKIE")
if not cookie:
    print("PENSIEVE_COOKIE not set. Run the app setup to generate it or set PENSIEVE_COOKIE in .env")
    sys.exit(1)

else:
    url = "https://www.pensieve.co/student"

session = requests.Session()
session.headers.update({"User-Agent": "pensieve-fetch/1.0", "Cookie": cookie})

try:
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    # Print raw HTML to stdout
    print(resp.text)
except requests.exceptions.RequestException as e:
    print("Request error:", e)
    if 'resp' in locals():
        print("Status code:", getattr(resp, 'status_code', None))
        print("Response headers:", getattr(resp, 'headers', None))
    sys.exit(2)

