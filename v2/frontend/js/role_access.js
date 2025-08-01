import { auth } from "./auth.js"

class RoleAccess {
  constructor() {
    this.permissions = {
      admin: [
        "view_dashboard",
        "manage_schools",
        "manage_classes",
        "manage_courses",
        "manage_students",
        "import_students",
        "view_all_data",
        "manage_users",
        "system_settings",
      ],
      teacher: ["view_dashboard", "view_assigned_courses", "upload_results", "view_student_grades", "manage_profile"],
      student: ["view_dashboard", "view_grades", "manage_profile", "upload_profile_image"],
      public: ["view_landing", "login", "register_admin"],
    }
  }

  // Check if user has permission
  hasPermission(permission) {
    const user = auth.getUser()
    if (!user) {
      return this.permissions.public.includes(permission)
    }

    const userRole = user.role
    return this.permissions[userRole]?.includes(permission) || false
  }

  // Check if user has any of the permissions
  hasAnyPermission(permissions) {
    return permissions.some((permission) => this.hasPermission(permission))
  }

  // Check if user has all permissions
  hasAllPermissions(permissions) {
    return permissions.every((permission) => this.hasPermission(permission))
  }

  // Get user role
  getUserRole() {
    const user = auth.getUser()
    return user?.role || "public"
  }

  // Check if user is authenticated
  isAuthenticated() {
    return auth.isAuthenticated()
  }

  // Show/hide elements based on permissions
  applyRoleBasedVisibility() {
    const elements = document.querySelectorAll("[data-role], [data-permission]")

    elements.forEach((element) => {
      let shouldShow = true

      // Check role-based visibility
      const allowedRoles = element.dataset.role
      if (allowedRoles) {
        const roles = allowedRoles.split(",").map((r) => r.trim())
        const userRole = this.getUserRole()
        shouldShow = roles.includes(userRole)
      }

      // Check permission-based visibility
      const requiredPermissions = element.dataset.permission
      if (requiredPermissions && shouldShow) {
        const permissions = requiredPermissions.split(",").map((p) => p.trim())
        shouldShow = this.hasAnyPermission(permissions)
      }

      // Show/hide element
      if (shouldShow) {
        element.style.display = ""
        element.removeAttribute("aria-hidden")
      } else {
        element.style.display = "none"
        element.setAttribute("aria-hidden", "true")
      }
    })
  }

  // Filter navigation menu based on role
  filterNavigationMenu() {
    const navItems = document.querySelectorAll(".nav-menu .nav-link")

    navItems.forEach((item) => {
      const section = item.dataset.section
      if (!section) return

      let shouldShow = true

      switch (section) {
        case "dashboard":
          shouldShow = this.hasPermission("view_dashboard")
          break
        case "schools":
          shouldShow = this.hasPermission("manage_schools")
          break
        case "classes":
          shouldShow = this.hasPermission("manage_classes")
          break
        case "courses":
          shouldShow = this.hasPermission("manage_courses")
          break
        case "students":
          shouldShow = this.hasPermission("manage_students")
          break
        case "import":
          shouldShow = this.hasPermission("import_students")
          break
        case "results":
          shouldShow = this.hasPermission("upload_results")
          break
        case "grades":
          shouldShow = this.hasPermission("view_grades")
          break
        case "profile":
          shouldShow = this.hasPermission("manage_profile")
          break
        default:
          shouldShow = true
      }

      const listItem = item.closest("li")
      if (listItem) {
        if (shouldShow) {
          listItem.style.display = ""
        } else {
          listItem.style.display = "none"
        }
      }
    })
  }

  // Filter action cards based on permissions
  filterActionCards() {
    const actionCards = document.querySelectorAll(".action-card")

    actionCards.forEach((card) => {
      const action = card.dataset.action
      if (!action) return

      let shouldShow = true

      switch (action) {
        case "create-school":
          shouldShow = this.hasPermission("manage_schools")
          break
        case "import-students":
          shouldShow = this.hasPermission("import_students")
          break
        case "manage-users":
          shouldShow = this.hasPermission("manage_users")
          break
        case "upload-results":
          shouldShow = this.hasPermission("upload_results")
          break
        case "view-students":
          shouldShow = this.hasPermission("view_student_grades")
          break
        default:
          shouldShow = true
      }

      if (shouldShow) {
        card.style.display = ""
      } else {
        card.style.display = "none"
      }
    })
  }

  // Check page access
  checkPageAccess(page) {
    const pagePermissions = {
      "index.html": ["view_landing"],
      "login.html": ["login"],
      "register.html": ["register_admin"],
      "admin_dashboard.html": ["view_dashboard", "manage_schools"],
      "teacher_dashboard.html": ["view_dashboard", "view_assigned_courses"],
      "student_dashboard.html": ["view_dashboard", "view_grades"],
      "school_management.html": ["manage_schools"],
      "class_management.html": ["manage_classes"],
      "course_management.html": ["manage_courses"],
      "student_import.html": ["import_students"],
      "result_upload.html": ["upload_results"],
      "error.html": [], // Always accessible
    }

    const requiredPermissions = pagePermissions[page]
    if (!requiredPermissions) return true // Unknown pages are accessible

    if (requiredPermissions.length === 0) return true // No permissions required

    return this.hasAnyPermission(requiredPermissions)
  }

  // Redirect if access denied
  enforcePageAccess() {
    const currentPage = window.location.pathname.split("/").pop() || "index.html"

    if (!this.checkPageAccess(currentPage)) {
      console.warn(`Access denied to ${currentPage}`)

      // Redirect based on user role
      const userRole = this.getUserRole()
      if (userRole === "public") {
        window.location.href = "login.html"
      } else {
        // Redirect to appropriate dashboard
        const dashboards = {
          admin: "admin_dashboard.html",
          teacher: "teacher_dashboard.html",
          student: "student_dashboard.html",
        }
        window.location.href = dashboards[userRole] || "error.html?code=403"
      }
    }
  }

  // Initialize role-based access control
  init() {
    // Check page access
    this.enforcePageAccess()

    // Apply role-based visibility
    this.applyRoleBasedVisibility()

    // Filter navigation
    this.filterNavigationMenu()

    // Filter action cards
    this.filterActionCards()

    console.log(`Role access initialized for: ${this.getUserRole()}`)
  }

  // Update access control when user role changes
  updateAccessControl() {
    this.init()
  }

  // Get available actions for current user
  getAvailableActions() {
    const userRole = this.getUserRole()
    const permissions = this.permissions[userRole] || []

    const actions = {
      dashboard: permissions.includes("view_dashboard"),
      manageSchools: permissions.includes("manage_schools"),
      manageClasses: permissions.includes("manage_classes"),
      manageCourses: permissions.includes("manage_courses"),
      manageStudents: permissions.includes("manage_students"),
      importStudents: permissions.includes("import_students"),
      uploadResults: permissions.includes("upload_results"),
      viewGrades: permissions.includes("view_grades"),
      manageProfile: permissions.includes("manage_profile"),
      uploadProfileImage: permissions.includes("upload_profile_image"),
    }

    return actions
  }

  // Check if user can access specific data
  canAccessData(dataType, ownerId = null) {
    const userRole = this.getUserRole()
    const user = auth.getUser()

    switch (dataType) {
      case "all_schools":
        return this.hasPermission("view_all_data")
      case "all_students":
        return this.hasPermission("manage_students") || this.hasPermission("view_all_data")
      case "student_grades":
        return (
          this.hasPermission("view_student_grades") ||
          this.hasPermission("view_all_data") ||
          (user && user.id === ownerId)
        )
      case "course_results":
        return this.hasPermission("upload_results") || this.hasPermission("view_all_data")
      case "profile_data":
        return this.hasPermission("manage_profile") || (user && user.id === ownerId)
      default:
        return false
    }
  }
}

export const roleAccess = new RoleAccess()
