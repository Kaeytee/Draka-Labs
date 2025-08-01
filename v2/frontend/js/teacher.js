import { api } from "./api.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"
import { navigation } from "./navigation.js"
import { auth } from "./auth.js"

class TeacherDashboard {
  constructor() {
    this.teacherCourses = []
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
    await this.loadTeacherData()

    console.log("Teacher dashboard initialized")
  }

  setupEventListeners() {
    // Logout button
    const logoutBtn = document.getElementById("logoutBtn")
    logoutBtn?.addEventListener("click", () => {
      if (confirm("Are you sure you want to logout?")) {
        auth.logout()
      }
    })

    // Action cards
    const actionCards = document.querySelectorAll(".action-card")
    actionCards.forEach((card) => {
      card.addEventListener("click", () => {
        const action = card.dataset.action
        this.handleActionCard(action)
      })
    })
  }

  async loadTeacherData() {
    this.showLoading(true)

    try {
      const user = auth.getUser()
      const response = await api.getTeacherCourses(user.id)
      this.teacherCourses = response.data || []

      this.updateUserInfo()
      this.renderCourseCards()

      console.log(`Loaded ${this.teacherCourses.length} courses for teacher`)
    } catch (err) {
      console.error("Failed to load teacher data:", err)
      error.handleApiError(err, "Loading teacher data")
    } finally {
      this.showLoading(false)
    }
  }

  updateUserInfo() {
    const user = auth.getUser()
    if (!user) return

    const userName = document.getElementById("userName")
    const teacherName = document.getElementById("teacherName")
    const avatarImg = document.getElementById("avatarImg")

    if (userName) {
      userName.textContent = user.fullName || user.name || "Teacher"
    }

    if (teacherName) {
      teacherName.textContent = user.fullName || user.name || "Teacher"
    }

    if (avatarImg && user.profileImage) {
      avatarImg.src = user.profileImage
    }
  }

  renderCourseCards() {
    const coursesGrid = document.getElementById("coursesGrid")
    if (!coursesGrid) return

    if (this.teacherCourses.length === 0) {
      coursesGrid.innerHTML = `
        <div class="no-courses glass-panel">
          <div class="no-data-icon">📚</div>
          <h3>No Courses Assigned</h3>
          <p>You haven't been assigned to any courses yet. Contact your administrator.</p>
        </div>
      `
      return
    }

    const template = `
      {{#each courses}}
      <div class="course-card glass-panel" data-course-id="{{id}}">
        <div class="course-header">
          <div class="course-code">{{code}}</div>
          <div class="course-students">{{studentCount}} students</div>
        </div>
        <div class="course-content">
          <h3 class="course-title">{{title}}</h3>
          <p class="course-class">{{className}}</p>
          <p class="course-description">{{description}}</p>
        </div>
        <div class="course-actions">
          <button class="course-action-btn" data-action="upload-results" data-course-id="{{id}}">
            <span class="action-icon">📝</span>
            Upload Results
          </button>
          <button class="course-action-btn" data-action="view-students" data-course-id="{{id}}">
            <span class="action-icon">👥</span>
            View Students
          </button>
        </div>
      </div>
      {{/each}}
    `

    coursesGrid.innerHTML = utils.template(template, { courses: this.teacherCourses })

    // Add event listeners to course action buttons
    coursesGrid.querySelectorAll(".course-action-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation()
        const action = btn.dataset.action
        const courseId = btn.dataset.courseId
        this.handleCourseAction(action, courseId)
      })
    })

    // Add click handlers to course cards
    coursesGrid.querySelectorAll(".course-card").forEach((card) => {
      card.addEventListener("click", () => {
        const courseId = card.dataset.courseId
        this.showCourseDetails(courseId)
      })
    })
  }

  handleActionCard(action) {
    switch (action) {
      case "upload-results":
        window.location.href = "result_upload.html"
        break
      case "view-students":
        this.showAllStudents()
        break
      default:
        console.log(`Action not implemented: ${action}`)
    }
  }

  handleCourseAction(action, courseId) {
    const course = this.teacherCourses.find((c) => c.id.toString() === courseId)
    if (!course) return

    switch (action) {
      case "upload-results":
        // Navigate to result upload with course pre-selected
        sessionStorage.setItem("selectedCourseId", courseId)
        window.location.href = "result_upload.html"
        break
      case "view-students":
        this.showCourseStudents(course)
        break
      default:
        console.log(`Course action not implemented: ${action}`)
    }
  }

  showCourseDetails(courseId) {
    const course = this.teacherCourses.find((c) => c.id.toString() === courseId)
    if (!course) return

    // Show course details in a modal or navigate to detailed view
    utils.showNotification(`Course details for ${course.code} - ${course.title}`, "info")
  }

  showCourseStudents(course) {
    // This would show students in the course
    utils.showNotification(`Viewing students for ${course.code}`, "info")
  }

  showAllStudents() {
    // This would show all students across teacher's courses
    utils.showNotification("Viewing all students in your courses", "info")
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
  document.addEventListener("DOMContentLoaded", () => new TeacherDashboard())
} else {
  new TeacherDashboard()
}

export const teacherDashboard = new TeacherDashboard()
