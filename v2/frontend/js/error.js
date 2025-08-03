import { utils } from "./utils.js"

class ErrorHandler {
  constructor() {
    this.errorLog = []
    this.maxLogSize = 100
    this.init()
  }

  init() {
    // Global error handler
    window.addEventListener("error", (e) => {
      this.logError({
        type: "javascript",
        message: e.message,
        filename: e.filename,
        lineno: e.lineno,
        colno: e.colno,
        stack: e.error?.stack,
        timestamp: new Date().toISOString(),
      })
    })

    // Unhandled promise rejection handler
    window.addEventListener("unhandledrejection", (e) => {
      this.logError({
        type: "promise",
        message: e.reason?.message || "Unhandled promise rejection",
        stack: e.reason?.stack,
        timestamp: new Date().toISOString(),
      })
    })

    // Initialize error page if we're on it
    if (window.location.pathname.includes("error.html")) {
      this.initializeErrorPage()
    }
  }

  // Log error
  logError(error) {
    // Add to error log
    this.errorLog.unshift(error)

    // Limit log size
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize)
    }

    // Console log
    console.error("Error logged:", error)

    // In production, send to error reporting service
    // Note: In browser environment, we can't access process.env directly
    // You could set a global variable or check window.location.hostname
    const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
    if (isProduction) {
      this.reportError(error)
    }
  }

  // Show error message
  show(title, message, type = "error", duration = 5000) {
    const errorContainer = this.createErrorContainer(title, message, type)
    document.body.appendChild(errorContainer)

    // Show with animation
    setTimeout(() => {
      errorContainer.classList.add("show")
    }, 100)

    // Auto-hide
    if (duration > 0) {
      setTimeout(() => {
        this.hide(errorContainer)
      }, duration)
    }

    return errorContainer
  }

  // Hide error message
  hide(errorContainer) {
    errorContainer.classList.add("hide")
    setTimeout(() => {
      if (errorContainer.parentNode) {
        errorContainer.parentNode.removeChild(errorContainer)
      }
    }, 300)
  }

  // Create error container
  createErrorContainer(title, message, type) {
    const container = document.createElement("div")
    container.className = `error-notification error-${type}`

    const icon = this.getErrorIcon(type)
    const sanitizedTitle = utils.sanitizeHtml(title)
    const sanitizedMessage = utils.sanitizeHtml(message)

    container.innerHTML = `
            <div class="error-notification-content glass-panel">
                <div class="error-notification-icon">${icon}</div>
                <div class="error-notification-text">
                    <div class="error-notification-title">${sanitizedTitle}</div>
                    <div class="error-notification-message">${sanitizedMessage}</div>
                </div>
                <button class="error-notification-close" aria-label="Close error message">×</button>
            </div>
        `

    // Close button handler
    const closeBtn = container.querySelector(".error-notification-close")
    closeBtn.addEventListener("click", () => {
      this.hide(container)
    })

    return container
  }

  // Get error icon
  getErrorIcon(type) {
    const icons = {
      error: "❌",
      warning: "⚠️",
      info: "ℹ️",
      success: "✅",
    }
    return icons[type] || icons.error
  }

  // Show inline error
  showInline(element, message) {
    // Remove existing error
    this.clearInline(element)

    // Create error element
    const errorElement = document.createElement("div")
    errorElement.className = "inline-error"
    errorElement.textContent = message
    errorElement.setAttribute("role", "alert")

    // Insert after element
    element.parentNode.insertBefore(errorElement, element.nextSibling)

    // Update element styling
    element.classList.add("error")
    element.setAttribute("aria-invalid", "true")
    element.setAttribute("aria-describedby", errorElement.id || "inline-error")

    return errorElement
  }

  // Clear inline error
  clearInline(element) {
    const existingError = element.parentNode.querySelector(".inline-error")
    if (existingError) {
      existingError.remove()
    }

    element.classList.remove("error")
    element.removeAttribute("aria-invalid")
    element.removeAttribute("aria-describedby")
  }

  // Handle API errors
  handleApiError(error, context = "") {
    let title = "Request Failed"
    let message = "An unexpected error occurred"
    let type = "error"

    if (error.response) {
      // HTTP error response
      const status = error.response.status
      title = `HTTP ${status} Error`

      switch (status) {
        case 400:
          message = "Bad request. Please check your input."
          break
        case 401:
          message = "Authentication required. Please log in."
          type = "warning"
          // Redirect to login after delay
          setTimeout(() => {
            window.location.href = "login.html"
          }, 2000)
          break
        case 403:
          message = "Access denied. You don't have permission for this action."
          break
        case 404:
          message = "The requested resource was not found."
          break
        case 429:
          message = "Too many requests. Please try again later."
          type = "warning"
          break
        case 500:
          message = "Server error. Please try again later."
          break
        default:
          message = error.response.data?.message || `Server returned ${status} error`
      }
    } else if (error.request) {
      // Network error
      title = "Network Error"
      message = "Unable to connect to server. Please check your internet connection."
    } else {
      // Other error
      message = error.message || "An unexpected error occurred"
    }

    // Add context if provided
    if (context) {
      message = `${context}: ${message}`
    }

    // Log error
    this.logError({
      type: "api",
      title,
      message,
      context,
      error: error.toString(),
      timestamp: new Date().toISOString(),
    })

    // Show error
    this.show(title, message, type)

    return { title, message, type }
  }

  // Handle form errors
  handleFormErrors(errors, form) {
    // Clear existing errors
    const existingErrors = form.querySelectorAll(".inline-error")
    existingErrors.forEach((error) => error.remove())

    const inputs = form.querySelectorAll("input, select, textarea")
    inputs.forEach((input) => {
      input.classList.remove("error")
      input.removeAttribute("aria-invalid")
    })

    // Show new errors
    if (Array.isArray(errors)) {
      errors.forEach((error) => {
        const field = form.querySelector(`[name="${error.field}"], #${error.field}`)
        if (field) {
          this.showInline(field, error.message)
        }
      })
    } else if (typeof errors === "object") {
      Object.entries(errors).forEach(([field, message]) => {
        const fieldElement = form.querySelector(`[name="${field}"], #${field}`)
        if (fieldElement) {
          this.showInline(fieldElement, message)
        }
      })
    }
  }

  // Initialize error page
  initializeErrorPage() {
    const urlParams = new URLSearchParams(window.location.search)
    const errorCode = urlParams.get("code") || "500"
    const errorMessage = urlParams.get("message") || "An unexpected error occurred"

    // Update error display
    const errorCodeElement = document.getElementById("errorCode")
    const errorDescriptionElement = document.getElementById("errorDescription")

    if (errorCodeElement) {
      errorCodeElement.textContent = errorCode
    }

    if (errorDescriptionElement) {
      errorDescriptionElement.textContent = this.getErrorDescription(errorCode, errorMessage)
    }

    // Update error details
    this.updateErrorDetails()

    // Set up retry button
    const retryBtn = document.getElementById("retryBtn")
    if (retryBtn) {
      retryBtn.addEventListener("click", () => {
        window.location.reload()
      })
    }

    // Set up back button
    const backBtn = document.getElementById("backBtn")
    if (backBtn) {
      backBtn.addEventListener("click", () => {
        if (window.history.length > 1) {
          window.history.back()
        } else {
          window.location.href = "index.html"
        }
      })
    }

    // Initialize particles
    this.initializeErrorParticles()
  }

  // Get error description
  getErrorDescription(code, message) {
    const descriptions = {
      400: "The request was invalid or cannot be served.",
      401: "Authentication is required to access this resource.",
      403: "You don't have permission to access this resource.",
      404: "The requested page or resource could not be found.",
      429: "Too many requests have been made. Please try again later.",
      500: "An internal server error occurred. Please try again later.",
      503: "The service is temporarily unavailable. Please try again later.",
    }

    return descriptions[code] || message || "An unexpected error occurred."
  }

  // Update error details
  updateErrorDetails() {
    const timestampElement = document.getElementById("errorTimestamp")
    const userAgentElement = document.getElementById("userAgent")
    const urlElement = document.getElementById("errorUrl")

    if (timestampElement) {
      timestampElement.textContent = new Date().toLocaleString()
    }

    if (userAgentElement) {
      userAgentElement.textContent = navigator.userAgent
    }

    if (urlElement) {
      urlElement.textContent = window.location.href
    }
  }

  // Initialize error page particles
  initializeErrorParticles() {
    const particlesContainer = document.getElementById("particlesContainer")
    if (!particlesContainer) return

    // Create error-themed particles
    for (let i = 0; i < 15; i++) {
      setTimeout(() => {
        this.createErrorParticle(particlesContainer)
      }, i * 200)
    }

    setInterval(() => {
      if (document.querySelectorAll(".error-particle").length < 20) {
        this.createErrorParticle(particlesContainer)
      }
    }, 1500)
  }

  createErrorParticle(container) {
    const particle = document.createElement("div")
    particle.className = "error-particle"

    particle.style.left = Math.random() * 100 + "%"
    particle.style.top = Math.random() * 100 + "%"
    particle.style.background = "var(--error-color)"
    particle.style.animationDelay = Math.random() * 4 + "s"

    container.appendChild(particle)

    setTimeout(() => {
      if (particle.parentNode) {
        particle.parentNode.removeChild(particle)
      }
    }, 4000)
  }

  // Report error to external service
  reportError(error) {
    // In production, send to error reporting service like Sentry
    console.log("Reporting error to external service:", error)

    // Example implementation:
    // fetch('/api/errors', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify(error)
    // }).catch(err => console.error('Failed to report error:', err));
  }

  // Get error log
  getErrorLog() {
    return [...this.errorLog]
  }

  // Clear error log
  clearErrorLog() {
    this.errorLog = []
  }

  // Export error log
  exportErrorLog() {
    const logData = {
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      errors: this.errorLog,
    }

    const blob = new Blob([JSON.stringify(logData, null, 2)], {
      type: "application/json",
    })

    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `siams-error-log-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
}

export const error = new ErrorHandler()
