import { api } from "./api.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"
import { fileUpload } from "./file_upload.js"
import { auth } from "./auth.js"

class ResultUpload {
  constructor() {
    this.courses = []
    this.selectedCourse = null
    this.courseStudents = []
    this.uploadMethod = null
    this.csvData = []
    this.validationResults = null
    this.uploadResults = null
    this.init()
  }

  async init() {
    // Check permissions
    if (!roleAccess.hasPermission("upload_results")) {
      window.location.href = "error.html?code=403&message=Access denied"
      return
    }

    this.setupEventListeners()
    await this.loadTeacherCourses()

    console.log("Result upload initialized")
  }

  async loadTeacherCourses() {
    this.showLoading(true)

    try {
      const user = auth.getUser()
      const response = await api.getTeacherCourses(user.id)
      this.courses = response.data || []
      this.populateCourseDropdown()

      console.log(`Loaded ${this.courses.length} courses for teacher`)
    } catch (err) {
      console.error("Failed to load teacher courses:", err)
      error.handleApiError(err, "Loading courses")
    } finally {
      this.showLoading(false)
    }
  }

  populateCourseDropdown() {
    const courseSelect = document.getElementById("courseSelect")
    if (!courseSelect) return

    courseSelect.innerHTML = '<option value="">Select a course to upload results</option>'
    this.courses.forEach((course) => {
      const option = document.createElement("option")
      option.value = course.id
      option.textContent = `${course.code} - ${course.title} (${course.className})`
      courseSelect.appendChild(option)
    })
  }

  setupEventListeners() {
    // Back button
    const backBtn = document.getElementById("backBtn")
    backBtn?.addEventListener("click", () => {
      window.history.back()
    })

    // Download template button
    const downloadTemplateBtn = document.getElementById("downloadTemplateBtn")
    downloadTemplateBtn?.addEventListener("click", () => {
      this.downloadTemplate()
    })

    // Course selection
    const courseSelect = document.getElementById("courseSelect")
    courseSelect?.addEventListener("change", (e) => {
      this.handleCourseSelection(e.target.value)
    })

    // Method selection
    const methodBtns = document.querySelectorAll(".method-btn")
    methodBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        this.selectUploadMethod(btn.dataset.method)
      })
    })

    // Manual form
    const manualForm = document.getElementById("manualForm")
    manualForm?.addEventListener("submit", (e) => {
      e.preventDefault()
      this.handleManualSubmission()
    })

    const manualCancelBtn = document.getElementById("manualCancelBtn")
    manualCancelBtn?.addEventListener("click", () => {
      this.resetUpload()
    })

    // Search students
    const searchStudents = document.getElementById("searchStudents")
    searchStudents?.addEventListener(
      "input",
      utils.debounce(() => {
        this.filterStudents()
      }, 300),
    )

    // CSV form
    const csvSubmitBtn = document.getElementById("csvSubmitBtn")
    csvSubmitBtn?.addEventListener("click", () => {
      this.handleCSVSubmission()
    })

    const csvCancelBtn = document.getElementById("csvCancelBtn")
    csvCancelBtn?.addEventListener("click", () => {
      this.resetCSVUpload()
    })

    // Results actions
    const newUploadBtn = document.getElementById("newUploadBtn")
    newUploadBtn?.addEventListener("click", () => {
      this.resetUpload()
    })

    const downloadResultsBtn = document.getElementById("downloadResultsBtn")
    downloadResultsBtn?.addEventListener("click", () => {
      this.downloadResults()
    })

    // Results tabs
    const tabBtns = document.querySelectorAll(".tab-btn")
    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const tabName = btn.dataset.tab
        this.switchResultsTab(tabName)
      })
    })
  }

  async handleCourseSelection(courseId) {
    if (!courseId) {
      this.selectedCourse = null
      this.hideMethodSection()
      return
    }

    this.selectedCourse = this.courses.find((c) => c.id.toString() === courseId)
    if (!this.selectedCourse) return

    // Load course students
    await this.loadCourseStudents(courseId)

    // Show course info
    this.showCourseInfo()

    // Show method selection
    this.showMethodSection()
  }

  async loadCourseStudents(courseId) {
    this.showLoading(true)

    try {
      const response = await api.get(`/courses/${courseId}/students`)
      this.courseStudents = response.data || []

      console.log(`Loaded ${this.courseStudents.length} students for course`)
    } catch (err) {
      console.error("Failed to load course students:", err)
      error.handleApiError(err, "Loading students")
    } finally {
      this.showLoading(false)
    }
  }

  showCourseInfo() {
    const courseInfo = document.getElementById("courseInfo")
    if (!courseInfo || !this.selectedCourse) return

    courseInfo.innerHTML = `
            <div class="course-details glass-panel">
                <div class="course-header">
                    <h3>${utils.sanitizeHtml(this.selectedCourse.code)} - ${utils.sanitizeHtml(this.selectedCourse.title)}</h3>
                    <span class="course-class">${utils.sanitizeHtml(this.selectedCourse.className)}</span>
                </div>
                <div class="course-stats">
                    <div class="stat-item">
                        <span class="stat-label">Students:</span>
                        <span class="stat-value">${this.courseStudents.length}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Credit Hours:</span>
                        <span class="stat-value">${this.selectedCourse.creditHours || "N/A"}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Grading:</span>
                        <span class="stat-value">${this.selectedCourse.gradingType || "School System"}</span>
                    </div>
                </div>
            </div>
        `
  }

  showMethodSection() {
    const methodSection = document.getElementById("methodSection")
    methodSection.classList.remove("hidden")
  }

  hideMethodSection() {
    const methodSection = document.getElementById("methodSection")
    methodSection.classList.add("hidden")
    this.hideAllUploadSections()
  }

  selectUploadMethod(method) {
    this.uploadMethod = method
    this.hideAllUploadSections()

    if (method === "manual") {
      this.showManualSection()
    } else if (method === "csv") {
      this.showCSVSection()
    }

    console.log(`Selected upload method: ${method}`)
  }

  hideAllUploadSections() {
    document.getElementById("manualSection").classList.add("hidden")
    document.getElementById("csvSection").classList.add("hidden")
    document.getElementById("progressSection").classList.add("hidden")
    document.getElementById("resultsSection").classList.add("hidden")
  }

  showManualSection() {
    const manualSection = document.getElementById("manualSection")
    manualSection.classList.remove("hidden")
    this.renderStudentsGrid()
  }

  renderStudentsGrid() {
    const studentsGrid = document.getElementById("studentsGrid")
    if (!studentsGrid) return

    const filteredStudents = this.getFilteredStudents()

    if (filteredStudents.length === 0) {
      studentsGrid.innerHTML = `
                <div class="no-students">
                    <div class="no-data-icon">👥</div>
                    <p>No students found in this course</p>
                </div>
            `
      return
    }

    const template = `
            {{#each students}}
            <div class="student-entry glass-panel">
                <div class="student-info">
                    <div class="student-avatar">
                        <img src="{{profileImage}}" alt="{{fullName}}" loading="lazy">
                    </div>
                    <div class="student-details">
                        <h4>{{fullName}}</h4>
                        <p>ID: {{studentId}}</p>
                        <p>{{email}}</p>
                    </div>
                </div>
                <div class="result-input">
                    <div class="form-group">
                        <label for="score_{{id}}">Score</label>
                        <input type="number" id="score_{{id}}" name="score_{{id}}" 
                               min="0" max="100" step="0.1" placeholder="0-100">
                        <div class="input-glow"></div>
                    </div>
                    <div class="grade-display" id="grade_{{id}}">
                        <!-- Grade will be calculated automatically -->
                    </div>
                </div>
            </div>
            {{/each}}
        `

    const studentsWithDefaults = filteredStudents.map((student) => ({
      ...student,
      profileImage: student.profileImage || "/placeholder.svg?height=50&width=50",
    }))

    studentsGrid.innerHTML = utils.template(template, { students: studentsWithDefaults })

    // Add score input listeners for grade calculation
    studentsGrid.querySelectorAll('input[type="number"]').forEach((input) => {
      input.addEventListener("input", (e) => {
        this.calculateGrade(e.target)
      })
    })
  }

  getFilteredStudents() {
    const searchTerm = document.getElementById("searchStudents")?.value.toLowerCase() || ""

    if (!searchTerm) return this.courseStudents

    return this.courseStudents.filter(
      (student) =>
        student.fullName.toLowerCase().includes(searchTerm) ||
        student.email.toLowerCase().includes(searchTerm) ||
        student.studentId.toLowerCase().includes(searchTerm),
    )
  }
  \
  filter;
  \
    )\
}
\
  filterStudents()
{
  \
    this.renderStudentsGrid()
}
\
  calculateGrade(input)
{
  \
  const score = Number.parseFloat(input.value)
  if (isNaN(score)) return

  const studentId = input.id.replace("score_", "")
  const gradeDisplay = document.getElementById(`grade_${studentId}`)
  if (!gradeDisplay) return

  // Use course grading system or school default
  const gradingSystem = this.selectedCourse.gradingSystem || [
    { grade: "A", min: 90, max: 100 },
    { grade: "B", min: 80, max: 89 },
    { grade: "C", min: 70, max: 79 },
    { grade: "D", min: 60, max: 69 },
    { grade: "F", min: 0, max: 59 },
  ]

  const grade = utils.formatGrade(score, gradingSystem)
  gradeDisplay.innerHTML = `<span class="grade-badge grade-${grade.toLowerCase()}">${grade}</span>`
}
\
  async handleManualSubmission()
{
  const studentsGrid = document.getElementById("studentsGrid")
  const scoreInputs = studentsGrid.querySelectorAll('input[type="number"]')

  const results = []
  let hasErrors = false

  scoreInputs.forEach((input) => {
    const studentId = input.id.replace("score_", "")
    const score = Number.parseFloat(input.value)

    if (!isNaN(score) && score >= 0 && score <= 100) {
      const student = this.courseStudents.find((s) => s.id.toString() === studentId)
      if (student) {
        results.push({
          studentId: student.id,
          score: score,
          grade: utils.formatGrade(score, this.selectedCourse.gradingSystem),
        })
      }
    } else if (input.value.trim() !== "") {
      hasErrors = true
      error.showInline(input, "Score must be between 0 and 100")
    }
  })

  if (hasErrors) {
    error.show("Validation Error", "Please fix the errors before submitting")
    return
  }

  if (results.length === 0) {
    error.show("No Results", "Please enter at least one score")
    return
  }

  await this.uploadResults(results)
}
\
  showCSVSection()
{
  \
  const csvSection = document.getElementById("csvSection")
  csvSection.classList.remove("hidden")
  this.setupCSVFileUpload()
}
\
  setupCSVFileUpload()
{
  \
  const csvFileInputContainer = document.getElementById("csvFileInputContainer")
  if (!csvFileInputContainer) return

  // Clear existing content
  csvFileInputContainer.innerHTML = ""

  const fileInput = fileUpload.createFileInput({
    accept: ".csv",
    multiple: false,
    dragDrop: true,
    preview: false,
    onFileSelect: (files) => this.handleCSVFileSelection(files),
    onError: (errors) => this.handleCSVFileErrors(errors),
  })

  csvFileInputContainer.appendChild(fileInput)
}
\
  async handleCSVFileSelection(files)
{
  if (files.length === 0) return

  const file = files[0]
  console.log("CSV file selected:", file.name)

  // Validate file
  const validation = fileUpload.validateFile(file, "csv", 5 * 1024 * 1024) // 5MB limit
  if (!validation.isValid) {
    error.show("Invalid File", validation.errors.join(", "))
    return
  }

  this.showLoading(true)

  try {
    // Parse CSV
    const data = await fileUpload.parseCSV(file)
    this.csvData = data
    this.validateCSVData()
    this.showCSVPreview()

    console.log(`Parsed ${data.length} rows from CSV`)
  } catch (err) {
    console.error("Failed to parse CSV:", err)
    error.show("CSV Parse Error", err.message)
  } finally {
    this.showLoading(false)
  }
}
\
  handleCSVFileErrors(errors)
{
  \
    error.show("File Upload Error", errors.join(", "))
}
\
  validateCSVData()
{
  \
  if (!this.csvData || this.csvData.length === 0) {
    this.validationResults = {
      isValid: false,
      errors: ["No data found in CSV file"],
      warnings: [],
      validRows: 0,
      invalidRows: 0,
    }
    return
  }

  // Check required columns
  const headers = Object.keys(this.csvData[0])
  const requiredColumns = ["Student ID", "Score"]
  const missingColumns = requiredColumns.filter((col) => !headers.includes(col))

  if (missingColumns.length > 0) {
    this.validationResults = {
      isValid: false,
      errors: [`Missing required columns: ${missingColumns.join(", ")}`],
      warnings: [],
      validRows: 0,
      invalidRows: this.csvData.length,
    }
    return
  }

  // Validate each row
  const errors = []
  const warnings = []
  let validRows = 0
  let invalidRows = 0

  this.csvData.forEach((row, index) => {
    const rowNumber = index + 1
    const rowErrors = []

    // Validate Student ID
    const studentId = row["Student ID"]
    if (!studentId || studentId.toString().trim() === "") {
      rowErrors.push(`Row ${rowNumber}: Missing Student ID`)
    } else {
      const student = this.courseStudents.find((s) => s.studentId === studentId || s.email === row["Student Email"])
      if (!student) {
        rowErrors.push(`Row ${rowNumber}: Student not found in course`)
      }
    }

    // Validate Score
    const score = Number.parseFloat(row.Score)
    if (isNaN(score)) {
      rowErrors.push(`Row ${rowNumber}: Invalid score format`)
    } else if (score < 0 || score > 100) {
      rowErrors.push(`Row ${rowNumber}: Score must be between 0 and 100`)
    }

    if (rowErrors.length > 0) {
      errors.push(...rowErrors)
      invalidRows++
    } else {
      validRows++
    }
  })

  this.validationResults = {
    isValid: errors.length === 0,
    errors,
    warnings,
    validRows,
    invalidRows,
  }

  console.log("CSV validation results:", this.validationResults)
}
\
  showCSVPreview()
{
  \
  const csvPreview = document.getElementById("csvPreview")
  csvPreview.classList.remove("hidden")

  // Update stats
  const csvPreviewStats = document.getElementById("csvPreviewStats")
  csvPreviewStats.innerHTML = `
      <div class="stat-item">
        <span class="stat-label">Total Rows:</span>
        <span class="stat-value">${this.csvData.length}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Valid:</span>
        <span class="stat-value success">${this.validationResults.validRows}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Invalid:</span>
        <span class="stat-value error">${this.validationResults.invalidRows}</span>
      </div>
    `

  // Update validation summary
  const csvValidationSummary = document.getElementById("csvValidationSummary")
  let summaryHTML = ""

  if (this.validationResults.errors.length > 0) {
    summaryHTML += `
        <div class="validation-errors">
          <h4>❌ Errors (${this.validationResults.errors.length})</h4>
          <ul>
            ${this.validationResults.errors
              .slice(0, 5)
              .map((error) => `<li>${utils.sanitizeHtml(error)}</li>`)
              .join("")}
            ${
              this.validationResults.errors.length > 5
                ? `<li>... and ${this.validationResults.errors.length - 5} more</li>`
                : ""
            }
          </ul>
        </div>
      `
  }

  if (this.validationResults.isValid) {
    summaryHTML += `
        <div class="validation-success">
          <h4>✅ Ready to Upload</h4>
          <p>All data is valid and ready for upload.</p>
        </div>
      `
  }

  csvValidationSummary.innerHTML = summaryHTML

  // Render preview table
  this.renderCSVPreviewTable()

  // Enable/disable submit button
  const csvSubmitBtn = document.getElementById("csvSubmitBtn")
  csvSubmitBtn.disabled = !this.validationResults.isValid || this.validationResults.validRows === 0
}

renderCSVPreviewTable()
{
  \
  const tbody = document.getElementById("csvPreviewTableBody")
  if (!tbody) return

  const template = `
      {{#each rows}}
      <tr class="{{#if isValid}}valid-row{{else}}invalid-row{{/if}}">
        <td>{{studentId}}</td>
        <td>{{studentName}}</td>
        <td>{{email}}</td>
        <td>{{score}}</td>
        <td>{{grade}}</td>
        <td>
          <span class="status-badge {{#if isValid}}status-valid{{else}}status-invalid{{/if}}">
            {{#if isValid}}✅ Valid{{else}}❌ Invalid{{/if}}
          </span>
        </td>
      </tr>
      {{/each}}
    `

  const rowsWithDetails = this.csvData.map((row, index) => {
    const student = this.courseStudents.find(
      (s) => s.studentId === row["Student ID"] || s.email === row["Student Email"],
    )
    const score = Number.parseFloat(row.Score)
    const isValid = !isNaN(score) && score >= 0 && score <= 100 && student

    return {
      studentId: row["Student ID"] || "N/A",
      studentName: student ? student.fullName : "Not Found",
      email: row["Student Email"] || student?.email || "N/A",
      score: isNaN(score) ? row.Score : score,
      grade: isValid ? utils.formatGrade(score, this.selectedCourse.gradingSystem) : "N/A",
      isValid,
    }
  })

  tbody.innerHTML = utils.template(template, { rows: rowsWithDetails })
}
\
  async handleCSVSubmission()
{
  if (!this.validationResults.isValid) {
    error.show("Cannot Upload", "Please fix validation errors before uploading")
    return
  }

  // Prepare results data
  const results = []
  this.csvData.forEach((row) => {
    const student = this.courseStudents.find(
      (s) => s.studentId === row["Student ID"] || s.email === row["Student Email"],
    )
    const score = Number.parseFloat(row.Score)

    if (student && !isNaN(score) && score >= 0 && score <= 100) {
      results.push({
        studentId: student.id,
        score: score,
        grade: utils.formatGrade(score, this.selectedCourse.gradingSystem),
      })
    }
  })

  await this.uploadResults(results)
}
\
  async uploadResults(results)
{
  if (!this.selectedCourse || results.length === 0) return

  // Show progress section
  this.showProgressSection()

  console.log(`Starting upload of ${results.length} results`)

  // Initialize progress
  this.updateProgress(0, results.length, 0, 0, 0)

  const uploadResults = {
    successful: [],
    failed: [],
  }

  // Upload results in batches
  const batchSize = 20
  for (let i = 0; i < results.length; i += batchSize) {
    const batch = results.slice(i, i + batchSize)

    try {
      const response = await api.uploadStudentResults(this.selectedCourse.id, {
        results: batch,
      })

      if (response.success) {
        uploadResults.successful.push(...(response.data?.successful || batch))
        uploadResults.failed.push(...(response.data?.failed || []))
      } else {
        // Mark all in batch as failed
        batch.forEach((result) => {
          uploadResults.failed.push({
            ...result,
            error: response.message || "Upload failed",
          })
        })
      }

      // Update progress
      const processed = Math.min(i + batchSize, results.length)
      this.updateProgress(
        processed,
        results.length,
        uploadResults.successful.length,
        uploadResults.failed.length,
        processed,
      )

      // Add delay between batches
      if (i + batchSize < results.length) {
        await new Promise((resolve) => setTimeout(resolve, 500))
      }
    } catch (err) {
      console.error("Batch upload failed:", err)
      // Mark all in batch as failed
      batch.forEach((result) => {
        uploadResults.failed.push({
          ...result,
          error: err.message || "Upload failed",
        })
      })
    }
  }

  this.uploadResults = uploadResults
  this.showResultsSection()

  console.log("Upload completed:", uploadResults)
}

showProgressSection()
{
  \
    this.hideAllUploadSections()
  const progressSection = document.getElementById("progressSection")
  progressSection.classList.remove("hidden")
}

updateProgress(processed, total, successful, failed, current)
{
  \
  const percentage = total > 0 ? Math.round((processed / total) * 100) : 0

  // Update progress bar
  const progressFill = document.getElementById("progressFill")
  const progressText = document.getElementById("progressText")
  progressFill.style.width = `${percentage}%`
  progressText.textContent = `${percentage}%`

  // Update progress details
  document.getElementById("totalResults").textContent = total
  document.getElementById("uploadedResults").textContent = processed
  document.getElementById("successfulResults").textContent = successful
  document.getElementById("failedResults").textContent = failed

  // Add to progress log
  const progressLog = document.getElementById("progressLog")
  if (current > 0) {
    const logEntry = document.createElement("div")
    logEntry.className = "log-entry"
    logEntry.innerHTML = `
        <span class="log-time">${new Date().toLocaleTimeString()}</span>
        <span class="log-message">Uploaded ${processed}/${total} results</span>
      `
    progressLog.appendChild(logEntry)
    progressLog.scrollTop = progressLog.scrollHeight
  }
}

showResultsSection()
{
  \
    this.hideAllUploadSections()
  const resultsSection = document.getElementById("resultsSection")
  resultsSection.classList.remove("hidden")

  // Update results summary
  const resultsSummary = document.getElementById("resultsSummary")
  const total = this.uploadResults.successful.length + this.uploadResults.failed.length
  const successRate = total > 0 ? Math.round((this.uploadResults.successful.length / total) * 100) : 0

  resultsSummary.innerHTML = `
      <div class="summary-card success">
        <div class="summary-icon">✅</div>
        <div class="summary-content">
          <h3>${this.uploadResults.successful.length}</h3>
          <p>Results Uploaded Successfully</p>
        </div>
      </div>
      <div class="summary-card error">
        <div class="summary-icon">❌</div>
        <div class="summary-content">
          <h3>${this.uploadResults.failed.length}</h3>
          <p>Upload Failures</p>
        </div>
      </div>
      <div class="summary-card info">
        <div class="summary-icon">📊</div>
        <div class="summary-content">
          <h3>${successRate}%</h3>
          <p>Success Rate</p>
        </div>
      </div>
    `

  // Update tab counts
  document.getElementById("successfulCount").textContent = this.uploadResults.successful.length
  document.getElementById("failedCount").textContent = this.uploadResults.failed.length

  // Render results tables
  this.renderResultsTables()
}

renderResultsTables()
{
  \
  // Render successful uploads
  const successfulTableBody = document.getElementById("successfulTableBody")
  if (successfulTableBody) {
    successfulTableBody.innerHTML = this.uploadResults.successful
      .map((result) => {
        const student = this.courseStudents.find((s) => s.id === result.studentId)
        return `
          <tr>
            <td>${utils.sanitizeHtml(student?.fullName || "Unknown")}</td>
            <td>${utils.sanitizeHtml(student?.studentId || result.studentId)}</td>
            <td>${result.score}</td>
            <td><span class="grade-badge grade-${result.grade.toLowerCase()}">${result.grade}</span></td>
            <td><span class="status-badge status-success">✅ Uploaded</span></td>
          </tr>
        `
      })
      .join("")
  }

  // Render failed uploads
  const failedTableBody = document.getElementById("failedTableBody")
  if (failedTableBody) {
    failedTableBody.innerHTML = this.uploadResults.failed
      .map((failure) => {
        const student = this.courseStudents.find((s) => s.id === failure.studentId)
        return `
          <tr>
            <td>${utils.sanitizeHtml(student?.studentId || failure.studentId || "N/A")}</td>
            <td>${utils.sanitizeHtml(student?.fullName || "Unknown")}</td>
            <td>${failure.score || "N/A"}</td>
            <td class="error-message">${utils.sanitizeHtml(failure.error)}</td>
          </tr>
        `
      })
      .join("")
  }
}

switchResultsTab(tabName)
{
  \
  // Update tab buttons
  const tabBtns = document.querySelectorAll(".tab-btn")
  tabBtns.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabName)
  })

  // Update tab panels
  const tabPanels = document.querySelectorAll(".tab-panel")
  tabPanels.forEach((panel) => {
    panel.classList.toggle("active", panel.id === `${tabName}Tab`)
  })
}

resetCSVUpload()
{
  \
    this.csvData = []
    this.validationResults = null

  const csvPreview = document.getElementById("csvPreview")
  csvPreview.classList.add("hidden")

  this.setupCSVFileUpload()
}

resetUpload()
{
  \
    // Reset all data
    this.selectedCourse = null
    this.courseStudents = []
    this.uploadMethod = null
    this.csvData = []
    this.validationResults = null
    this.uploadResults = null

    // Reset UI
    document.getElementById("courseSelect").value = ""
    document.getElementById("courseInfo").innerHTML = ""
    this.hideMethodSection()

    console.log("Upload reset")
}

downloadTemplate()
{
  \
  if (!this.selectedCourse || this.courseStudents.length === 0) {
    error.show("No Course Selected", "Please select a course first")
    return
  }

  const headers = ["Student ID", "Student Email", "Score", "Grade"]
  let csvContent = headers.join(",") + "\n"

  // Add sample data for first few students
  const sampleStudents = this.courseStudents.slice(0, 3)
  sampleStudents.forEach((student) => {
    csvContent += `${student.studentId},${student.email},,\n`
  })

  // Create and download file
  const blob = new Blob([csvContent], { type: "text/csv" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `${this.selectedCourse.code}_results_template.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  console.log("Template downloaded")
}

downloadResults()
{
  if (!this.uploadResults) return

  const results = {
    course: {
      id: this.selectedCourse.id,
      code: this.selectedCourse.code,
      title: this.selectedCourse.title,
      className: this.selectedCourse.className,
    },
    summary: {
      totalProcessed: this.uploadResults.successful.length + this.uploadResults.failed.length,
      successful: this.uploadResults.successful.length,
      failed: this.uploadResults.failed.length,
      timestamp: new Date().toISOString(),
    },
    successful: this.uploadResults.successful,
    failed: this.uploadResults.failed,
  }

  const blob = new Blob([JSON.stringify(results, null, 2)], {
    type: "application/json",
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `${this.selectedCourse.code}_upload_results_${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  console.log("Results downloaded")
}

showLoading(show)
{
  const loadingOverlay = document.getElementById("loadingOverlay")
  if (loadingOverlay) {
    loadingOverlay.classList.toggle("active", show)
  }
}


// Initialize when DOM is loaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => new ResultUpload())
} else {
  new ResultUpload()
}

export const resultUpload = new ResultUpload()
