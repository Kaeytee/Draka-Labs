---
applyTo: '**/*.ts'
---
# Copilot Instructions for SIAMS Python Backend

## Project Overview

This is a modular, frameworkless Python backend for a school management system (SIAMS). It enables schools to register, define classes/courses, auto-generate teachers, enroll students, and manage academic records. All user and data flows are automated to minimize manual admin work.

## Architecture & Key Patterns

- **No web framework**: Uses Python’s `http.server` for HTTP, custom routing, and JSON handling.
- **Hot reload**: Use `app.py` (with `watchdog`) to auto-restart the server on code changes.
- **Database**: PostgreSQL via SQLAlchemy ORM. `db.py` ensures the DB exists and provides the engine/session.
- **Directory structure**:
  - `models/`: SQLAlchemy models (User, School, Class, Course, etc.)
  - `services/`: Business logic (e.g., user registration, auto-generation, grade calculation)
  - `handlers/` or route modules: HTTP endpoint logic, one file per endpoint or resource
  - `main.py`: Starts the HTTP server, wires up handlers
  - `app.py`: Dev runner for hot reload
- **Environment**: `.env` for DB and config; loaded via `python-dotenv`.

## Core Flows

- **School Registration**:  
  - POST `/register_school` with school details (name, initials, phone, email, address, grading system)
  - Generates unique school ID, admin email, and default password
  - Creates a School Admin user and redirects to dashboard

- **Class & Course Creation**:  
  - School admin creates classes (levels, metadata)
  - Courses are attached to classes; each course auto-generates a Teacher user with unique email/password

- **Student Enrollment**:  
  - Adding a student to a class auto-generates their email/password and assigns them to the class/courses
  - Students have view-only access to their classes, courses, and grades

- **Teacher Role**:  
  - Teachers can upload grades for assigned courses only
  - Grade calculation uses the school’s grading system (editable by school admin)

- **Roles & Access**:  
  - App Admin: System-wide view, cannot change grades
  - School Admin: Full control over own school
  - Teacher: Can only manage grades for assigned courses
  - Student: View-only

- **Timestamps & Audits**:  
  - All grade uploads/updates must include `created_at`, `updated_at`, and user info

## Coding Conventions

- **Keep endpoint logic out of `main.py`**: Use handler modules for each endpoint.
- **Service logic**: Place business logic in `services/` (e.g., `user_services.py` for registration).
- **Auto-generation**: User emails and passwords follow the pattern:  
  - Admin: `[INITIALS][ID]@schoolsystem.com`
  - Teacher: `[initials]_t[ID]@schoolsystem.com`
  - Student: `[initials]_s[ID]@schoolsystem.com`
  - Password: `[INITIALS]+!+[ID]`
- **Grading system**: Stored as JSON per school; changing it updates all grade mappings.
- **All endpoints must return JSON** and set appropriate HTTP status codes.

## Developer Workflows

- **Start dev server with hot reload**:  
  `python app.py`
- **Run main server (no reload)**:  
  `python main.py`
- **DB setup**:  
  On startup, `db.py` ensures the target DB exists (auto-creates if missing).

## Integration Points

- **No external web frameworks**; only standard library + SQLAlchemy, watchdog, dotenv, psycopg2.
- **No REST framework**: All routing and request parsing is custom.
- **All cross-component logic (e.g., user creation, grade calculation) is in `services/`**.

## Examples

- See `services/user_services.py` for user registration logic.
- See `main.py` for HTTP server setup and handler wiring.
- See `db.py` for DB connection and auto-creation logic.

---

**If you add new endpoints or flows, follow the modular pattern: handler → service → model.**  
**When in doubt, keep business logic out of HTTP handlers.**

---

Let us know if any section is unclear or if you need more details on a specific workflow or pattern!