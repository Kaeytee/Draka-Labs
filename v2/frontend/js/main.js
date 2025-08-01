import { auth } from "./auth.js"
import { navigation } from "./navigation.js"
import { utils } from "./utils.js"
import { error } from "./error.js"

class Main {
  constructor() {
    this.init()
  }

  async init() {
    try {
      console.log("SIAMS Frontend initialized")

      // Check authentication status
      const token = auth.getToken()
      const currentPath = window.location.pathname

      // If user is logged in and on landing page, redirect to dashboard
      if (token && (currentPath === "/" || currentPath === "/index.html")) {
        const userRole = auth.getUserRole()
        navigation.redirectToDashboard(userRole)
        return
      }

      // Initialize page-specific functionality
      this.initializePage()

      // Set up global event listeners
      this.setupGlobalEventListeners()

      // Initialize particles effect
      this.initializeParticles()

      // Log page load
      this.logPageLoad()
    } catch (err) {
      console.error("Failed to initialize SIAMS:", err)
      error.show("Failed to initialize application", err.message)
    }
  }

  initializePage() {
    const path = window.location.pathname
    const page = path.split("/").pop() || "index.html"

    switch (page) {
      case "index.html":
      case "":
        this.initializeLandingPage()
        break
      case "login.html":
        // Login page initialization handled by auth.js
        break
      case "register.html":
        // Registration page initialization handled by auth.js
        break
      default:
        // Dashboard pages initialization handled by respective modules
        break
    }
  }

  initializeLandingPage() {
    // Set up role card interactions
    const roleCards = document.querySelectorAll(".role-card")
    const loginBtn = document.getElementById("loginBtn")
    this.selectedRole = null

    roleCards.forEach((card) => {
      card.addEventListener("click", () => this.selectRole(card, roleCards))
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          this.selectRole(card, roleCards)
        }
      })
    })

    loginBtn.addEventListener("click", () => {
      if (this.selectedRole) {
        navigation.navigateToLogin(this.selectedRole)
      } else {
        navigation.navigateToLogin()
      }
    })

    // Animate elements on load
    this.animatePageLoad()
  }

  selectRole(selectedCard, allCards) {
    allCards.forEach((card) => card.classList.remove("selected"))
    selectedCard.classList.add("selected")

    const role = selectedCard.dataset.role
    this.selectedRole = role
    sessionStorage.setItem("selectedRole", role)

    // Update login button text
    const loginBtn = document.getElementById("loginBtn")
    const btnText = loginBtn.querySelector("span")
    btnText.textContent = `Access ${role.charAt(0).toUpperCase() + role.slice(1)} Portal`

    console.log(`Role selected: ${role}`)
  }

  animatePageLoad() {
    // Animate title
    const title = document.querySelector(".main-title")
    if (title) {
      title.style.opacity = "0"
      title.style.transform = "translateY(30px)"

      setTimeout(() => {
        title.style.transition = "all 1s ease-out"
        title.style.opacity = "1"
        title.style.transform = "translateY(0)"
      }, 100)
    }

    // Animate role cards
    const roleCards = document.querySelectorAll(".role-card")
    roleCards.forEach((card, index) => {
      card.style.opacity = "0"
      card.style.transform = "translateY(50px)"

      setTimeout(
        () => {
          card.style.transition = "all 0.6s ease-out"
          card.style.opacity = "1"
          card.style.transform = "translateY(0)"
        },
        300 + index * 200,
      )
    })

    // Animate login button
    const loginBtn = document.getElementById("loginBtn")
    if (loginBtn) {
      loginBtn.style.opacity = "0"
      loginBtn.style.transform = "translateY(30px)"

      setTimeout(() => {
        loginBtn.style.transition = "all 0.8s ease-out"
        loginBtn.style.opacity = "1"
        loginBtn.style.transform = "translateY(0)"
      }, 1000)
    }
  }

  setupGlobalEventListeners() {
    // Handle browser back/forward navigation
    window.addEventListener("popstate", (e) => {
      console.log("Navigation state changed:", e.state)
      this.initializePage()
    })

    // Handle global keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      // Escape key to close modals
      if (e.key === "Escape") {
        const activeModal = document.querySelector(".modal-overlay.active")
        if (activeModal) {
          activeModal.classList.remove("active")
        }

        const activeError = document.querySelector(".error-overlay.active")
        if (activeError) {
          activeError.classList.remove("active")
        }
      }
    })

    // Handle online/offline status
    window.addEventListener("online", () => {
      console.log("Connection restored")
      utils.showNotification("Connection restored", "success")
    })

    window.addEventListener("offline", () => {
      console.log("Connection lost")
      utils.showNotification("Connection lost. Some features may not work.", "warning")
    })

    // Handle visibility change (tab switching)
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        console.log("Page hidden")
      } else {
        console.log("Page visible")
        // Refresh data if needed
        this.refreshPageData()
      }
    })
  }

  initializeParticles() {
    const particlesContainer = document.getElementById("particlesContainer")
    if (!particlesContainer) return

    // Create floating particles
    for (let i = 0; i < 20; i++) {
      setTimeout(() => {
        this.createParticle(particlesContainer)
      }, i * 200)
    }

    // Continue creating particles
    setInterval(() => {
      if (document.querySelectorAll(".particle").length < 30) {
        this.createParticle(particlesContainer)
      }
    }, 1000)
  }

  createParticle(container) {
    const particle = document.createElement("div")
    particle.className = "particle"

    // Random position
    particle.style.left = Math.random() * 100 + "%"
    particle.style.top = Math.random() * 100 + "%"

    // Random color
    const colors = ["var(--primary-color)", "var(--secondary-color)", "var(--accent-color)"]
    particle.style.background = colors[Math.floor(Math.random() * colors.length)]

    // Random animation delay
    particle.style.animationDelay = Math.random() * 6 + "s"

    container.appendChild(particle)

    // Remove particle after animation
    setTimeout(() => {
      if (particle.parentNode) {
        particle.parentNode.removeChild(particle)
      }
    }, 6000)
  }

  refreshPageData() {
    // Override in specific page implementations
    console.log("Refreshing page data...")
  }

  logPageLoad() {
    const logData = {
      timestamp: new Date().toISOString(),
      page: window.location.pathname,
      userAgent: navigator.userAgent,
      referrer: document.referrer,
      screenResolution: `${screen.width}x${screen.height}`,
      viewportSize: `${window.innerWidth}x${window.innerHeight}`,
      connectionType: navigator.connection?.effectiveType || "unknown",
    }

    console.log("Page load logged:", logData)

    // In production, send to analytics service
    // analytics.track('page_view', logData);
  }
}

// Initialize when DOM is loaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => new Main())
} else {
  new Main()
}

// Export for use in other modules
export const main = new Main()
