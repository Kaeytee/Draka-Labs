import { api } from "./api.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"
import { auth } from "./auth.js"

class GradeView {
  constructor() {
    this.grades = []
    this.filteredGrades = []
    this.currentPage = 1
    this.itemsPerPage = 10
    this.totalPages = 1
  }

  async init() {
    // Check permissions
    if (!roleAccess.hasPermission("view_grades")) {
      return
    }

    this.setupEventListeners()
    await this.loadGrades()

    console.log("Grade view initialized")
  }

  setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById("searchGrades")
    searchInput?.addEventListener(
      "input",
      utils.debounce(() => {
        this.filterGrades()
      }, 300),
    )

    // Filter functionality
    const filterSelect = document.getElementById("filterSemester")
    filterSelect?.addEventListener("change", () => {
      this.filterGrades()
    })

    // Pagination
    const prevPageBtn = document.getElementById("prevGradesPageBtn")
    const nextPageBtn = document.getElementById("nextGradesPageBtn")

    prevPageBtn?.addEventListener("click", () => {
      if (this.currentPage > 1) {
        this.currentPage--
        this.renderGradesTable()
      }
    })

    nextPageBtn?.addEventListener("click", () => {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
        this.renderGradesTable()
      }
    })
  }

  async loadGrades() {
    try {
      const user = auth.getUser()
      const response = await api.getStudentGrades(user.id)
      this.grades = response.data || []
      this.filteredGrades = [...this.grades]
      this.renderGradesTable()
      this.updateGradesSummary()

      console.log(`Loaded ${this.grades.length} grades`)
    } catch (err) {
      console.error("Failed to load grades:", err)
      error.handleApiError(err, "Loading grades")
    }
  }

  filterGrades() {
    const searchTerm = document.getElementById("searchGrades")?.value.toLowerCase() || ""
    const semesterFilter = document.getElementById("filterSemester")?.value || "all"

    this.filteredGrades = this.grades.filter((grade) => {
      const matchesSearch =
        !searchTerm ||
        grade.courseCode.toLowerCase().includes(searchTerm) ||
        grade.courseTitle.toLowerCase().includes(searchTerm)

      const matchesSemester = semesterFilter === "all" || grade.semester === semesterFilter

      return matchesSearch && matchesSemester
    })

    this.currentPage = 1
    this.renderGradesTable()
  }

  renderGradesTable() {
    const container = document.getElementById("gradesTableContainer")
    if (!container) return

    // Calculate pagination
    this.totalPages = Math.ceil(this.filteredGrades.length / this.itemsPerPage)
    const startIndex = (this.currentPage - 1) * this.itemsPerPage
    const endIndex = startIndex + this.itemsPerPage
    const pageGrades = this.filteredGrades.slice(startIndex, endIndex)

    if (pageGrades.length === 0) {
      container.innerHTML = `
        <div class="no-grades glass-panel">
          <div class="no-data-icon">📊</div>
          <h3>No Grades Found</h3>
          <p>No grades match your current filters.</p>
        </div>
      `
      return
    }

    const template = `
      <div class="grades-table-container">
        <table class="data-table" id="gradesTable">
          <thead>
            <tr>
              <th>Course Code</th>
              <th>Course Title</th>
              <th>Score</th>
              <th>Grade</th>
              <th>Credit Hours</th>
              <th>Semester</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {{#each grades}}
            <tr>
              <td class="course-code">{{courseCode}}</td>
              <td class="course-title">{{courseTitle}}</td>
              <td class="score">{{score}}</td>
              <td>
                <span class="grade-badge grade-{{gradeLower}}">{{grade}}</span>
              </td>
              <td>{{creditHours}}</td>
              <td>{{semester}}</td>
              <td>{{formattedDate}}</td>
            </tr>
            {{/each}}
          </tbody>
        </table>
      </div>
    `

    const gradesWithFormatting = pageGrades.map((grade) => ({
      ...grade,
      gradeLower: grade.grade?.toLowerCase() || "n",
      formattedDate: utils.formatDate(grade.createdAt, "DD/MM/YYYY"),
      creditHours: grade.creditHours || 1,
    }))

    container.innerHTML = utils.template(template, { grades: gradesWithFormatting })

    // Update pagination
    this.updatePagination()
  }

  updatePagination() {
    const paginationInfo = document.getElementById("gradesPaginationInfo")
    const prevPageBtn = document.getElementById("prevGradesPageBtn")
    const nextPageBtn = document.getElementById("nextGradesPageBtn")

    if (paginationInfo) {
      const startIndex = (this.currentPage - 1) * this.itemsPerPage + 1
      const endIndex = Math.min(this.currentPage * this.itemsPerPage, this.filteredGrades.length)
      paginationInfo.textContent = `Showing ${startIndex}-${endIndex} of ${this.filteredGrades.length}`
    }

    if (prevPageBtn) {
      prevPageBtn.disabled = this.currentPage <= 1
    }

    if (nextPageBtn) {
      nextPageBtn.disabled = this.currentPage >= this.totalPages
    }
  }

  updateGradesSummary() {
    const summaryContainer = document.getElementById("gradesSummaryContainer")
    if (!summaryContainer) return

    // Calculate statistics
    const totalGrades = this.grades.length
    const averageScore = this.calculateAverageScore()
    const gpa = this.calculateGPA()
    const gradeDistribution = this.calculateGradeDistribution()

    const template = `
      <div class="grades-summary">
        <div class="summary-stats">
          <div class="stat-card glass-panel">
            <div class="stat-icon">📊</div>
            <div class="stat-content">
              <h3>{{totalGrades}}</h3>
              <p>Total Grades</p>
            </div>
          </div>
          <div class="stat-card glass-panel">
            <div class="stat-icon">📈</div>
            <div class="stat-content">
              <h3>{{averageScore}}%</h3>
              <p>Average Score</p>
            </div>
          </div>
          <div class="stat-card glass-panel">
            <div class="stat-icon">🎯</div>
            <div class="stat-content">
              <h3>{{gpa}}</h3>
              <p>GPA</p>
            </div>
          </div>
        </div>
        
        <div class="grade-distribution glass-panel">
          <h3>Grade Distribution</h3>
          <div class="distribution-chart">
            {{#each distribution}}
            <div class="distribution-item">
              <span class="grade-label grade-{{gradeLower}}">{{grade}}</span>
              <div class="distribution-bar">
                <div class="distribution-fill grade-{{gradeLower}}" style="width: {{percentage}}%"></div>
              </div>
              <span class="distribution-count">{{count}}</span>
            </div>
            {{/each}}
          </div>
        </div>
      </div>
    `

    summaryContainer.innerHTML = utils.template(template, {
      totalGrades,
      averageScore: averageScore ? averageScore.toFixed(1) : "N/A",
      gpa: gpa ? gpa.toFixed(2) : "N/A",
      distribution: gradeDistribution,
    })
  }

  calculateAverageScore() {
    if (this.grades.length === 0) return null

    const validScores = this.grades.filter((g) => g.score != null && !isNaN(g.score))
    if (validScores.length === 0) return null

    const total = validScores.reduce((sum, grade) => sum + Number.parseFloat(grade.score), 0)
    return total / validScores.length
  }

  calculateGPA() {
    if (this.grades.length === 0) return null

    const gradePoints = {
      A: 4.0,
      "A+": 4.0,
      "A-": 3.7,
      B: 3.0,
      "B+": 3.3,
      "B-": 2.7,
      C: 2.0,
      "C+": 2.3,
      "C-": 1.7,
      D: 1.0,
      "D+": 1.3,
      "D-": 0.7,
      F: 0.0,
    }

    let totalPoints = 0
    let totalCredits = 0

    this.grades.forEach((grade) => {
      if (grade.grade && gradePoints.hasOwnProperty(grade.grade)) {
        const credits = grade.creditHours || 1
        totalPoints += gradePoints[grade.grade] * credits
        totalCredits += credits
      }
    })

    return totalCredits > 0 ? totalPoints / totalCredits : null
  }

  calculateGradeDistribution() {
    const distribution = {}
    const gradeOrder = ["A", "B", "C", "D", "F"]

    // Initialize distribution
    gradeOrder.forEach((grade) => {
      distribution[grade] = 0
    })

    // Count grades
    this.grades.forEach((grade) => {
      if (grade.grade) {
        const baseGrade = grade.grade.charAt(0) // Get base grade (A, B, C, D, F)
        if (distribution.hasOwnProperty(baseGrade)) {
          distribution[baseGrade]++
        }
      }
    })

    // Convert to array with percentages
    const total = this.grades.length
    return gradeOrder.map((grade) => ({
      grade,
      gradeLower: grade.toLowerCase(),
      count: distribution[grade],
      percentage: total > 0 ? (distribution[grade] / total) * 100 : 0,
    }))
  }
}

export const gradeView = new GradeView()

document.addEventListener("DOMContentLoaded", () => {
  const backBtn = document.getElementById("backBtn")
  backBtn?.addEventListener("click", () => {
    window.history.back()
  })

  // Example: Load grade details (replace with real logic)
  const gradeDetails = document.getElementById("gradeDetails")
  if (gradeDetails && gradeDetails.textContent.trim() === "") {
    gradeDetails.textContent = "Grade details will appear here."
  }
})
