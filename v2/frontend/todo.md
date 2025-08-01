
### To-Do Plan for Building a Robust Framework-Free Frontend

- **Validate File Structure Alignment**:
  - Confirm each JavaScript module (`main.js`, `auth.js`, etc.) maps to specific functionality (e.g., `school.js` for school CRUD, `student_import.js` for CSV/Excel imports).
  - Ensure HTML pages (`index.html`, `login.html`, etc.) correspond to user roles and features (admin, teacher, student).
  - Verify that utility modules (`utils.js`, `api.js`, etc.) support reusable logic across features.
  - Check that all required features (admin registration, school/class/course management, student imports, result uploads, grading, profile images) are covered by the listed files.
  - Identify any missing files (e.g., CSS files for styling, a dedicated grading page).

- **Implement Global Logic in `main.js`**:
  - Initialize the application by setting up event listeners and loading initial page content.
  - Coordinate module imports (e.g., `auth.js`, `navigation.js`) using ES modules.
  - Handle global state (e.g., current user role, JWT token) stored in `localStorage` or `sessionStorage`.
  - Set up error handling to redirect to `error.html` for unhandled issues.
  - Log frontend initialization and errors for debugging.

- **Build Authentication in `auth.js`**:
  - Implement login logic for `login.html` to send credentials to the backend’s login endpoint and store JWT tokens.
  - Handle admin registration with form validation for secure account creation.
  - Manage token refresh and logout functionality.
  - Validate inputs (e.g., email format, password strength) using `validation.js`.
  - Log authentication events and errors.

- **Develop Admin Features in `admin.js`**:
  - Implement logic for `admin_dashboard.html` to display admin-specific options (e.g., school/class/course management, student imports).
  - Coordinate with `school.js`, `class.js`, `course.js`, and `student_import.js` for CRUD operations.
  - Use `api.js` for backend API calls and `role_access.js` to restrict UI elements to admins.
  - Log admin actions (e.g., creating schools, importing students).

- **Implement Teacher Features in `teacher.js`**:
  - Build logic for `teacher_dashboard.html` to show assigned courses and result upload options.
  - Integrate with `result_upload.js` for uploading student results.
  - Use `api.js` to fetch course data and submit results.
  - Restrict access to teacher-specific features using `role_access.js`.
  - Log result upload attempts and errors.

- **Develop Student Features in `student.js`**:
  - Implement logic for `student_dashboard.html` to display grades and profile management options.
  - Integrate with `grade_view.js` for fetching and displaying grades.
  - Coordinate with `profile.js` and `profile_image_upload.js` for profile updates.
  - Use `api.js` for backend requests and `role_access.js` to limit access.
  - Log student actions (e.g., viewing grades, updating profiles).

- **Handle School Management in `school.js`**:
  - Implement CRUD logic for `school_management.html` to create, update, and list schools.
  - Validate school data (e.g., non-empty name, valid grading system) using `validation.js`.
  - Use `api.js` to call backend school APIs (e.g., create school, update grading system).
  - Display school lists and grading systems in tables or forms.
  - Log school management actions.

- **Manage Class Operations in `class.js`**:
  - Build CRUD logic for `class_management.html` to create, update, and list classes.
  - Support optional teacher assignment during class creation using `validation.js` for input checks.
  - Use `api.js` to interact with backend class APIs.
  - Display class details, including associated courses and students.
  - Log class creation and updates.

- **Implement Course Management in `course.js`**:
  - Develop CRUD logic for `course_management.html` to create, update, and list courses.
  - Handle optional teacher creation or assignment with input validation via `validation.js`.
  - Use `api.js` to call backend course APIs.
  - Display course details, including assigned teachers and students.
  - Log course management actions.

- **Build Student Import in `student_import.js`**:
  - Implement logic for `student_import.html` to handle CSV/Excel file uploads.
  - Parse files client-side using `file_upload.js` and a minimal library (e.g., `PapaParse` for CSV, if permitted).
  - Validate student data (e.g., `full_name`, `date_of_birth`, `gender`) using `validation.js`.
  - Send parsed data to the backend’s student import API via `api.js`.
  - Display import success/failure messages and log events.

- **Handle Result Uploads in `result_upload.js`**:
  - Implement logic for `result_upload.html` to allow teachers to upload student results (e.g., via form or CSV).
  - Validate inputs (e.g., student IDs, scores) using `validation.js`.
  - Use `file_upload.js` for CSV uploads and `api.js` for backend API calls.
  - Display confirmation or error messages and log upload events.

- **Implement Grade Viewing in `grade_view.js`**:
  - Build logic for `student_dashboard.html` or a dedicated grade page to fetch and display student grades.
  - Use `api.js` to call the backend’s grade retrieval API.
  - Format grades based on school or course-specific grading systems.
  - Log grade viewing requests and errors.

- **Manage Profiles in `profile.js`**:
  - Implement logic for profile management (e.g., updating student details like email or additional fields).
  - Use `api.js` to send profile updates to the backend.
  - Validate inputs (e.g., email format) using `validation.js`.
  - Log profile update actions.

- **Handle Profile Image Uploads in `profile_image_upload.js`**:
  - Implement logic for uploading student profile images in `student_dashboard.html` or a profile page.
  - Use `file_upload.js` to handle image uploads with `FormData`.
  - Validate image types (e.g., JPEG, PNG) client-side using `validation.js`.
  - Send images to the backend’s profile image API via `api.js`.
  - Display uploaded images and log upload events.

- **Develop Utility Functions in `utils.js`**:
  - Create reusable functions for common tasks (e.g., DOM manipulation, string sanitization, date formatting).
  - Implement helper functions for JWT parsing, role checking, or data formatting.
  - Ensure utilities are lightweight to avoid bloat.

- **Implement API Calls in `api.js`**:
  - Create wrapper functions for `fetch` API to handle GET, POST, and PUT requests to backend microservices.
  - Include JWT tokens in headers for authenticated requests.
  - Handle API responses and errors (e.g., 400, 401, 500) with consistent error messages.
  - Log all API calls and responses for debugging.

- **Manage Navigation in `navigation.js`**:
  - Implement page navigation logic for `index.html` and role-specific dashboards.
  - Use `window.location` for multi-page navigation or dynamic DOM updates for single-page app style.
  - Redirect users based on roles (e.g., admin to `admin_dashboard.html`, student to `student_dashboard.html`) using `role_access.js`.
  - Log navigation events.

- **Handle Form Validation in `validation.js`**:
  - Implement client-side validation for all forms (e.g., login, school creation, student import).
  - Check for required fields, valid formats (e.g., email, date of birth), and data ranges (e.g., grading system min/max).
  - Display validation errors on forms without reloading pages.
  - Log validation failures for debugging.

- **Support File Uploads in `file_upload.js`**:
  - Create reusable functions for handling file inputs (CSV/Excel for student imports, images for profiles).
  - Parse files client-side using `FileReader` and minimal libraries (if permitted).
  - Use `FormData` to send files to backend APIs via `api.js`.
  - Validate file types and sizes before upload.

- **Implement Role-Based Access in `role_access.js`**:
  - Control UI visibility based on user roles (admin, teacher, student) from JWT token or API response.
  - Show/hide elements (e.g., admin sees student import, teachers see result upload) using DOM manipulation.
  - Redirect unauthorized users to `login.html` or `error.html`.
  - Log access control events.

- **Handle Errors in `error.js`**:
  - Implement centralized error handling for API failures, validation errors, and unexpected issues.
  - Display user-friendly error messages on `error.html` or inline on pages.
  - Log errors to the console or a client-side logging service.
  - Redirect to `error.html` for critical failures.

- **Style HTML Pages with Vanilla CSS**:
  - Create a global `styles.css` for consistent styling across all HTML pages.
  - Use CSS custom properties for theming (e.g., colors, fonts).
  - Implement responsive design with Grid or Flexbox for mobile and desktop support.
  - Style forms, tables, and buttons to match system branding.
  - Minimize CSS file size for performance.

- **Ensure Robustness and Security**:
  - Validate all inputs client-side to reduce invalid API requests.
  - Sanitize user inputs to prevent XSS attacks (e.g., escape HTML in displayed data).
  - Handle HTTP errors (400, 401, 500) with clear messages.
  - Implement CSRF protection by including tokens in POST requests (if backend supports).
  - Use HTTPS for all API calls to secure data.
  - Log client-side errors for debugging.

- **Optimize Performance**:
  - Cache DOM elements to minimize queries.
  - Use event delegation for efficient event handling.
  - Lazy-load profile images with `loading="lazy"`.
  - Compress CSS and JavaScript files.
  - Cache API responses in `localStorage` for frequently accessed data (e.g., school lists).

- **Ensure Accessibility**:
  - Use semantic HTML5 elements (e.g., `<form>`, `<nav>`) for all pages.
  - Add ARIA attributes for interactive elements (e.g., forms, buttons).
  - Ensure keyboard navigation for all features.
  - Provide alt text for images (e.g., student profiles).
  - Test with screen readers for compatibility.

- **Integrate with Backend Microservices**:
  - Map each HTML page and JavaScript module to corresponding backend API endpoints (e.g., `school.js` to school APIs, `result_upload.js` to result APIs).
  - Handle microservice-specific responses and errors via `api.js`.
  - Support asynchronous tasks (e.g., student imports) with polling or status checks.
  - Verify backend CORS settings allow frontend requests.

- **Test Frontend Functionality**:
  - Test each page (`login.html`, `admin_dashboard.html`, etc.) for functionality and responsiveness.
  - Simulate API calls with browser developer tools or Postman to verify integration.
  - Test file uploads (CSV/Excel, images) with various file sizes and formats.
  - Validate role-based access (e.g., teachers can’t access admin features).
  - Check error handling on `error.html` and inline messages.

- **Deploy Frontend**:
  - Host static files (HTML, CSS, JavaScript) on a web server (e.g., Nginx) or CDN.
  - Configure backend to serve images (`GET /uploads/<filename>`) correctly.
  - Set up a reverse proxy for API routing to microservices.
  - Monitor frontend performance and errors with browser tools or lightweight logging.

### Evaluation of File Structure and Gaps
- **Implemented Correctly**:
  - File structure covers all major features: authentication (`auth.js`, `login.html`), admin/teacher/student dashboards, school/class/course management, student imports, result uploads, grade viewing, and profile/image management.
  - Utility modules (`utils.js`, `api.js`, etc.) support reusable logic.
  - HTML pages align with user roles and functionality.
- **Potential Gaps**:
  - Missing a dedicated grading page (e.g., `grade_view.html`) for students to view grades, though `student_dashboard.html` may cover this.
  - No CSS file listed (e.g., `styles.css`) for styling HTML pages.
  - No explicit support for microservices discovery (e.g., API gateway URLs in `api.js`).
  - Potential need for additional utility modules (e.g., for async task polling).
- **Alignment with Logic**:
  - Structure supports admin registration, school/class/course creation, student imports with automatic account creation, result uploads, grading, and profile images.
  - Role-based access (`role_access.js`) aligns with admin/teacher/student roles.
  - File uploads (`file_upload.js`, `student_import.js`, `profile_image_upload.js`) cover CSV/Excel and image requirements.
- **Action for Gaps**:
  - Add a global `styles.css` file for consistent styling.
  - Consider a dedicated `grade_view.html` if `student_dashboard.html` is insufficient.
  - Define API endpoints in `api.js` for each microservice or use a gateway URL.
  - Add polling logic in `utils.js` for async tasks (e.g., student import status).

### Next Steps
- Implement each JavaScript module and HTML page incrementally, starting with `login.html` and `auth.js`.
- Test integration with backend APIs using browser developer tools or Postman.
- Confirm backend supports all required endpoints (e.g., student import, result uploads) and returns compatible JSON responses.
- Specify if external libraries (e.g., `PapaParse` for CSV parsing) are allowed for `file_upload.js`.
- Share backend API details (e.g., endpoint URLs, response formats) to ensure `api.js` aligns.
- Test responsiveness and accessibility on all pages.
- Deploy and monitor the frontend to verify smooth operation with the backend.

This plan leverages your file structure to build a robust, framework-free frontend that integrates with your backend microservices, ensuring all features are implemented securely and efficiently. 