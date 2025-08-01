import { auth } from "./auth.js"

class Navigation {
  constructor() {
    this.currentPage = null
    this.history = []
    this.init()
  }

  init() {
    // Handle browser navigation
    window.addEventListener("popstate", (e) => {
      this.handlePopState(e)
    })

    // Initialize current page
    this.currentPage = this.getCurrentPage()
    this.updateNavigationState()
  }

  getCurrentPage() {
    const path = window.location.pathname
    return path.split("/").pop() || "index.html"
  }

  navigateToLogin(selectedRole = null) {
    const url = selectedRole ? `login.html?role=${selectedRole}` : "login.html"
    this.navigateTo(url)
  }

  navigateToRegister() {
    this.navigateTo("register.html")
  }

  redirectToDashboard(role) {
    const dashboards = {
      admin: "admin_dashboard.html",
      teacher: "teacher_dashboard.html",
      student: "student_dashboard.html",
    }

    const dashboard = dashboards[role]
    if (dashboard) {
      console.log(`Redirecting to ${role} dashboard`)
      this.navigateTo(dashboard)
    } else {
      console.error("Unknown role:", role)
      this.navigateTo("error.html?code=403&message=Invalid role")
    }
  }

  navigateTo(url, pushState = true) {
    // Add to history
    if (pushState) {
      this.history.push(this.currentPage)
      history.pushState({ page: url }, "", url)
    }

    // Update current page
    this.currentPage = url.split("?")[0]

    // Navigate
    window.location.href = url

    console.log(`Navigated to: ${url}`)
  }

  goBack() {
    if (this.history.length > 0) {
      const previousPage = this.history.pop()
      this.navigateTo(previousPage, false)
    } else {
      history.back()
    }
  }

  handlePopState(e) {
    if (e.state && e.state.page) {
      this.currentPage = e.state.page
      this.updateNavigationState()
    }
  }

  updateNavigationState() {
    // Update active navigation links
    const navLinks = document.querySelectorAll(".nav-link")
    navLinks.forEach((link) => {
      const href = link.getAttribute("href")
      if (href && href.includes(this.currentPage)) {
        link.classList.add("active")
      } else {
        link.classList.remove("active")
      }
    })
  }

  // Dashboard navigation handlers
  setupDashboardNavigation() {
    const navLinks = document.querySelectorAll(".nav-link[data-section]")
    const contentSections = document.querySelectorAll(".content-section")
    const dashboardSection = document.getElementById("dashboardSection")
    const pageTitle = document.getElementById("pageTitle")

    navLinks.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault()
        const section = link.dataset.section

        // Update active link
        navLinks.forEach((l) => l.classList.remove("active"))
        link.classList.add("active")

        // Show/hide sections
        if (section === "dashboard") {
          dashboardSection.style.display = "block"
          contentSections.forEach((s) => s.classList.add("hidden"))
        } else {
          dashboardSection.style.display = "none"
          contentSections.forEach((s) => {
            if (s.id === `${section}Section`) {
              s.classList.remove("hidden")
            } else {
              s.classList.add("hidden")
            }
          })
        }

        // Update page title
        if (pageTitle) {
          pageTitle.textContent = this.getSectionTitle(section)
        }

        // Load section content
        this.loadSectionContent(section)

        console.log(`Dashboard section changed to: ${section}`)
      })
    })
  }

  getSectionTitle(section) {
    const titles = {
      dashboard: "Dashboard",
      schools: "School Management",
      classes: "Class Management",
      courses: "Course Management",
      students: "Student Management",
      import: "Import Students",
      results: "Upload Results",
      grades: "My Grades",
      profile: "Profile",
    }
    return titles[section] || "Dashboard"
  }

  async loadSectionContent(section) {
    const contentArea = document.querySelector(`#${section}Section`)
    if (!contentArea) return

    // Show loading
    this.showSectionLoading(contentArea)

    try {
      // Load section-specific content based on user role
      const userRole = auth.getUserRole()
      await this.loadRoleBasedContent(section, userRole, contentArea)
    } catch (err) {
      console.error(`Failed to load ${section} content:`, err)
      this.showSectionError(contentArea, err.message)
    }
  }

  async loadRoleBasedContent(section, role, container) {
    // This will be implemented by specific dashboard modules
    console.log(`Loading ${section} content for ${role}`)
  }

  showSectionLoading(container) {
    container.innerHTML = `
            <div class="section-loading">
                <div class="loading-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                </div>
                <p>Loading...</p>
            </div>
        `
  }

  showSectionError(container, message) {
    container.innerHTML = `
            <div class="section-error glass-panel">
                <div class="error-icon">⚠️</div>
                <h3>Failed to Load Content</h3>
                <p>${message}</p>
                <button class="retry-btn" onclick="location.reload()">
                    <span>Retry</span>
                    <div class="btn-glow"></div>
                </button>
            </div>
        `
  }

  // Mobile navigation
  setupMobileNavigation() {
    const sidebar = document.querySelector(".sidebar")
    const mobileToggle = document.createElement("button")

    mobileToggle.className = "mobile-nav-toggle"
    mobileToggle.innerHTML = `
            <span class="hamburger-line"></span>
            <span class="hamburger-line"></span>
            <span class="hamburger-line"></span>
        `
    mobileToggle.setAttribute("aria-label", "Toggle navigation menu")

    // Add to top bar
    const topBar = document.querySelector(".top-bar")
    if (topBar) {
      topBar.insertBefore(mobileToggle, topBar.firstChild)
    }

    // Toggle sidebar
    mobileToggle.addEventListener("click", () => {
      sidebar.classList.toggle("active")
      mobileToggle.classList.toggle("active")
      document.body.classList.toggle("nav-open")
    })

    // Close on outside click
    document.addEventListener("click", (e) => {
      if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target)) {
        sidebar.classList.remove("active")
        mobileToggle.classList.remove("active")
        document.body.classList.remove("nav-open")
      }
    })

    // Close on escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && sidebar.classList.contains("active")) {
        sidebar.classList.remove("active")
        mobileToggle.classList.remove("active")
        document.body.classList.remove("nav-open")
      }
    })
  }

  // Breadcrumb navigation
  updateBreadcrumb(items) {
    const breadcrumb = document.querySelector(".breadcrumb")
    if (!breadcrumb) return

    const breadcrumbHTML = items
      .map((item, index) => {
        if (index === items.length - 1) {
          return `<span class="breadcrumb-current">${item.title}</span>`
        } else {
          return `<a href="${item.url}" class="breadcrumb-link">${item.title}</a>`
        }
      })
      .join('<span class="breadcrumb-separator">›</span>')

    breadcrumb.innerHTML = breadcrumbHTML
  }

  // URL parameter helpers
  getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search)
    return urlParams.get(name)
  }

  setUrlParameter(name, value) {
    const url = new URL(window.location)
    url.searchParams.set(name, value)
    history.replaceState(null, "", url)
  }

  removeUrlParameter(name) {
    const url = new URL(window.location)
    url.searchParams.delete(name)
    history.replaceState(null, "", url)
  }
}

export const navigation = new Navigation()
