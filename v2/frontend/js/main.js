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
    const roleCards = document.querySelectorAll(".role-card")
    const loginBtn = document.getElementById("loginBtn")
    if (!roleCards.length || !loginBtn) {
      console.error("Required elements missing for landing page")
      error.show("Page Error", "Required elements not found")
      return
    }
    this.selectedRole = sessionStorage.getItem("selectedRole") || null


    // Clicking a role card immediately navigates to login for that role
    roleCards.forEach((card) => {
      card.addEventListener("click", () => {
        const role = card.dataset.role
        if (role) {
          sessionStorage.setItem("selectedRole", role)
          navigation.navigateToLogin(role)
        }
      })
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          const role = card.dataset.role
          if (role) {
            sessionStorage.setItem("selectedRole", role)
            navigation.navigateToLogin(role)
          }
        }
      })
    })

    // Access Portal button always goes to generic login page
    loginBtn.addEventListener("click", () => {
      navigation.navigateToLogin()
    })

    // Animate elements on load
    this.animatePageLoad()
  }

  selectRole(selectedCard, allCards) {
    allCards.forEach((card) => card.classList.remove("selected"))
    selectedCard.classList.add("selected")

    const role = selectedCard.dataset.role
    if (!role) {
      console.error("Role card missing data-role attribute")
      error.show("Selection Error", "Invalid role selected")
      return
    }
    this.selectedRole = role
    sessionStorage.setItem("selectedRole", role)

    // Update login button text
    const loginBtn = document.getElementById("loginBtn")
    const btnText = loginBtn.querySelector("span")
    if (btnText) {
      btnText.textContent = `Access ${role.charAt(0).toUpperCase() + role.slice(1)} Portal`
    }

    console.log(`Role selected: ${role}`)
  }

  animatePageLoad() {
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

    const roleCards = document.querySelectorAll(".role-card")
    roleCards.forEach((card, index) => {
      card.style.opacity = "0"
      card.style.transform = "translateY(50px)"
      setTimeout(() => {
        card.style.transition = "all 0.6s ease-out"
        card.style.opacity = "1"
        card.style.transform = "translateY(0)"
      }, 300 + index * 200)
    })

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
    window.addEventListener("popstate", (e) => {
      console.log("Navigation state changed:", e.state)
      this.initializePage()
    })

    document.addEventListener("keydown", (e) => {
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

    window.addEventListener("online", () => {
      console.log("Connection restored")
      utils.showNotification("Connection restored", "success")
    })

    window.addEventListener("offline", () => {
      console.log("Connection lost")
      utils.showNotification("Connection lost. Some features may not work.", "warning")
    })

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        console.log("Page hidden")
      } else {
        console.log("Page visible")
        this.refreshPageData()
      }
    })
  }

  initializeParticles() {
    const particlesContainer = document.getElementById("particlesContainer")
    if (!particlesContainer) return

    for (let i = 0; i < 20; i++) {
      setTimeout(() => {
        this.createParticle(particlesContainer)
      }, i * 200)
    }

    const intervalId = setInterval(() => {
      if (document.querySelectorAll(".particle").length < 30) {
        this.createParticle(particlesContainer)
      }
    }, 1000)

    window.addEventListener("unload", () => clearInterval(intervalId))
  }

  createParticle(container) {
    const particle = document.createElement("div")
    particle.className = "particle"
    particle.style.left = Math.random() * 100 + "%"
    particle.style.top = Math.random() * 100 + "%"
    const colors = ["var(--primary-color)", "var(--secondary-color)", "var(--accent-color)"]
    particle.style.background = colors[Math.floor(Math.random() * colors.length)]
    particle.style.animationDelay = Math.random() * 6 + "s"
    container.appendChild(particle)
    setTimeout(() => {
      if (particle.parentNode) {
        particle.parentNode.removeChild(particle)
      }
    }, 6000)
  }

  refreshPageData() {
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
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => new Main())
} else {
  new Main()
}

export const main = new Main()