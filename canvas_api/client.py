import re
import requests
from typing import TYPE_CHECKING, Dict, List, Optional
from canvas_api.course import CanvasCourse

class CanvasAPI:
    def __init__(self, base_url, api_token):
        
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_token}'
        }
        self.session = requests.Session()  # Create a session object

    def get_courses(self) -> List[CanvasCourse]:
        
        endpoint = f"{self.base_url}/courses?per_page=100"
        try:
            response = self.session.get(endpoint, headers=self.headers)
            response.raise_for_status()
            courses = response.json()

            # Regular expression to match course names with the pattern [Semester] [Year]
            pattern1 = re.compile(r'\b(Fall|Spring|Summer|Winter) \d{4}\b')
            pattern2 = re.compile(r'\b(S|F|Su|W)\d{4}\b')
    
            courses = [course for course in courses if 'name' in course]
            
            # Filter courses
            filtered_courses = [course for course in courses if pattern1.search(course['name']) or pattern2.search(course['name'])]

            # Filter for student enrollments
            student_courses = [
                course for course in filtered_courses
                if 'enrollments' in course and 'student' in [e['type'] for e in course.get('enrollments', [])]
            ]

            canvas_courses = []
            for course in student_courses:
                course_name = re.sub(r'\s*\(.*?\)\s*', '', course['name'].split(':')[0]).strip()
                course_id = course['id']

                term_match = re.search(r'\((.*?)\)', course['name'])
                term = term_match.group(1) if term_match else ''

                canvas_course = CanvasCourse(self, course_id, course_name, term)

                canvas_courses.append(canvas_course)

            return canvas_courses

        except requests.exceptions.RequestException as e:
            print(f"Error fetching courses: {e}")
            return None
