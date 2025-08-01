import { api } from "./api.js"
import { validation } from "./validation.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"

class SchoolManagement {
  constructor() {
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
    if (!roleAccess.hasPermission("manage_schools")) {
      window.location.href = "error.html?code=403&message=Access denied"
      return
    }

    this.setupEventListeners()
    this.setupFormValidation()
    await this.loadSchools()

    console.log("School management initialized")
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
      this.loadSchools()
    })

    // Toggle form visibility
    const toggleFormBtn = document.getElementById("toggleFormBtn")
    const formSection = document.querySelector(".form-section .management-form")
    toggleFormBtn?.addEventListener("click", () => {
      const isVisible = formSection.style.display !== "none"
      formSection.style.display = isVisible ? "none" : "block"
      toggleFormBtn.querySelector(".toggle-icon").textContent = isVisible ? "+" : "−"
    })

    // School form submission
    const schoolForm = document.getElementById("schoolForm")
    schoolForm?.addEventListener("submit", (e) => {
      e.preventDefault()
      this.handleSchoolSubmission(schoolForm)
    })

    // Reset form
    const resetBtn = document.getElementById("resetBtn")
    resetBtn?.addEventListener("click", () => {
      this.resetForm()
    })

    // Grading system type change
    const gradingSystemType = document.getElementById("gradingSystemType")
    gradingSystemType?.addEventListener("change", (e) => {
      this.toggleCustomGradingSection(e.target.value === "custom")
    })

    // Add grade button
    const addGradeBtn = document.getElementById("addGradeBtn")
    addGradeBtn?.addEventListener("click", () => {
      this.addGradeItem()
    })

    // Search functionality
    const searchInput = document.getElementById("searchSchools")
    searchInput?.addEventListener(
      "input",
      utils.debounce(() => {
        this.filterSchools()
      }, 300),
    )

    // Filter functionality
    const filterSelect = document.getElementById("filterSchools")
    filterSelect?.addEventListener("change", () => {
      this.filterSchools()
    })

    // Pagination
    const prevPageBtn = document.getElementById("prevPageBtn")
    const nextPageBtn = document.getElementById("nextPageBtn")
    prevPageBtn?.addEventListener("click", () => {
      if (this.currentPage > 1) {
        this.currentPage--
        this.renderSchoolsTable()
      }
    })
    nextPageBtn?.addEventListener("click", () => {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
        this.renderSchoolsTable()
      }
    })

    // Edit modal
    const editModalClose = document.getElementById("editModalClose")
    const editCancelBtn = document.getElementById("editCancelBtn")
    const editSchoolForm = document.getElementById("editSchoolForm")

    editModalClose?.addEventListener("click", () => {
      this.closeEditModal()
    })
    editCancelBtn?.addEventListener("click", () => {
      this.closeEditModal()
    })
    editSchoolForm?.addEventListener("submit", (e) => {
      e.preventDefault()
      this.handleSchoolUpdate(editSchoolForm)
    })

    // Delete modal
    const deleteModalClose = document.getElementById("deleteModalClose")
    const deleteCancelBtn = document.getElementById("deleteCancelBtn")
    const deleteConfirmBtn = document.getElementById("deleteConfirmBtn")

    deleteModalClose?.addEventListener("click", () => {
      this.closeDeleteModal()
    })
    deleteCancelBtn?.addEventListener("click", () => {
      this.closeDeleteModal()
    })
    deleteConfirmBtn?.addEventListener("click", () => {
      this.handleSchoolDeletion()
    })

    // Close modals on overlay click
    document.getElementById("editModalOverlay")?.addEventListener("click", (e) => {
      if (e.target.id === "editModalOverlay") {
        this.closeEditModal()
      }
    })
    document.getElementById("deleteModalOverlay")?.addEventListener("click", (e) => {
      if (e.target.id === "deleteModalOverlay") {
        this.closeDeleteModal()
      }
    })
  }

  setupFormValidation() {
    const schoolForm = document.getElementById("schoolForm")
    const editSchoolForm = document.getElementById("editSchoolForm")

    if (schoolForm) {
      validation.setupRealTimeValidation(schoolForm)
    }
    if (editSchoolForm) {
      validation.setupRealTimeValidation(editSchoolForm)
    }
  }

  async loadSchools() {
    this.showLoading(true)

    try {
      const response = await api.getSchools()
      this.schools = response.data || []
      this.renderSchoolsTable()
      console.log(`Loaded ${this.schools.length} schools`)
    } catch (err) {
      console.error("Failed to load schools:", err)
      error.handleApiError(err, "Loading schools")
    } finally {
      this.showLoading(false)
    }
  }

  async handleSchoolSubmission(form) {
    const formData = utils.getFormData(form)

    // Validate form
    const formValidation = validation.validateForm(form)
    if (!formValidation.isValid) {
      error.handleFormErrors(formValidation.errors, form)
      return
    }

    // Prepare school data
    const schoolData = {
      name: formData.name.trim(),
      address: formData.address?.trim() || "",
      phone: formData.phone?.trim() || "",
      email: formData.email?.trim() || "",
      gradingSystem: this.getGradingSystemData(formData.gradingSystemType),
    }

    // Validate grading system if custom
    if (formData.gradingSystemType === "custom") {
      const gradingValidation = validation.validateGradingSystem(schoolData.gradingSystem)
      if (!gradingValidation.isValid) {
        error.show("Invalid Grading System", gradingValidation.message)
        return
      }
    }

    this.showLoading(true)

    try {
      const response = await api.createSchool(schoolData)
      if (response.success) {
        utils.showNotification("School created successfully!", "success")
        this.resetForm()
        await this.loadSchools()
      } else {
        throw new Error(response.message || "Failed to create school")
      }
    } catch (err) {
      console.error("Failed to create school:", err)
      error.handleApiError(err, "Creating school")
    } finally {
      this.showLoading(false)
    }
  }

  async handleSchoolUpdate(form) {
    const formData = utils.getFormData(form)

    // Validate form
    const formValidation = validation.validateForm(form)
    if (!formValidation.isValid) {
      error.handleFormErrors(formValidation.errors, form)
      return
    }

    const schoolData = {
      name: formData.name.trim(),
      address: formData.address?.trim() || "",
      phone: formData.phone?.trim() || "",
      email: formData.email?.trim() || "",
      status: formData.status,
    }

    this.showLoading(true)

    try {
      const response = await api.updateSchool(this.currentEditId, schoolData)
      if (response.success) {
        utils.showNotification("School updated successfully!", "success")
        this.closeEditModal()
        await this.loadSchools()
      } else {
        throw new Error(response.message || "Failed to update school")
      }
    } catch (err) {
      console.error("Failed to update school:", err)
      error.handleApiError(err, "Updating school")
    } finally {
      this.showLoading(false)
    }
  }

  async handleSchoolDeletion() {
    if (!this.currentDeleteId) return

    this.showLoading(true)

    try {
      const response = await api.deleteSchool(this.currentDeleteId)
      if (response.success) {
        utils.showNotification("School deleted successfully!", "success")
        this.closeDeleteModal()
        await this.loadSchools()
      } else {
        throw new Error(response.message || "Failed to delete school")
      }
    } catch (err) {
      console.error("Failed to delete school:", err)
      error.handleApiError(err, "Deleting school")
    } finally {
      this.showLoading(false)
    }
  }

  getGradingSystemData(type) {
    if (type === "custom") {
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
    } else {
      // Default grading system
      return [
        { grade: "A", min: 90, max: 100 },
        { grade: "B", min: 80, max: 89 },
        { grade: "C", min: 70, max: 79 },
        { grade: "D", min: 60, max: 69 },
        { grade: "F", min: 0, max: 59 },
      ]
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

  renderSchoolsTable() {
    const tbody = document.getElementById("schoolsTableBody")
    if (!tbody) return

    // Apply filters
    const filteredSchools = this.getFilteredSchools()

    // Calculate pagination
    this.totalPages = Math.ceil(filteredSchools.length / this.itemsPerPage)
    const startIndex = (this.currentPage - 1) * this.itemsPerPage
    const endIndex = startIndex + this.itemsPerPage
    const pageSchools = filteredSchools.slice(startIndex, endIndex)

    // Render table rows
    if (pageSchools.length === 0) {
      tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="no-data">
                        <div class="no-data-message">
                            <div class="no-data-icon">🏫</div>
                            <p>No schools found</p>
                        </div>
                    </td>
                </tr>
            `
    } else {
      const template = `
                {{#each schools}}
                <tr data-school-id="{{id}}">
                    <td>{{id}}</td>
                    <td class="school-name">{{name}}</td>
                    <td>{{address}}</td>
                    <td>{{phone}}</td>
                    <td>{{email}}</td>
                    <td>
                        <span class="grading-system-badge">
                            {{#if gradingSystem.length}}
                                {{gradingSystem.length}} grades
                            {{else}}
                                Default
                            {{/if}}
                        </span>
                    </td>
                    <td>
                        <span class="status-badge status-{{status}}">
                            {{status}}
                        </span>
                    </td>
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

      tbody.innerHTML = utils.template(template, { schools: pageSchools })

      // Add event listeners to action buttons
      tbody.querySelectorAll(".action-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          const action = btn.dataset.action
          const schoolId = btn.dataset.id
          const school = this.schools.find((s) => s.id.toString() === schoolId)

          if (action === "edit") {
            this.openEditModal(school)
          } else if (action === "delete") {
            this.openDeleteModal(school)
          }
        })
      })
    }

    // Update pagination
    this.updatePagination()
  }

  getFilteredSchools() {
    const searchTerm = document.getElementById("searchSchools")?.value.toLowerCase() || ""
    const statusFilter = document.getElementById("filterSchools")?.value || "all"

    return this.schools.filter((school) => {
      const matchesSearch =
        !searchTerm ||
        school.name.toLowerCase().includes(searchTerm) ||
        school.address?.toLowerCase().includes(searchTerm) ||
        school.email?.toLowerCase().includes(searchTerm)

      const matchesStatus = statusFilter === "all" || school.status === statusFilter

      return matchesSearch && matchesStatus
    })
  }

  filterSchools() {
    this.currentPage = 1
    this.renderSchoolsTable()
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

  openEditModal(school) {
    this.currentEditId = school.id

    // Populate form
    document.getElementById("editSchoolId").value = school.id
    document.getElementById("editSchoolName").value = school.name
    document.getElementById("editSchoolAddress").value = school.address || ""
    document.getElementById("editSchoolPhone").value = school.phone || ""
    document.getElementById("editSchoolEmail").value = school.email || ""
    document.getElementById("editSchoolStatus").value = school.status || "active"

    // Show modal
    const modal = document.getElementById("editModalOverlay")
    modal.classList.add("active")
  }

  closeEditModal() {
    this.currentEditId = null
    const modal = document.getElementById("editModalOverlay")
    modal.classList.remove("active")

    // Reset form
    const form = document.getElementById("editSchoolForm")
    utils.resetForm(form)
  }

  openDeleteModal(school) {
    this.currentDeleteId = school.id

    // Populate school info
    const schoolInfo = document.getElementById("deleteSchoolInfo")
    schoolInfo.innerHTML = `
            <div class="school-details">
                <strong>${utils.sanitizeHtml(school.name)}</strong>
                <br>
                <small>${utils.sanitizeHtml(school.address || "No address")}</small>
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
    const form = document.getElementById("schoolForm")
    utils.resetForm(form)

    // Reset grading system
    document.getElementById("gradingSystemType").value = "default"
    this.toggleCustomGradingSection(false)

    // Clear custom grades
    const builder = document.getElementById("gradingSystemBuilder")
    builder.innerHTML = ""
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
  document.addEventListener("DOMContentLoaded", () => new SchoolManagement())
} else {
  new SchoolManagement()
}

export const schoolManagement = new SchoolManagement()
