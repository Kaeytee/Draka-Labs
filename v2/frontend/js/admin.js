import { api } from "./api.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"
import { navigation } from "./navigation.js"
import { auth } from "./auth.js" // Declare the auth variable

class AdminDashboard {
  constructor() {
    this.dashboardStats = {}
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
    await this.loadDashboardData()

    console.log("Admin dashboard initialized")
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

    // Refresh dashboard
    const refreshBtn = document.querySelector(".refresh-btn")
    refreshBtn?.addEventListener("click", () => {
      this.loadDashboardData()
    })
  }

  async loadDashboardData() {
    this.showLoading(true)

    try {
      const response = await api.getDashboardStats()
      this.dashboardStats = response.data || {}
      this.updateDashboardStats()
      this.updateUserInfo()

      console.log("Dashboard data loaded:", this.dashboardStats)
    } catch (err) {
      console.error("Failed to load dashboard data:", err)
      error.handleApiError(err, "Loading dashboard")
    } finally {
      this.showLoading(false)
    }
  }

  updateDashboardStats() {
    // Update stat cards with animation
    const stats = [
      { id: "schoolCount", value: this.dashboardStats.schools || 0 },
      { id: "classCount", value: this.dashboardStats.classes || 0 },
      { id: "courseCount", value: this.dashboardStats.courses || 0 },
      { id: "studentCount", value: this.dashboardStats.students || 0 },
    ]

    stats.forEach((stat) => {
      const element = document.getElementById(stat.id)
      if (element) {
        this.animateCounter(element, stat.value)
      }
    })
  }

  animateCounter(element, targetValue) {
    const startValue = 0
    const duration = 1000
    const startTime = performance.now()

    const updateCounter = (currentTime) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)

      // Easing function
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOutQuart)

      element.textContent = currentValue.toLocaleString()

      if (progress < 1) {
        requestAnimationFrame(updateCounter)
      }
    }

    requestAnimationFrame(updateCounter)
  }

  updateUserInfo() {
    const user = auth.getUser()
    if (!user) return

    const userName = document.getElementById("userName")
    const avatarImg = document.getElementById("avatarImg")

    if (userName) {
      userName.textContent = user.fullName || user.name || "Administrator"
    }

    if (avatarImg && user.profileImage) {
      avatarImg.src = user.profileImage
    }
  }

  handleActionCard(action) {
    switch (action) {
      case "create-school":
        window.location.href = "school_management.html"
        break
      case "import-students":
        window.location.href = "student_import.html"
        break
      case "manage-users":
        this.showManageUsersModal()
        break
      default:
        console.log(`Action not implemented: ${action}`)
    }
  }

  showManageUsersModal() {
    // This would show a modal for user management
    // For now, just show a notification
    utils.showNotification("User management feature coming soon!", "info")
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
  document.addEventListener("DOMContentLoaded", () => new AdminDashboard())
} else {
  new AdminDashboard()
}

export const adminDashboard = new AdminDashboard()
