import { api } from "./api.js"
import { validation } from "./validation.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"

class ClassManagement {
  constructor() {
    this.classes = []
    this.schools = []
    this.teachers = []
    this.currentPage = 1
    this.itemsPerPage = 10
    this.totalPages = 1
    this.currentEditId = null
    this.currentDeleteId = null
    this.init()
  }

  async init() {
    // Check permissions
    if (!roleAccess.hasPermission("manage_classes")) {
      window.location.href = "error.html?code=403&message=Access denied"
      return
    }

    this.setupEventListeners()
    this.setupFormValidation()
    await this.loadInitialData()

    console.log("Class management initialized")
  }

  async loadInitialData() {
    this.showLoading(true)

    try {
      // Load schools, teachers, and classes in parallel
      const [schoolsResponse, teachersResponse, classesResponse] = await Promise.all([
        api.getSchools(),
        api.get("/teachers"),
        api.getClasses(),
      ])

      this.schools = schoolsResponse.data || []
      this.teachers = teachersResponse.data || []
      this.classes = classesResponse.data || []

      this.populateSchoolDropdowns()
      this.populateTeacherDropdowns()
      this.populateFilters()
      this.renderClassesTable()

      console.log(
        `Loaded ${this.classes.length} classes, ${this.schools.length} schools, ${this.teachers.length} teachers`,
      )
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

    // Class form submission
    const classForm = document.getElementById("classForm")
    classForm?.addEventListener("submit", (e) => {
      e.preventDefault()
      this.handleClassSubmission(classForm)
    })

    // Reset form
    const resetBtn = document.getElementById("resetBtn")
    resetBtn?.addEventListener("click", () => {
      this.resetForm()
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
    const searchInput = document.getElementById("searchClasses")
    searchInput?.addEventListener(
      "input",
      utils.debounce(() => {
        this.filterClasses()
      }, 300),
    )

    const filterSchool = document.getElementById("filterSchool")
    const filterYear = document.getElementById("filterYear")
    filterSchool?.addEventListener("change", () => this.filterClasses())
    filterYear?.addEventListener("change", () => this.filterClasses())

    // Pagination
    const prevPageBtn = document.getElementById("prevPageBtn")
    const nextPageBtn = document.getElementById("nextPageBtn")
    prevPageBtn?.addEventListener("click", () => {
      if (this.currentPage > 1) {
        this.currentPage--
        this.renderClassesTable()
      }
    })
    nextPageBtn?.addEventListener("click", () => {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
        this.renderClassesTable()
      }
    })

    // Modal event listeners
    this.setupModalEventListeners()
  }

  setupModalEventListeners() {
    // Edit modal
    const editModalClose = document.getElementById("editModalClose")
    const editCancelBtn = document.getElementById("editCancelBtn")
    const editClassForm = document.getElementById("editClassForm")

    editModalClose?.addEventListener("click", () => this.closeEditModal())
    editCancelBtn?.addEventListener("click", () => this.closeEditModal())
    editClassForm?.addEventListener("submit", (e) => {
      e.preventDefault()
      this.handleClassUpdate(editClassForm)
    })

    // Delete modal
    const deleteModalClose = document.getElementById("deleteModalClose")
    const deleteCancelBtn = document.getElementById("deleteCancelBtn")
    const deleteConfirmBtn = document.getElementById("deleteConfirmBtn")

    deleteModalClose?.addEventListener("click", () => this.closeDeleteModal())
    deleteCancelBtn?.addEventListener("click", () => this.closeDeleteModal())
    deleteConfirmBtn?.addEventListener("click", () => this.handleClassDeletion())

    // Close modals on overlay click
    document.getElementById("editModalOverlay")?.addEventListener("click", (e) => {
      if (e.target.id === "editModalOverlay") this.closeEditModal()
    })
    document.getElementById("deleteModalOverlay")?.addEventListener("click", (e) => {
      if (e.target.id === "deleteModalOverlay") this.closeDeleteModal()
    })
  }

  setupFormValidation() {
    const classForm = document.getElementById("classForm")
    const editClassForm = document.getElementById("editClassForm")

    if (classForm) {
      validation.setupRealTimeValidation(classForm)
    }
    if (editClassForm) {
      validation.setupRealTimeValidation(editClassForm)
    }
  }

  populateSchoolDropdowns() {
    const schoolSelect = document.getElementById("schoolSelect")
    const filterSchool = document.getElementById("filterSchool")

    if (schoolSelect) {
      schoolSelect.innerHTML = '<option value="">Select School</option>'
      this.schools.forEach((school) => {
        const option = document.createElement("option")
        option.value = school.id
        option.textContent = school.name
        schoolSelect.appendChild(option)
      })
    }

    if (filterSchool) {
      // Keep "All Schools" option and add schools
      this.schools.forEach((school) => {
        const option = document.createElement("option")
        option.value = school.id
        option.textContent = school.name
        filterSchool.appendChild(option)
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
    const filterYear = document.getElementById("filterYear")
    if (!filterYear) return

    // Extract unique academic years from classes
    const years = [...new Set(this.classes.map((cls) => cls.academicYear).filter(Boolean))]
    years.sort().forEach((year) => {
      const option = document.createElement("option")
      option.value = year
      option.textContent = year
      filterYear.appendChild(option)
    })
  }

  async handleClassSubmission(form) {
    const formData = utils.getFormData(form)

    // Validate form
    const formValidation = validation.validateForm(form)
    if (!formValidation.isValid) {
      error.handleFormErrors(formValidation.errors, form)
      return
    }

    // Validate academic year format
    const yearPattern = /^\d{4}-\d{4}$/
    if (!yearPattern.test(formData.academicYear)) {
      error.showInline(document.getElementById("academicYear"), "Academic year must be in format YYYY-YYYY")
      return
    }

    // Prepare class data
    const classData = {
      name: formData.name.trim(),
      schoolId: Number.parseInt(formData.schoolId),
      academicYear: formData.academicYear.trim(),
      capacity: formData.capacity ? Number.parseInt(formData.capacity) : null,
      description: formData.description?.trim() || "",
    }

    // Handle teacher assignment
    if (formData.teacherId) {
      classData.teacherId = Number.parseInt(formData.teacherId)
    } else if (formData.newTeacherName?.trim()) {
      classData.newTeacherName = formData.newTeacherName.trim()
    }

    this.showLoading(true)

    try {
      const response = await api.createClass(classData)
      if (response.success) {
        utils.showNotification("Class created successfully!", "success")
        this.resetForm()
        await this.loadInitialData()
      } else {
        throw new Error(response.message || "Failed to create class")
      }
    } catch (err) {
      console.error("Failed to create class:", err)
      error.handleApiError(err, "Creating class")
    } finally {
      this.showLoading(false)
    }
  }

  async handleClassUpdate(form) {
    const formData = utils.getFormData(form)

    // Validate form
    const formValidation = validation.validateForm(form)
    if (!formValidation.isValid) {
      error.handleFormErrors(formValidation.errors, form)
      return
    }

    const classData = {
      name: formData.name.trim(),
      academicYear: formData.academicYear.trim(),
      capacity: formData.capacity ? Number.parseInt(formData.capacity) : null,
      teacherId: formData.teacherId ? Number.parseInt(formData.teacherId) : null,
      description: formData.description?.trim() || "",
    }

    this.showLoading(true)

    try {
      const response = await api.updateClass(this.currentEditId, classData)
      if (response.success) {
        utils.showNotification("Class updated successfully!", "success")
        this.closeEditModal()
        await this.loadInitialData()
      } else {
        throw new Error(response.message || "Failed to update class")
      }
    } catch (err) {
      console.error("Failed to update class:", err)
      error.handleApiError(err, "Updating class")
    } finally {
      this.showLoading(false)
    }
  }

  async handleClassDeletion() {
    if (!this.currentDeleteId) return

    this.showLoading(true)

    try {
      const response = await api.deleteClass(this.currentDeleteId)
      if (response.success) {
        utils.showNotification("Class deleted successfully!", "success")
        this.closeDeleteModal()
        await this.loadInitialData()
      } else {
        throw new Error(response.message || "Failed to delete class")
      }
    } catch (err) {
      console.error("Failed to delete class:", err)
      error.handleApiError(err, "Deleting class")
    } finally {
      this.showLoading(false)
    }
  }

  renderClassesTable() {
    const tbody = document.getElementById("classesTableBody")
    if (!tbody) return

    // Apply filters
    const filteredClasses = this.getFilteredClasses()

    // Calculate pagination
    this.totalPages = Math.ceil(filteredClasses.length / this.itemsPerPage)
    const startIndex = (this.currentPage - 1) * this.itemsPerPage
    const endIndex = startIndex + this.itemsPerPage
    const pageClasses = filteredClasses.slice(startIndex, endIndex)

    // Render table rows
    if (pageClasses.length === 0) {
      tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="no-data">
                        <div class="no-data-message">
                            <div class="no-data-icon">🎓</div>
                            <p>No classes found</p>
                        </div>
                    </td>
                </tr>
            `
    } else {
      const template = `
                {{#each classes}}
                <tr data-class-id="{{id}}">
                    <td>{{id}}</td>
                    <td class="class-name">{{name}}</td>
                    <td>{{schoolName}}</td>
                    <td>{{academicYear}}</td>
                    <td>{{teacherName}}</td>
                    <td class="student-count">{{studentCount}}</td>
                    <td>{{capacity}}</td>
                    <td class="actions-cell">
                        <button class="action-btn edit-btn" data-action="edit" data-id="{{id}}" 
                                aria-label="Edit {{name}}">
                            <span>✏️</span>
                        </button>
                        <button class="action-btn delete-btn" data-action="delete" data-id="{{id}}"
                                aria-label="Delete {{name}}">
                            <span>🗑️</span>
                        </button>
                    </td>
                </tr>
                {{/each}}
            `

      // Prepare data with additional fields
      const classesWithDetails = pageClasses.map((cls) => ({
        ...cls,
        schoolName: this.getSchoolName(cls.schoolId),
        teacherName: this.getTeacherName(cls.teacherId) || "Not assigned",
        studentCount: cls.studentCount || 0,
        capacity: cls.capacity || "No limit",
      }))

      tbody.innerHTML = utils.template(template, { classes: classesWithDetails })

      // Add event listeners to action buttons
      tbody.querySelectorAll(".action-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          const action = btn.dataset.action
          const classId = btn.dataset.id
          const classObj = this.classes.find((c) => c.id.toString() === classId)

          if (action === "edit") {
            this.openEditModal(classObj)
          } else if (action === "delete") {
            this.openDeleteModal(classObj)
          }
        })
      })
    }

    // Update pagination
    this.updatePagination()
  }

  getFilteredClasses() {
    const searchTerm = document.getElementById("searchClasses")?.value.toLowerCase() || ""
    const schoolFilter = document.getElementById("filterSchool")?.value || "all"
    const yearFilter = document.getElementById("filterYear")?.value || "all"

    return this.classes.filter((cls) => {
      const matchesSearch =
        !searchTerm ||
        cls.name.toLowerCase().includes(searchTerm) ||
        cls.description?.toLowerCase().includes(searchTerm) ||
        this.getSchoolName(cls.schoolId).toLowerCase().includes(searchTerm) ||
        this.getTeacherName(cls.teacherId)?.toLowerCase().includes(searchTerm)

      const matchesSchool = schoolFilter === "all" || cls.schoolId.toString() === schoolFilter
      const matchesYear = yearFilter === "all" || cls.academicYear === yearFilter

      return matchesSearch && matchesSchool && matchesYear
    })
  }

  filterClasses() {
    this.currentPage = 1
    this.renderClassesTable()
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

  getSchoolName(schoolId) {
    const school = this.schools.find((s) => s.id === schoolId)
    return school ? school.name : "Unknown School"
  }

  getTeacherName(teacherId) {
    if (!teacherId) return null
    const teacher = this.teachers.find((t) => t.id === teacherId)
    return teacher ? teacher.fullName || teacher.name : "Unknown Teacher"
  }

  openEditModal(classObj) {
    this.currentEditId = classObj.id

    // Populate form
    document.getElementById("editClassId").value = classObj.id
    document.getElementById("editClassName").value = classObj.name
    document.getElementById("editAcademicYear").value = classObj.academicYear
    document.getElementById("editCapacity").value = classObj.capacity || ""
    document.getElementById("editTeacherSelect").value = classObj.teacherId || ""
    document.getElementById("editClassDescription").value = classObj.description || ""

    // Show modal
    const modal = document.getElementById("editModalOverlay")
    modal.classList.add("active")
  }

  closeEditModal() {
    this.currentEditId = null
    const modal = document.getElementById("editModalOverlay")
    modal.classList.remove("active")

    // Reset form
    const form = document.getElementById("editClassForm")
    utils.resetForm(form)
  }

  openDeleteModal(classObj) {
    this.currentDeleteId = classObj.id

    // Populate class info
    const classInfo = document.getElementById("deleteClassInfo")
    classInfo.innerHTML = `
            <div class="class-details">
                <strong>${utils.sanitizeHtml(classObj.name)}</strong>
                <br>
                <small>School: ${utils.sanitizeHtml(this.getSchoolName(classObj.schoolId))}</small>
                <br>
                <small>Academic Year: ${utils.sanitizeHtml(classObj.academicYear)}</small>
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
    const form = document.getElementById("classForm")
    utils.resetForm(form)

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
  document.addEventListener("DOMContentLoaded", () => new ClassManagement())
} else {
  new ClassManagement()
}

export const classManagement = new ClassManagement()
