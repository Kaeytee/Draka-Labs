import { api } from "./api.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"
import { navigation } from "./navigation.js"
import { auth } from "./auth.js"

class StudentDashboard {
  constructor() {
    this.studentGrades = []
    this.studentProfile = null
    this.init()
  }

  async init() {
    // Check permissions
    if (!roleAccess.hasPermission("view_dashboard")) {
      window.location.href = "error.html?code=403&message=Access denied"
      return
    }

    this.setupEventListeners()
    navigation.setupDashboardNavigation()
    navigation.setupMobileNavigation()
    await this.loadStudentData()

    console.log("Student dashboard initialized")
  }

  setupEventListeners() {
    // Logout button
    const logoutBtn = document.getElementById("logoutBtn")
    logoutBtn?.addEventListener("click", () => {
      if (confirm("Are you sure you want to logout?")) {
        auth.logout()
      }
    })

    // Edit profile button
    const editProfileBtn = document.getElementById("editProfileBtn")
    editProfileBtn?.addEventListener("click", () => {
      this.showEditProfileModal()
    })

    // View all grades button
    const viewAllBtn = document.querySelector(".view-all-btn")
    viewAllBtn?.addEventListener("click", () => {
      navigation.loadSectionContent("grades")
    })
  }

  async loadStudentData() {
    this.showLoading(true)

    try {
      const user = auth.getUser()

      // Load student grades and profile in parallel
      const [gradesResponse, profileResponse] = await Promise.all([
        api.getStudentGrades(user.id),
        api.get(`/students/${user.id}/profile`),
      ])

      this.studentGrades = gradesResponse.data || []
      this.studentProfile = profileResponse.data || user

      this.updateStudentInfo()
      this.renderRecentGrades()
      this.updateAcademicInfo()

      console.log(`Loaded ${this.studentGrades.length} grades for student`)
    } catch (err) {
      console.error("Failed to load student data:", err)
      error.handleApiError(err, "Loading student data")
    } finally {
      this.showLoading(false)
    }
  }

  updateStudentInfo() {
    const user = auth.getUser()
    if (!user) return

    // Update navigation user info
    const userName = document.getElementById("userName")
    const avatarImg = document.getElementById("avatarImg")

    if (userName) {
      userName.textContent = user.fullName || user.name || "Student"
    }

    if (avatarImg && user.profileImage) {
      avatarImg.src = user.profileImage
    }

    // Update profile card
    const studentName = document.getElementById("studentName")
    const studentId = document.getElementById("studentId")
    const studentClass = document.getElementById("studentClass")
    const profileImage = document.getElementById("profileImage")

    if (studentName) {
      studentName.textContent = this.studentProfile.fullName || user.fullName || "Student"
    }

    if (studentId) {
      studentId.textContent = `Student ID: ${this.studentProfile.studentId || user.studentId || "#12345"}`
    }

    if (studentClass) {
      studentClass.textContent = `Class: ${this.studentProfile.className || "Not Assigned"}`
    }

    if (profileImage) {
      profileImage.src = this.studentProfile.profileImage || user.profileImage || "/placeholder.svg?height=80&width=80"
    }
  }

  renderRecentGrades() {
    const gradesSummary = document.getElementById("gradesSummary")
    if (!gradesSummary) return

    // Show recent grades (last 5)
    const recentGrades = this.studentGrades.slice(0, 5)

    if (recentGrades.length === 0) {
      gradesSummary.innerHTML = `
        <div class="no-grades">
          <div class="no-data-icon">📊</div>
          <p>No grades available yet</p>
        </div>
      `
      return
    }

    const template = `
      {{#each grades}}
      <div class="grade-item">
        <div class="grade-course">
          <span class="course-code">{{courseCode}}</span>
          <span class="course-title">{{courseTitle}}</span>
        </div>
        <div class="grade-score">
          <span class="score">{{score}}</span>
          <span class="grade grade-{{gradeLower}}">{{grade}}</span>
        </div>
      </div>
      {{/each}}
    `

    const gradesWithFormatting = recentGrades.map((grade) => ({
      ...grade,
      gradeLower: grade.grade?.toLowerCase() || "n",
    }))

    gradesSummary.innerHTML = utils.template(template, { grades: gradesWithFormatting })
  }

  updateAcademicInfo() {
    // Calculate GPA
    const gpa = this.calculateGPA()
    const totalCourses = this.studentGrades.length
    const completedCourses = this.studentGrades.filter((g) => g.grade && g.grade !== "F").length

    // Update academic info
    const gpaValue = document.getElementById("gpaValue")
    const totalCoursesElement = document.getElementById("totalCourses")
    const completedCoursesElement = document.getElementById("completedCourses")

    if (gpaValue) {
      gpaValue.textContent = gpa ? gpa.toFixed(2) : "-"
    }

    if (totalCoursesElement) {
      totalCoursesElement.textContent = totalCourses
    }

    if (completedCoursesElement) {
      completedCoursesElement.textContent = completedCourses
    }
  }

  calculateGPA() {
    if (this.studentGrades.length === 0) return null

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
    let totalCourses = 0

    this.studentGrades.forEach((grade) => {
      if (grade.grade && gradePoints.hasOwnProperty(grade.grade)) {
        totalPoints += gradePoints[grade.grade] * (grade.creditHours || 1)
        totalCourses += grade.creditHours || 1
      }
    })

    return totalCourses > 0 ? totalPoints / totalCourses : null
  }

  showEditProfileModal() {
    // This would show a modal for editing profile
    utils.showNotification("Profile editing feature coming soon!", "info")
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
  document.addEventListener("DOMContentLoaded", () => new StudentDashboard())
} else {
  new StudentDashboard()
}

export const studentDashboard = new StudentDashboard()
