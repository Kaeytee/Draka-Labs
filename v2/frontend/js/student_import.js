import { api } from "./api.js"
import { validation } from "./validation.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"
import { fileUpload } from "./file_upload.js"

class StudentImport {
  constructor() {
    this.importData = []
    this.classes = []
    this.validationResults = null
    this.importResults = null
    this.currentPreviewPage = 1
    this.previewItemsPerPage = 10
    this.requiredColumns = ["Full Name", "Date of Birth", "Gender", "Email"]
    this.optionalColumns = ["Class ID", "Phone", "Address", "Parent Name", "Parent Phone"]
    this.init()
  }

  async init() {
    // Check permissions
    if (!roleAccess.hasPermission("import_students")) {
      window.location.href = "error.html?code=403&message=Access denied"
      return
    }

    this.setupEventListeners()
    this.setupFileUpload()
    await this.loadClasses()

    console.log("Student import initialized")
  }

  async loadClasses() {
    try {
      const response = await api.getClasses()
      this.classes = response.data || []
      this.populateClassDropdown()
      console.log(`Loaded ${this.classes.length} classes`)
    } catch (err) {
      console.error("Failed to load classes:", err)
      error.handleApiError(err, "Loading classes")
    }
  }

  populateClassDropdown() {
    const classSelect = document.getElementById("defaultClassSelect")
    if (!classSelect) return

    classSelect.innerHTML = '<option value="">Select default class for students without Class ID</option>'
    this.classes.forEach((cls) => {
      const option = document.createElement("option")
      option.value = cls.id
      option.textContent = `${cls.name} (${cls.schoolName || "Unknown School"})`
      classSelect.appendChild(option)
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

    // Toggle instructions
    const toggleInstructionsBtn = document.getElementById("toggleInstructionsBtn")
    const instructionsContent = document.getElementById("instructionsContent")
    toggleInstructionsBtn?.addEventListener("click", () => {
      const isVisible = instructionsContent.style.display !== "none"
      instructionsContent.style.display = isVisible ? "none" : "block"
      toggleInstructionsBtn.querySelector(".toggle-icon").textContent = isVisible ? "+" : "−"
    })

    // Import button
    const importBtn = document.getElementById("importBtn")
    importBtn?.addEventListener("click", () => {
      this.startImport()
    })

    // Cancel button
    const cancelBtn = document.getElementById("cancelBtn")
    cancelBtn?.addEventListener("click", () => {
      this.cancelImport()
    })

    // New import button
    const newImportBtn = document.getElementById("newImportBtn")
    newImportBtn?.addEventListener("click", () => {
      this.resetImport()
    })

    // Download results button
    const downloadResultsBtn = document.getElementById("downloadResultsBtn")
    downloadResultsBtn?.addEventListener("click", () => {
      this.downloadResults()
    })

    // Preview pagination
    const prevPreviewBtn = document.getElementById("prevPreviewBtn")
    const nextPreviewBtn = document.getElementById("nextPreviewBtn")
    prevPreviewBtn?.addEventListener("click", () => {
      if (this.currentPreviewPage > 1) {
        this.currentPreviewPage--
        this.renderPreviewTable()
      }
    })
    nextPreviewBtn?.addEventListener("click", () => {
      const totalPages = Math.ceil(this.importData.length / this.previewItemsPerPage)
      if (this.currentPreviewPage < totalPages) {
        this.currentPreviewPage++
        this.renderPreviewTable()
      }
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

  setupFileUpload() {
    const fileInputContainer = document.getElementById("fileInputContainer")
    if (!fileInputContainer) return

    const fileInput = fileUpload.createFileInput({
      accept: ".csv,.xlsx,.xls",
      multiple: false,
      dragDrop: true,
      preview: false,
      onFileSelect: (files) => this.handleFileSelection(files),
      onError: (errors) => this.handleFileErrors(errors),
    })

    fileInputContainer.appendChild(fileInput)
  }

  async handleFileSelection(files) {
    if (files.length === 0) return

    const file = files[0]
    console.log("File selected:", file.name)

    // Validate file
    const validation = fileUpload.validateFile(file, "csv", 10 * 1024 * 1024) // 10MB limit
    if (!validation.isValid) {
      error.show("Invalid File", validation.errors.join(", "))
      return
    }

    this.showLoading(true)

    try {
      // Parse file
      let data
      if (file.name.toLowerCase().endsWith(".csv")) {
        data = await fileUpload.parseCSV(file)
      } else {
        // For Excel files, you would need a library like SheetJS
        throw new Error("Excel file parsing not implemented in this demo")
      }

      this.importData = data
      this.validateImportData()
      this.showPreviewSection()
      this.renderPreviewTable()

      console.log(`Parsed ${data.length} rows from file`)
    } catch (err) {
      console.error("Failed to parse file:", err)
      error.show("File Parse Error", err.message)
    } finally {
      this.showLoading(false)
    }
  }

  handleFileErrors(errors) {
    error.show("File Upload Error", errors.join(", "))
  }

  validateImportData() {
    if (!this.importData || this.importData.length === 0) {
      this.validationResults = {
        isValid: false,
        errors: ["No data found in file"],
        warnings: [],
        validRows: 0,
        invalidRows: 0,
      }
      return
    }

    // Check required columns
    const headers = Object.keys(this.importData[0])
    const missingColumns = this.requiredColumns.filter((col) => !headers.includes(col))

    if (missingColumns.length > 0) {
      this.validationResults = {
        isValid: false,
        errors: [`Missing required columns: ${missingColumns.join(", ")}`],
        warnings: [],
        validRows: 0,
        invalidRows: this.importData.length,
      }
      return
    }

    // Validate each row
    const errors = []
    const warnings = []
    let validRows = 0
    let invalidRows = 0

    this.importData.forEach((row, index) => {
      const rowNumber = index + 1
      const rowErrors = []

      // Validate required fields
      this.requiredColumns.forEach((col) => {
        if (!row[col] || row[col].toString().trim() === "") {
          rowErrors.push(`Row ${rowNumber}: Missing ${col}`)
        }
      })

      // Validate email format
      if (row.Email && !validation.isValidEmail(row.Email)) {
        rowErrors.push(`Row ${rowNumber}: Invalid email format`)
      }

      // Validate date of birth
      if (row["Date of Birth"]) {
        const date = new Date(row["Date of Birth"])
        if (isNaN(date.getTime())) {
          rowErrors.push(`Row ${rowNumber}: Invalid date of birth format`)
        }
      }

      // Validate gender
      if (row.Gender && !["Male", "Female", "Other", "M", "F", "O"].includes(row.Gender)) {
        warnings.push(`Row ${rowNumber}: Unusual gender value "${row.Gender}"`)
      }

      // Validate class ID if provided
      if (row["Class ID"]) {
        const classId = Number.parseInt(row["Class ID"])
        if (isNaN(classId) || !this.classes.find((c) => c.id === classId)) {
          rowErrors.push(`Row ${rowNumber}: Invalid Class ID "${row["Class ID"]}"`)
        }
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

    console.log("Validation results:", this.validationResults)
  }

  showPreviewSection() {
    const previewSection = document.getElementById("previewSection")
    previewSection.classList.remove("hidden")

    // Update stats
    const previewStats = document.getElementById("previewStats")
    previewStats.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Total Rows:</span>
                <span class="stat-value">${this.importData.length}</span>
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
    const validationSummary = document.getElementById("validationSummary")
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
                        ${this.validationResults.errors.length > 5 ? `<li>... and ${this.validationResults.errors.length - 5} more</li>` : ""}
                    </ul>
                </div>
            `
    }

    if (this.validationResults.warnings.length > 0) {
      summaryHTML += `
                <div class="validation-warnings">
                    <h4>⚠️ Warnings (${this.validationResults.warnings.length})</h4>
                    <ul>
                        ${this.validationResults.warnings
                          .slice(0, 3)
                          .map((warning) => `<li>${utils.sanitizeHtml(warning)}</li>`)
                          .join("")}
                        ${this.validationResults.warnings.length > 3 ? `<li>... and ${this.validationResults.warnings.length - 3} more</li>` : ""}
                    </ul>
                </div>
            `
    }

    if (this.validationResults.isValid) {
      summaryHTML += `
                <div class="validation-success">
                    <h4>✅ Ready to Import</h4>
                    <p>All data is valid and ready for import.</p>
                </div>
            `
    }

    validationSummary.innerHTML = summaryHTML

    // Enable/disable import button
    const importBtn = document.getElementById("importBtn")
    importBtn.disabled = !this.validationResults.isValid || this.validationResults.validRows === 0
  }

  renderPreviewTable() {
    const table = document.getElementById("previewTable")
    const thead = document.getElementById("previewTableHead")
    const tbody = document.getElementById("previewTableBody")

    if (!table || !thead || !tbody || this.importData.length === 0) return

    // Render headers
    const headers = Object.keys(this.importData[0])
    thead.innerHTML = `
            <tr>
                <th>Row</th>
                ${headers.map((header) => `<th>${utils.sanitizeHtml(header)}</th>`).join("")}
                <th>Status</th>
            </tr>
        `

    // Calculate pagination
    const totalPages = Math.ceil(this.importData.length / this.previewItemsPerPage)
    const startIndex = (this.currentPreviewPage - 1) * this.previewItemsPerPage
    const endIndex = Math.min(startIndex + this.previewItemsPerPage, this.importData.length)
    const pageData = this.importData.slice(startIndex, endIndex)

    // Render rows
    tbody.innerHTML = pageData
      .map((row, index) => {
        const actualRowIndex = startIndex + index
        const rowNumber = actualRowIndex + 1
        const isValid = this.isRowValid(row, actualRowIndex)

        return `
                <tr class="${isValid ? "valid-row" : "invalid-row"}">
                    <td>${rowNumber}</td>
                    ${headers.map((header) => `<td>${utils.sanitizeHtml(row[header] || "")}</td>`).join("")}
                    <td>
                        <span class="status-badge ${isValid ? "status-valid" : "status-invalid"}">
                            ${isValid ? "✅ Valid" : "❌ Invalid"}
                        </span>
                    </td>
                </tr>
            `
      })
      .join("")

    // Update pagination info
    const paginationInfo = document.getElementById("previewPaginationInfo")
    paginationInfo.textContent = `Showing ${startIndex + 1}-${endIndex} of ${this.importData.length}`

    // Update pagination buttons
    const prevBtn = document.getElementById("prevPreviewBtn")
    const nextBtn = document.getElementById("nextPreviewBtn")
    prevBtn.disabled = this.currentPreviewPage <= 1
    nextBtn.disabled = this.currentPreviewPage >= totalPages
  }

  isRowValid(row, index) {
    // Check if this row has any validation errors
    const rowNumber = index + 1
    return !this.validationResults.errors.some((error) => error.includes(`Row ${rowNumber}:`))
  }

  async startImport() {
    if (!this.validationResults.isValid) {
      error.show("Cannot Import", "Please fix validation errors before importing")
      return
    }

    // Show progress section
    this.showProgressSection()

    // Get default class ID
    const defaultClassId = document.getElementById("defaultClassSelect").value

    // Prepare import data
    const studentsToImport = this.importData.filter((row, index) => this.isRowValid(row, index))

    console.log(`Starting import of ${studentsToImport.length} students`)

    // Initialize progress
    this.updateProgress(0, studentsToImport.length, 0, 0, 0)

    const results = {
      successful: [],
      failed: [],
    }

    // Import students in batches
    const batchSize = 10
    for (let i = 0; i < studentsToImport.length; i += batchSize) {
      const batch = studentsToImport.slice(i, i + batchSize)

      try {
        const batchResults = await this.importBatch(batch, defaultClassId)
        results.successful.push(...batchResults.successful)
        results.failed.push(...batchResults.failed)

        // Update progress
        const processed = Math.min(i + batchSize, studentsToImport.length)
        this.updateProgress(
          processed,
          studentsToImport.length,
          results.successful.length,
          results.failed.length,
          processed,
        )

        // Add delay between batches to avoid overwhelming the server
        if (i + batchSize < studentsToImport.length) {
          await new Promise((resolve) => setTimeout(resolve, 1000))
        }
      } catch (err) {
        console.error("Batch import failed:", err)
        // Mark all students in this batch as failed
        batch.forEach((student, index) => {
          results.failed.push({
            row: i + index + 1,
            data: student,
            error: err.message || "Import failed",
          })
        })
      }
    }

    this.importResults = results
    this.showResultsSection()

    console.log("Import completed:", results)
  }

  async importBatch(students, defaultClassId) {
    const importData = {
      students: students.map((student) => ({
        fullName: student["Full Name"],
        dateOfBirth: student["Date of Birth"],
        gender: student.Gender,
        email: student.Email,
        phone: student.Phone || "",
        address: student.Address || "",
        parentName: student["Parent Name"] || "",
        parentPhone: student["Parent Phone"] || "",
        classId: student["Class ID"]
          ? Number.parseInt(student["Class ID"])
          : defaultClassId
            ? Number.parseInt(defaultClassId)
            : null,
      })),
    }

    try {
      const response = await api.importStudents(importData)
      return {
        successful: response.data?.successful || [],
        failed: response.data?.failed || [],
      }
    } catch (err) {
      throw err
    }
  }

  showProgressSection() {
    const previewSection = document.getElementById("previewSection")
    const progressSection = document.getElementById("progressSection")

    previewSection.classList.add("hidden")
    progressSection.classList.remove("hidden")
  }

  updateProgress(processed, total, successful, failed, current) {
    const percentage = total > 0 ? Math.round((processed / total) * 100) : 0

    // Update progress bar
    const progressFill = document.getElementById("progressFill")
    const progressText = document.getElementById("progressText")
    progressFill.style.width = `${percentage}%`
    progressText.textContent = `${percentage}%`

    // Update progress details
    document.getElementById("totalStudents").textContent = total
    document.getElementById("processedStudents").textContent = processed
    document.getElementById("successfulStudents").textContent = successful
    document.getElementById("failedStudents").textContent = failed

    // Add to progress log
    const progressLog = document.getElementById("progressLog")
    if (current > 0) {
      const logEntry = document.createElement("div")
      logEntry.className = "log-entry"
      logEntry.innerHTML = `
                <span class="log-time">${new Date().toLocaleTimeString()}</span>
                <span class="log-message">Processed ${processed}/${total} students</span>
            `
      progressLog.appendChild(logEntry)
      progressLog.scrollTop = progressLog.scrollHeight
    }
  }

  showResultsSection() {
    const progressSection = document.getElementById("progressSection")
    const resultsSection = document.getElementById("resultsSection")

    progressSection.classList.add("hidden")
    resultsSection.classList.remove("hidden")

    // Update results summary
    const resultsSummary = document.getElementById("resultsSummary")
    const total = this.importResults.successful.length + this.importResults.failed.length
    const successRate = total > 0 ? Math.round((this.importResults.successful.length / total) * 100) : 0

    resultsSummary.innerHTML = `
            <div class="summary-card success">
                <div class="summary-icon">✅</div>
                <div class="summary-content">
                    <h3>${this.importResults.successful.length}</h3>
                    <p>Students Imported Successfully</p>
                </div>
            </div>
            <div class="summary-card error">
                <div class="summary-icon">❌</div>
                <div class="summary-content">
                    <h3>${this.importResults.failed.length}</h3>
                    <p>Import Failures</p>
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
    document.getElementById("successfulCount").textContent = this.importResults.successful.length
    document.getElementById("failedCount").textContent = this.importResults.failed.length

    // Render results tables
    this.renderResultsTables()
  }

  renderResultsTables() {
    // Render successful imports
    const successfulTableBody = document.getElementById("successfulTableBody")
    if (successfulTableBody) {
      successfulTableBody.innerHTML = this.importResults.successful
        .map(
          (student) => `
                <tr>
                    <td>${utils.sanitizeHtml(student.fullName || student.name)}</td>
                    <td>${utils.sanitizeHtml(student.email)}</td>
                    <td>${utils.sanitizeHtml(student.className || "N/A")}</td>
                    <td>${utils.sanitizeHtml(student.studentId || student.id)}</td>
                    <td><span class="status-badge status-success">✅ Imported</span></td>
                </tr>
            `,
        )
        .join("")
    }

    // Render failed imports
    const failedTableBody = document.getElementById("failedTableBody")
    if (failedTableBody) {
      failedTableBody.innerHTML = this.importResults.failed
        .map(
          (failure) => `
                <tr>
                    <td>${failure.row || "N/A"}</td>
                    <td>${utils.sanitizeHtml(failure.data?.["Full Name"] || "N/A")}</td>
                    <td>${utils.sanitizeHtml(failure.data?.Email || "N/A")}</td>
                    <td class="error-message">${utils.sanitizeHtml(failure.error)}</td>
                </tr>
            `,
        )
        .join("")
    }
  }

  switchResultsTab(tabName) {
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

  cancelImport() {
    this.resetImport()
  }

  resetImport() {
    // Reset data
    this.importData = []
    this.validationResults = null
    this.importResults = null
    this.currentPreviewPage = 1

    // Hide sections
    document.getElementById("previewSection").classList.add("hidden")
    document.getElementById("progressSection").classList.add("hidden")
    document.getElementById("resultsSection").classList.add("hidden")

    // Reset file input
    const fileInputContainer = document.getElementById("fileInputContainer")
    fileInputContainer.innerHTML = ""
    this.setupFileUpload()

    console.log("Import reset")
  }

  downloadTemplate() {
    const headers = [...this.requiredColumns, ...this.optionalColumns]
    const csvContent = headers.join(",") + "\n"

    // Add sample data
    const sampleData = [
      "John Doe,1995-05-15,Male,john.doe@email.com,1,+1234567890,123 Main St,Jane Doe,+1234567891",
      "Jane Smith,1996-08-22,Female,jane.smith@email.com,1,+1234567892,456 Oak Ave,Bob Smith,+1234567893",
    ]

    const fullContent = csvContent + sampleData.join("\n")

    // Create and download file
    const blob = new Blob([fullContent], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "student_import_template.csv"
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    console.log("Template downloaded")
  }

  downloadResults() {
    if (!this.importResults) return

    const results = {
      summary: {
        totalProcessed: this.importResults.successful.length + this.importResults.failed.length,
        successful: this.importResults.successful.length,
        failed: this.importResults.failed.length,
        timestamp: new Date().toISOString(),
      },
      successful: this.importResults.successful,
      failed: this.importResults.failed,
    }

    const blob = new Blob([JSON.stringify(results, null, 2)], {
      type: "application/json",
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `import_results_${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    console.log("Results downloaded")
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
  document.addEventListener("DOMContentLoaded", () => new StudentImport())
} else {
  new StudentImport()
}

export const studentImport = new StudentImport()
