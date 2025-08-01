import { api } from "./api.js"
import { validation } from "./validation.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"

class CourseManagement {
  constructor() {
    this.courses = []
    this.classes = []
    this.teachers = []
    this.schools = []
    this.currentPage = 1
    this.itemsPerPage = 10
    this.totalPages = 1
    this.currentEditId = null
    this.currentDeleteId = null
    this.init()
  }

  async init() {
    // Check permissions
    if (!roleAccess.hasPermission("manage_courses")) {
      window.location.href = "error.html?code=403&message=Access denied"
      return
    }

    this.setupEventListeners()
    this.setupFormValidation()
    await this.loadInitialData()

    console.log("Course management initialized")
  }

  async loadInitialData() {
    this.showLoading(true)

    try {
      // Load all required data
      const [coursesResponse, classesResponse, teachersResponse, schoolsResponse] = await Promise.all([
        api.getCourses(),
        api.getClasses(),
        api.get("/teachers"),
        api.getSchools(),
      ])

      this.courses = coursesResponse.data || []
      this.classes = classesResponse.data || []
      this.teachers = teachersResponse.data || []
      this.schools = schoolsResponse.data || []

      this.populateDropdowns()
      this.populateFilters()
      this.renderCoursesTable()

      console.log(`Loaded ${this.courses.length} courses`)
    } catch (err) {
      console.error("Failed to load initial data:", err)
      error.handleApiError(err, "Loading data")
    } finally {
      this.showLoading(false)
    }
  }

  setupEventListeners() {
    // Back button
    const backBtn = document.getElementById("backBtn")
    backBtn?.addEventListener("click", () => {
      window.history.back()
    })

    // Refresh button
    const refreshBtn = document.getElementById("refreshBtn")
    refreshBtn?.addEventListener("click", () => {
      this.loadInitialData()
    })

    // Toggle form visibility
    const toggleFormBtn = document.getElementById("toggleFormBtn")
    const formSection = document.querySelector(".form-section .management-form")
    toggleFormBtn?.addEventListener("click", () => {
      const isVisible = formSection.style.display !== "none"
      formSection.style.display = isVisible ? "none" : "block"
      toggleFormBtn.querySelector(".toggle-icon").textContent = isVisible ? "+" : "−"
    })

    // Course form submission
    const courseForm = document.getElementById("courseForm")
    courseForm?.addEventListener("submit", (e) => {
      e.preventDefault()
      this.handleCourseSubmission(courseForm)
    })

    // Reset form
    const resetBtn = document.getElementById("resetBtn")
    resetBtn?.addEventListener("click", () => {
      this.resetForm()
    })

    // Grading type change
    const gradingType = document.getElementById("gradingType")
    gradingType?.addEventListener("change", (e) => {
      this.toggleCustomGradingSection(e.target.value === "custom")
    })

    // Add grade button
    const addGradeBtn = document.getElementById("addGradeBtn")
    addGradeBtn?.addEventListener("click", () => {
      this.addGradeItem()
    })

    // Teacher selection logic
    const teacherSelect = document.getElementById("teacherSelect")
    const newTeacherName = document.getElementById("newTeacherName")

    teacherSelect?.addEventListener("change", () => {
      if (teacherSelect.value) {
        newTeacherName.disabled = true
        newTeacherName.value = ""
      } else {
        newTeacherName.disabled = false
      }
    })

    newTeacherName?.addEventListener("input", () => {
      if (newTeacherName.value.trim()) {
        teacherSelect.disabled = true
        teacherSelect.value = ""
      } else {
        teacherSelect.disabled = false
      }
    })

    // Search and filter functionality
    const searchInput = document.getElementById("searchCourses")
    searchInput?.addEventListener(
      "input",
      utils.debounce(() => {
        this.filterCourses()
      }, 300),
    )

    const filterClass = document.getElementById("filterClass")
    const filterTeacher = document.getElementById("filterTeacher")
    filterClass?.addEventListener("change", () => this.filterCourses())
    filterTeacher?.addEventListener("change", () => this.filterCourses())

    // Pagination
    const prevPageBtn = document.getElementById("prevPageBtn")
    const nextPageBtn = document.getElementById("nextPageBtn")
    prevPageBtn?.addEventListener("click", () => {
      if (this.currentPage > 1) {
        this.currentPage--
        this.renderCoursesTable()
      }
    })
    nextPageBtn?.addEventListener("click", () => {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
        this.renderCoursesTable()
      }
    })

    // Modal event listeners
    this.setupModalEventListeners()
  }

  setupModalEventListeners() {
    // Edit modal
    const editModalClose = document.getElementById("editModalClose")
    const editCancelBtn = document.getElementById("editCancelBtn")
    const editCourseForm = document.getElementById("editCourseForm")

    editModalClose?.addEventListener("click", () => this.closeEditModal())
    editCancelBtn?.addEventListener("click", () => this.closeEditModal())
    editCourseForm?.addEventListener("submit", (e) => {
      e.preventDefault()
      this.handleCourseUpdate(editCourseForm)
    })

    // Delete modal
    const deleteModalClose = document.getElementById("deleteModalClose")
    const deleteCancelBtn = document.getElementById("deleteCancelBtn")
    const deleteConfirmBtn = document.getElementById("deleteConfirmBtn")

    deleteModalClose?.addEventListener("click", () => this.closeDeleteModal())
    deleteCancelBtn?.addEventListener("click", () => this.closeDeleteModal())
    deleteConfirmBtn?.addEventListener("click", () => this.handleCourseDeletion())

    // Close modals on overlay click
    document.getElementById("editModalOverlay")?.addEventListener("click", (e) => {
      if (e.target.id === "editModalOverlay") this.closeEditModal()
    })
    document.getElementById("deleteModalOverlay")?.addEventListener("click", (e) => {
      if (e.target.id === "deleteModalOverlay") this.closeDeleteModal()
    })
  }

  setupFormValidation() {
    const courseForm = document.getElementById("courseForm")
    const editCourseForm = document.getElementById("editCourseForm")

    if (courseForm) {
      validation.setupRealTimeValidation(courseForm)
    }
    if (editCourseForm) {
      validation.setupRealTimeValidation(editCourseForm)
    }
  }

  populateDropdowns() {
    this.populateClassDropdowns()
    this.populateTeacherDropdowns()
  }

  populateClassDropdowns() {
    const classSelect = document.getElementById("classSelect")

    if (classSelect) {
      classSelect.innerHTML = '<option value="">Select Class</option>'
      this.classes.forEach((cls) => {
        const option = document.createElement("option")
        option.value = cls.id
        option.textContent = `${cls.name} (${this.getSchoolName(cls.schoolId)})`
        classSelect.appendChild(option)
      })
    }
  }

  populateTeacherDropdowns() {
    const teacherSelect = document.getElementById("teacherSelect")
    const editTeacherSelect = document.getElementById("editTeacherSelect")

    const populateSelect = (select) => {
      if (!select) return
      select.innerHTML = '<option value="">Select Teacher</option>'
      this.teachers.forEach((teacher) => {
        const option = document.createElement("option")
        option.value = teacher.id
        option.textContent = teacher.fullName || teacher.name
        select.appendChild(option)
      })
    }

    populateSelect(teacherSelect)
    populateSelect(editTeacherSelect)
  }

  populateFilters() {
    const filterClass = document.getElementById("filterClass")
    const filterTeacher = document.getElementById("filterTeacher")

    // Populate class filter
    if (filterClass) {
      this.classes.forEach((cls) => {
        const option = document.createElement("option")
        option.value = cls.id
        option.textContent = `${cls.name} (${this.getSchoolName(cls.schoolId)})`
        filterClass.appendChild(option)
      })
    }

    // Populate teacher filter
    if (filterTeacher) {
      this.teachers.forEach((teacher) => {
        const option = document.createElement("option")
        option.value = teacher.id
        option.textContent = teacher.fullName || teacher.name
        filterTeacher.appendChild(option)
      })
    }
  }

  toggleCustomGradingSection(show) {
    const customSection = document.getElementById("customGradingSection")
    if (customSection) {
      customSection.classList.toggle("hidden", !show)
      if (show && !customSection.querySelector(".grade-item")) {
        this.addGradeItem()
      }
    }
  }

  addGradeItem() {
    const builder = document.getElementById("gradingSystemBuilder")
    const gradeItem = document.createElement("div")
    gradeItem.className = "grade-item"
    gradeItem.innerHTML = `
            <input type="text" placeholder="Grade (e.g., A)" class="grade-name" required>
            <input type="number" placeholder="Min %" class="grade-min" min="0" max="100" required>
            <input type="number" placeholder="Max %" class="grade-max" min="0" max="100" required>
            <button type="button" class="remove-grade-btn" aria-label="Remove grade">×</button>
        `

    // Add remove functionality
    const removeBtn = gradeItem.querySelector(".remove-grade-btn")
    removeBtn.addEventListener("click", () => {
      gradeItem.remove()
    })

    builder.appendChild(gradeItem)
  }

  async handleCourseSubmission(form) {
    const formData = utils.getFormData(form)

    // Validate form
    const formValidation = validation.validateForm(form)
    if (!formValidation.isValid) {
      error.handleFormErrors(formValidation.errors, form)
      return
    }

    // Validate course code format
    const codePattern = /^[A-Z]{2,4}\d{3,4}$/
    if (!codePattern.test(formData.code)) {
      error.showInline(document.getElementById("courseCode"), "Course code must be in format: MATH101, ENG201")
      return
    }

    // Prepare course data
    const courseData = {
      title: formData.title.trim(),
      code: formData.code.trim().toUpperCase(),
      classId: Number.parseInt(formData.classId),
      creditHours: formData.creditHours ? Number.parseInt(formData.creditHours) : null,
      gradingType: formData.gradingType,
      description: formData.description?.trim() || "",
    }

    // Handle teacher assignment
    if (formData.teacherId) {
      courseData.teacherId = Number.parseInt(formData.teacherId)
    } else if (formData.newTeacherName?.trim()) {
      courseData.newTeacherName = formData.newTeacherName.trim()
    }

    // Handle custom grading system
    if (formData.gradingType === "custom") {
      courseData.gradingSystem = this.getCustomGradingSystem()
      const gradingValidation = validation.validateGradingSystem(courseData.gradingSystem)
      if (!gradingValidation.isValid) {
        error.show("Invalid Grading System", gradingValidation.message)
        return
      }
    }

    this.showLoading(true)

    try {
      const response = await api.createCourse(courseData)
      if (response.success) {
        utils.showNotification("Course created successfully!", "success")
        this.resetForm()
        await this.loadInitialData()
      } else {
        throw new Error(response.message || "Failed to create course")
      }
    } catch (err) {
      console.error("Failed to create course:", err)
      error.handleApiError(err, "Creating course")
    } finally {
      this.showLoading(false)
    }
  }

  async handleCourseUpdate(form) {
    const formData = utils.getFormData(form)

    // Validate form
    const formValidation = validation.validateForm(form)
    if (!formValidation.isValid) {
      error.handleFormErrors(formValidation.errors, form)
      return
    }

    const courseData = {
      title: formData.title.trim(),
      code: formData.code.trim().toUpperCase(),
      creditHours: formData.creditHours ? Number.parseInt(formData.creditHours) : null,
      teacherId: formData.teacherId ? Number.parseInt(formData.teacherId) : null,
      description: formData.description?.trim() || "",
    }

    this.showLoading(true)

    try {
      const response = await api.updateCourse(this.currentEditId, courseData)
      if (response.success) {
        utils.showNotification("Course updated successfully!", "success")
        this.closeEditModal()
        await this.loadInitialData()
      } else {
        throw new Error(response.message || "Failed to update course")
      }
    } catch (err) {
      console.error("Failed to update course:", err)
      error.handleApiError(err, "Updating course")
    } finally {
      this.showLoading(false)
    }
  }

  async handleCourseDeletion() {
    if (!this.currentDeleteId) return

    this.showLoading(true)

    try {
      const response = await api.deleteCourse(this.currentDeleteId)
      if (response.success) {
        utils.showNotification("Course deleted successfully!", "success")
        this.closeDeleteModal()
        await this.loadInitialData()
      } else {
        throw new Error(response.message || "Failed to delete course")
      }
    } catch (err) {
      console.error("Failed to delete course:", err)
      error.handleApiError(err, "Deleting course")
    } finally {
      this.showLoading(false)
    }
  }

  getCustomGradingSystem() {
    const gradeItems = document.querySelectorAll("#gradingSystemBuilder .grade-item")
    const gradingSystem = []

    gradeItems.forEach((item) => {
      const grade = item.querySelector(".grade-name").value.trim()
      const min = Number.parseFloat(item.querySelector(".grade-min").value)
      const max = Number.parseFloat(item.querySelector(".grade-max").value)

      if (grade && !isNaN(min) && !isNaN(max)) {
        gradingSystem.push({ grade, min, max })
      }
    })

    return gradingSystem
  }

  renderCoursesTable() {
    const tbody = document.getElementById("coursesTableBody")
    if (!tbody) return

    // Apply filters
    const filteredCourses = this.getFilteredCourses()

    // Calculate pagination
    this.totalPages = Math.ceil(filteredCourses.length / this.itemsPerPage)
    const startIndex = (this.currentPage - 1) * this.itemsPerPage
    const endIndex = startIndex + this.itemsPerPage
    const pageCourses = filteredCourses.slice(startIndex, endIndex)

    // Render table rows
    if (pageCourses.length === 0) {
      tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="no-data">
                        <div class="no-data-message">
                            <div class="no-data-icon">📚</div>
                            <p>No courses found</p>
                        </div>
                    </td>
                </tr>
            `
    } else {
      const template = `
                {{#each courses}}
                <tr data-course-id="{{id}}">
                    <td>{{id}}</td>
                    <td class="course-code">{{code}}</td>
                    <td class="course-title">{{title}}</td>
                    <td>{{className}}</td>
                    <td>{{teacherName}}</td>
                    <td>{{creditHours}}</td>
                    <td class="student-count">{{studentCount}}</td>
                    <td class="actions-cell">
                        <button class="action-btn edit-btn" data-action="edit" data-id="{{id}}" 
                                aria-label="Edit {{title}}">
                            <span>✏️</span>
                        </button>
                        <button class="action-btn delete-btn" data-action="delete" data-id="{{id}}"
                                aria-label="Delete {{title}}">
                            <span>🗑️</span>
                        </button>
                    </td>
                </tr>
                {{/each}}
            `

      // Prepare data with additional fields
      const coursesWithDetails = pageCourses.map((course) => ({
        ...course,
        className: this.getClassName(course.classId),
        teacherName: this.getTeacherName(course.teacherId) || "Not assigned",
        creditHours: course.creditHours || "N/A",
        studentCount: course.studentCount || 0,
      }))

      tbody.innerHTML = utils.template(template, { courses: coursesWithDetails })

      // Add event listeners to action buttons
      tbody.querySelectorAll(".action-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          const action = btn.dataset.action
          const courseId = btn.dataset.id
          const course = this.courses.find((c) => c.id.toString() === courseId)

          if (action === "edit") {
            this.openEditModal(course)
          } else if (action === "delete") {
            this.openDeleteModal(course)
          }
        })
      })
    }

    // Update pagination
    this.updatePagination()
  }

  getFilteredCourses() {
    const searchTerm = document.getElementById("searchCourses")?.value.toLowerCase() || ""
    const classFilter = document.getElementById("filterClass")?.value || "all"
    const teacherFilter = document.getElementById("filterTeacher")?.value || "all"

    return this.courses.filter((course) => {
      const matchesSearch =
        !searchTerm ||
        course.title.toLowerCase().includes(searchTerm) ||
        course.code.toLowerCase().includes(searchTerm) ||
        course.description?.toLowerCase().includes(searchTerm) ||
        this.getClassName(course.classId).toLowerCase().includes(searchTerm) ||
        this.getTeacherName(course.teacherId)?.toLowerCase().includes(searchTerm)

      const matchesClass = classFilter === "all" || course.classId.toString() === classFilter
      const matchesTeacher = teacherFilter === "all" || course.teacherId?.toString() === teacherFilter

      return matchesSearch && matchesClass && matchesTeacher
    })
  }

  filterCourses() {
    this.currentPage = 1
    this.renderCoursesTable()
  }

  updatePagination() {
    const paginationInfo = document.getElementById("paginationInfo")
    const prevPageBtn = document.getElementById("prevPageBtn")
    const nextPageBtn = document.getElementById("nextPageBtn")

    if (paginationInfo) {
      paginationInfo.textContent = `Page ${this.currentPage} of ${this.totalPages}`
    }

    if (prevPageBtn) {
      prevPageBtn.disabled = this.currentPage <= 1
    }

    if (nextPageBtn) {
      nextPageBtn.disabled = this.currentPage >= this.totalPages
    }
  }

  getClassName(classId) {
    const cls = this.classes.find((c) => c.id === classId)
    return cls ? cls.name : "Unknown Class"
  }

  getSchoolName(schoolId) {
    const school = this.schools.find((s) => s.id === schoolId)
    return school ? school.name : "Unknown School"
  }

  getTeacherName(teacherId) {
    if (!teacherId) return null
    const teacher = this.teachers.find((t) => t.id === teacherId)
    return teacher ? teacher.fullName || teacher.name : "Unknown Teacher"
  }

  openEditModal(course) {
    this.currentEditId = course.id

    // Populate form
    document.getElementById("editCourseId").value = course.id
    document.getElementById("editCourseTitle").value = course.title
    document.getElementById("editCourseCode").value = course.code
    document.getElementById("editCreditHours").value = course.creditHours || ""
    document.getElementById("editTeacherSelect").value = course.teacherId || ""
    document.getElementById("editCourseDescription").value = course.description || ""

    // Show modal
    const modal = document.getElementById("editModalOverlay")
    modal.classList.add("active")
  }

  closeEditModal() {
    this.currentEditId = null
    const modal = document.getElementById("editModalOverlay")
    modal.classList.remove("active")

    // Reset form
    const form = document.getElementById("editCourseForm")
    utils.resetForm(form)
  }

  openDeleteModal(course) {
    this.currentDeleteId = course.id

    // Populate course info
    const courseInfo = document.getElementById("deleteCourseInfo")
    courseInfo.innerHTML = `
            <div class="course-details">
                <strong>${utils.sanitizeHtml(course.code)} - ${utils.sanitizeHtml(course.title)}</strong>
                <br>
                <small>Class: ${utils.sanitizeHtml(this.getClassName(course.classId))}</small>
                <br>
                <small>Teacher: ${utils.sanitizeHtml(this.getTeacherName(course.teacherId) || "Not assigned")}</small>
            </div>
        `

    // Show modal
    const modal = document.getElementById("deleteModalOverlay")
    modal.classList.add("active")
  }

  closeDeleteModal() {
    this.currentDeleteId = null
    const modal = document.getElementById("deleteModalOverlay")
    modal.classList.remove("active")
  }

  resetForm() {
    const form = document.getElementById("courseForm")
    utils.resetForm(form)

    // Reset grading system
    document.getElementById("gradingType").value = "school"
    this.toggleCustomGradingSection(false)

    // Clear custom grades
    const builder = document.getElementById("gradingSystemBuilder")
    builder.innerHTML = ""

    // Re-enable all fields
    document.getElementById("teacherSelect").disabled = false
    document.getElementById("newTeacherName").disabled = false
  }

  showLoading(show) {
    const loadingOverlay = document.getElementById("loadingOverlay")
    if (loadingOverlay) {
      loadingOverlay.classList.toggle("active", show)
    }
  }
}

// Initialize when DOM is loaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => new CourseManagement())
} else {
  new CourseManagement()
}

export const courseManagement = new CourseManagement()
