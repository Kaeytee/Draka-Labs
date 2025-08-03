import { api } from "./api.js"
import { validation } from "./validation.js"
import { navigation } from "./navigation.js"

class Auth {
  constructor() {
    this.token = localStorage.getItem("siams_token")
    this.user = JSON.parse(localStorage.getItem("siams_user") || "null")
    this.init()
  }

  init() {
    const path = window.location.pathname
    const page = path.split("/").pop()

    if (page === "login.html") {
      this.initializeLoginPage()
    } else if (page === "register.html") {
      this.initializeRegisterPage()
    }
  }

  initializeLoginPage() {
    const loginForm = document.getElementById("loginForm")
    const roleSelect = document.getElementById("role")
    const emailInput = document.getElementById("email")
    const passwordInput = document.getElementById("password")
    const submitBtn = document.getElementById("loginSubmit")
    const roleIndicator = document.getElementById("selectedRole")

    // Pre-select role if coming from landing page
    const selectedRole = sessionStorage.getItem("selectedRole")
    if (selectedRole) {
      roleSelect.value = selectedRole
      roleIndicator.textContent = selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1)
    }

    // Role selection handler
    roleSelect.addEventListener("change", (e) => {
      const role = e.target.value
      roleIndicator.textContent = role ? role.charAt(0).toUpperCase() + role.slice(1) : "Select Role"
    })

    // Form validation
    emailInput.addEventListener("input", () => {
      validation.validateEmail(emailInput)
    })

    passwordInput.addEventListener("input", () => {
      validation.validatePassword(passwordInput)
    })

    // Form submission
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault()
      await this.handleLogin(loginForm)
    })

    // Initialize particles
    this.initializeAuthParticles()
  }

  initializeRegisterPage() {
    const registerForm = document.getElementById("registerForm")
    const fullNameInput = document.getElementById("fullName")
    const emailInput = document.getElementById("email")
    const passwordInput = document.getElementById("password")
    const confirmPasswordInput = document.getElementById("confirmPassword")

    // Form validation
    fullNameInput.addEventListener("input", () => {
      validation.validateRequired(fullNameInput, "Full name is required")
    })

    emailInput.addEventListener("input", () => {
      validation.validateEmail(emailInput)
    })

    passwordInput.addEventListener("input", () => {
      validation.validatePassword(passwordInput)
      this.updatePasswordStrength(passwordInput.value)
    })

    confirmPasswordInput.addEventListener("input", () => {
      validation.validatePasswordConfirmation(passwordInput, confirmPasswordInput)
    })

    // Form submission
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault()
      await this.handleRegistration(registerForm)
    })

    // Initialize particles
    this.initializeAuthParticles()
  }

  async handleLogin(form) {

    const formData = new FormData(form)
    const loginData = {
      email: formData.get("email"),
      password: formData.get("password"),
    }

    // Validate form
    if (!loginData.email || !loginData.password) {
      validation.validateEmail(form.querySelector('[name="email"]'))
      validation.validatePassword(form.querySelector('[name="password"]'))
      return
    }

    this.showLoading(true)

    try {
      console.log("Attempting login:", { email: loginData.email })

      const response = await api.post("/auth/login", loginData)

      if (response.success) {
        // Store authentication data
        this.token = response.data.token
        this.user = response.data.user

        localStorage.setItem("siams_token", this.token)
        localStorage.setItem("siams_user", JSON.stringify(this.user))

        console.log("Login successful:", this.user)

        // Clear selected role from session
        sessionStorage.removeItem("selectedRole")

        // Redirect to appropriate dashboard
        navigation.redirectToDashboard(this.user.role)
      } else {
        throw new Error(response.message || "Login failed")
      }
    } catch (err) {
      console.error("Login error:", err)
      this.showError(err.message || "Login failed. Please check your credentials.")
    } finally {
      this.showLoading(false)
    }
  }

  async handleRegistration(form) {
    const formData = new FormData(form)
    const registrationData = {
      fullName: formData.get("fullName"),
      email: formData.get("email"),
      password: formData.get("password"),
      confirmPassword: formData.get("confirmPassword"),
      role: "admin", // Admin registration only
    }

    // Validate form
    if (!this.validateRegistrationForm(registrationData)) {
      return
    }

    this.showLoading(true)

    try {
      console.log("Attempting registration:", {
        fullName: registrationData.fullName,
        email: registrationData.email,
      })

      const response = await api.post("/auth/register", {
        fullName: registrationData.fullName,
        email: registrationData.email,
        password: registrationData.password,
        role: registrationData.role,
      })

      if (response.success) {
        console.log("Registration successful")
        this.showSuccess("Registration successful! Redirecting to login...")

        // Redirect to login after delay
        setTimeout(() => {
          navigation.navigateToLogin()
        }, 2000)
      } else {
        throw new Error(response.message || "Registration failed")
      }
    } catch (err) {
      console.error("Registration error:", err)
      this.showError(err.message || "Registration failed. Please try again.")
    } finally {
      this.showLoading(false)
    }
  }

  validateLoginForm(data) {
    
    if (!validation.isValidEmail(data.email)) {
      this.showError("Please enter a valid email address")
      return false
    }

    if (!data.password || data.password.length < 6) {
      this.showError("Password must be at least 6 characters long")
      return false
    }

    return true
  }

  validateRegistrationForm(data) {
    if (!data.fullName || data.fullName.trim().length < 2) {
      this.showError("Full name must be at least 2 characters long")
      return false
    }

    if (!validation.isValidEmail(data.email)) {
      this.showError("Please enter a valid email address")
      return false
    }

    if (!validation.isStrongPassword(data.password)) {
      this.showError("Password must be at least 8 characters with uppercase, lowercase, number, and special character")
      return false
    }

    if (data.password !== data.confirmPassword) {
      this.showError("Passwords do not match")
      return false
    }

    return true
  }

  updatePasswordStrength(password) {
    const strengthIndicator = document.getElementById("passwordStrength")
    if (!strengthIndicator) return

    const strength = validation.getPasswordStrength(password)
    const strengthText = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
    const strengthColors = ["#ff4444", "#ff8800", "#ffaa00", "#88ff00", "#00ff88"]

    strengthIndicator.textContent = password ? `Strength: ${strengthText[strength]}` : ""
    strengthIndicator.style.color = strengthColors[strength]
  }

  showLoading(show) {
    const loadingOverlay = document.getElementById("loadingOverlay")
    if (loadingOverlay) {
      loadingOverlay.classList.toggle("active", show)
    }
  }

  showError(message) {
    const errorOverlay = document.getElementById("errorOverlay")
    const errorMessage = document.getElementById("errorMessage")
    const errorClose = document.getElementById("errorClose")

    if (errorOverlay && errorMessage) {
      errorMessage.textContent = message
      errorOverlay.classList.add("active")

      // Auto-hide after 5 seconds
      setTimeout(() => {
        errorOverlay.classList.remove("active")
      }, 5000)

      // Close button handler
      if (errorClose) {
        errorClose.onclick = () => {
          errorOverlay.classList.remove("active")
        }
      }
    }
  }

  showSuccess(message) {
    const successOverlay = document.getElementById("successOverlay")
    const successContent = successOverlay?.querySelector(".success-content p")

    if (successOverlay && successContent) {
      successContent.textContent = message
      successOverlay.classList.add("active")

      // Auto-hide after 3 seconds
      setTimeout(() => {
        successOverlay.classList.remove("active")
      }, 3000)
    }
  }

  initializeAuthParticles() {
    const particlesContainer = document.getElementById("particlesContainer")
    if (!particlesContainer) return

    // Create fewer particles for auth pages
    for (let i = 0; i < 10; i++) {
      setTimeout(() => {
        this.createAuthParticle(particlesContainer)
      }, i * 300)
    }

    setInterval(() => {
      if (document.querySelectorAll(".particle").length < 15) {
        this.createAuthParticle(particlesContainer)
      }
    }, 2000)
  }

  createAuthParticle(container) {
    const particle = document.createElement("div")
    particle.className = "particle"

    particle.style.left = Math.random() * 100 + "%"
    particle.style.top = Math.random() * 100 + "%"
    particle.style.background = "var(--primary-color)"
    particle.style.animationDelay = Math.random() * 6 + "s"

    container.appendChild(particle)

    setTimeout(() => {
      if (particle.parentNode) {
        particle.parentNode.removeChild(particle)
      }
    }, 6000)
  }

  // Authentication utility methods
  isAuthenticated() {
    return !!this.token && !!this.user
  }

  getToken() {
    return this.token
  }

  getUser() {
    return this.user
  }

  getUserRole() {
    return this.user?.role
  }

  logout() {
    this.token = null
    this.user = null
    localStorage.removeItem("siams_token")
    localStorage.removeItem("siams_user")
    sessionStorage.clear()

    console.log("User logged out")
    navigation.navigateToLogin()
  }

  // Check if token is expired (basic check)
  isTokenExpired() {
    if (!this.token) return true

    try {
      const payload = JSON.parse(atob(this.token.split(".")[1]))
      const currentTime = Date.now() / 1000
      return payload.exp < currentTime
    } catch (err) {
      console.error("Error checking token expiration:", err)
      return true
    }
  }
}

// Initialize and export
export const auth = new Auth()
