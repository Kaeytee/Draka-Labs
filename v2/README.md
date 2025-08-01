# SIAMS School Management System: Frontend Developer Reference

## Overview

**SIAMS** is a modular, role-based school management platform supporting Superusers (system owners), School Admins, Teachers (Staff), and Students. The system is designed for extensibility, robust data validation, and a professional user experience across both backend and frontend.

---

## User Roles & Permissions

| Role        | Permissions                                                                                   |
|-------------|----------------------------------------------------------------------------------------------|
| Superuser   | View all schools, analytics, audit logs. Cannot view raw student/teacher data.               |
| Admin       | Manage their own school: classes, courses, teachers, students. Cannot view audit logs.       |
| Teacher     | Manage/view their assigned courses, upload grades, view students in their classes/courses.   |
| Student     | View their own grades, profile, and academic analytics.                                      |

---

## Data Types & Validation

### User

| Field         | Type     | Validation/Notes                                 |
|---------------|----------|--------------------------------------------------|
| id            | int      | Auto-generated                                   |
| username      | string   | Unique, required, min 3 chars                    |
| full_name     | string   | Required, letters and spaces only                |
| email         | string   | Required, valid email format, unique             |
| role          | enum     | One of: `superuser`, `admin`, `staff`, `student` |
| gender        | enum     | `Male`, `Female`, `Other`                        |
| date_of_birth | date     | Optional, format: `YYYY-MM-DD`                   |
| phone         | string   | Optional, valid phone format                     |
| school_id     | int      | Required for admin, staff, student               |

### School

| Field         | Type     | Validation/Notes                                 |
|---------------|----------|--------------------------------------------------|
| id            | int      | Auto-generated                                   |
| name          | string   | Required, unique                                 |
| initials      | string   | 2-5 uppercase letters, required                  |
| grading_system| array    | List of grade objects (see below)                |
| admin_id      | int      | Required, references User                        |

### Class

| Field         | Type     | Validation/Notes                                 |
|---------------|----------|--------------------------------------------------|
| id            | int      | Auto-generated                                   |
| name          | string   | Required                                         |
| school_id     | int      | Required                                         |
| academic_year | string   | Required, e.g. `2025-2026`                       |
| description   | string   | Optional                                         |

### Course

| Field         | Type     | Validation/Notes                                 |
|---------------|----------|--------------------------------------------------|
| id            | int      | Auto-generated                                   |
| title         | string   | Required                                         |
| code          | string   | Required, e.g. `MATH101`                         |
| class_id      | int      | Required                                         |
| teacher_id    | int      | Required                                         |
| credit_hours  | int      | Required, min 1                                  |
| grading_type  | string   | `default` or `custom`                            |

### Grade

| Field         | Type     | Validation/Notes                                 |
|---------------|----------|--------------------------------------------------|
| id            | int      | Auto-generated                                   |
| student_id    | int      | Required                                         |
| course_id     | int      | Required                                         |
| value         | string   | Required, matches grading system                 |
| graded_by     | int      | Teacher user id                                  |
| timestamp     | datetime | Auto-generated                                   |

### Grading System

Each school/course can have a custom grading system:
```js
[
  { grade: "A", min: 80, max: 100 },
  { grade: "B", min: 70, max: 79 },
  { grade: "C", min: 60, max: 69 },
  { grade: "F", min: 0, max: 59 }
]
```
- **Validation:** No overlapping ranges, min < max, all required fields present.

---

## Data Validation (Frontend)

- **Forms:** All forms must validate required fields, correct types, and formats before submission.
- **CSV Import:** Validate structure, required columns, and data types. Show preview and errors before import.
- **Grading System:** Validate for overlaps, missing fields, and correct ranges.
- **Profile:** Validate email, phone, and date formats.
- **Course Codes:** Regex: `/^[A-Z]{2,4}\d{3,4}$/` (e.g., `MATH101`).

---

## API Data Structures

- **All API responses** are JSON.
- **Errors**: `{ success: false, message: "Error message" }`
- **Success**: `{ success: true, data: {...} }` or `{ success: true, results: [...] }`

---

## UI/UX Expectations

- **Tabulated Data:** All lists (students, courses, teachers, grades) should be displayed in clear, tabular format.
- **Role-Based Navigation:** Show/hide features based on user role.
- **Data Preview:** For imports and analytics, show summary stats and validation results before committing.
- **Accessibility:** Use semantic HTML, ARIA labels, and keyboard navigation.
- **Responsive Design:** All dashboards and tables must be mobile-friendly.

---

## Example: Listing Students (Tabulated)

| ID  | Name           | Email                    | Username   |
|-----|----------------|--------------------------|------------|
| 1   | John Doe       | john@school.com          | johndoe    |
| 2   | Jane Smith     | jane@school.com          | janesmith  |

---

## Example: Listing Teachers with Courses & Classes

| Teacher Name | Email                  | Courses Taught                | Classes         |
|--------------|------------------------|-------------------------------|-----------------|
| Mr. Adams    | adams@school.com       | Math 101, Physics 201         | Class 1, Class 2|
| Ms. Baker    | baker@school.com       | English 101                   | Class 3         |

---

## Example: Student Grade View

| Course         | Grade | Teacher      | Class   | Date       |
|----------------|-------|-------------|---------|------------|
| Math 101       | A     | Mr. Adams   | Class 1 | 2025-06-10 |
| English 101    | B     | Ms. Baker   | Class 3 | 2025-06-11 |

- **Analytics:** Show GPA, grade distribution, and trends.

---

## File Structure (Frontend)

- `js/`
  - `main.js` – App initialization
  - `auth.js` – Authentication logic
  - `admin.js`, `teacher.js`, `student.js` – Role dashboards
  - `school.js`, `class.js`, `course.js` – Management modules
  - `student_import.js` – CSV import logic
  - `grade_view.js` – Grade analytics and display
  - `validation.js` – All validation logic
  - `utils.js` – Utility functions
  - `role_access.js` – Role-based UI control
- `html/`
  - `login.html`, `admin_dashboard.html`, `teacher_dashboard.html`, `student_dashboard.html`, etc.
- `css/`
  - `styles.css` – Global and responsive styles

---

## Best Practices

- **Always validate data client-side before sending to backend.**
- **Use enums and constants for roles and types.**
- **Display errors and validation feedback clearly to users.**
- **Keep UI consistent and accessible.**
- **Use modular JS and CSS for maintainability.**

---

## Next Steps for Frontend Devs

- Map each UI feature to its backend endpoint and data structure.
- Use the provided validation logic and types for all forms and imports.
- Implement tabular and analytics views as shown above.
- Ensure all role-based restrictions are enforced in the UI.
- Coordinate with backend for any new endpoints or data needs.

---

*For more details, see the backend API docs and the populated demo data in `backend/populated_data.md`.*
