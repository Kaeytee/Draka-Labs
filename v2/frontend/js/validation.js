class Validation {
  constructor() {
    this.rules = {}
    this.messages = {
      required: "This field is required",
      email: "Please enter a valid email address",
      minLength: "Must be at least {min} characters long",
      maxLength: "Must be no more than {max} characters long",
      pattern: "Please enter a valid format",
      number: "Please enter a valid number",
      min: "Value must be at least {min}",
      max: "Value must be no more than {max}",
      match: "Fields do not match",
      unique: "This value already exists",
    }
  }

  // Email validation
  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  validateEmail(input) {
    const email = input.value.trim()
    const isValid = this.isValidEmail(email)

    this.updateFieldValidation(input, isValid, isValid ? "" : this.messages.email)
    return isValid
  }

  // Password validation
  isStrongPassword(password) {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number, 1 special character
    const strongRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/
    return strongRegex.test(password)
  }

  getPasswordStrength(password) {
    if (!password) return 0

    let strength = 0
    const checks = [
      password.length >= 8, // Length
      /[a-z]/.test(password), // Lowercase
      /[A-Z]/.test(password), // Uppercase
      /\d/.test(password), // Number
      /[@$!%*?&]/.test(password), // Special character
    ]

    strength = checks.filter(Boolean).length
    return Math.min(strength, 4) // Max strength of 4
  }

  validatePassword(input, minLength = 6) {
    const password = input.value
    const isValid = password.length >= minLength

    let message = ""
    if (!isValid) {
      message = this.messages.minLength.replace("{min}", minLength)
    }

    this.updateFieldValidation(input, isValid, message)
    return isValid
  }

  validatePasswordConfirmation(passwordInput, confirmInput) {
    const password = passwordInput.value
    const confirm = confirmInput.value
    const isValid = password === confirm && password.length > 0

    this.updateFieldValidation(confirmInput, isValid, isValid ? "" : this.messages.match)
    return isValid
  }

  // Required field validation
  validateRequired(input, customMessage = null) {
    const value = input.value.trim()
    const isValid = value.length > 0

    const message = isValid ? "" : customMessage || this.messages.required
    this.updateFieldValidation(input, isValid, message)
    return isValid
  }

  // Number validation
  validateNumber(input, min = null, max = null) {
    const value = Number.parseFloat(input.value)
    let isValid = !isNaN(value)
    let message = ""

    if (!isValid) {
      message = this.messages.number
    } else {
      if (min !== null && value < min) {
        isValid = false
        message = this.messages.min.replace("{min}", min)
      } else if (max !== null && value > max) {
        isValid = false
        message = this.messages.max.replace("{max}", max)
      }
    }

    this.updateFieldValidation(input, isValid, message)
    return isValid
  }

  // Date validation
  validateDate(input, minDate = null, maxDate = null) {
    const value = input.value
    if (!value) {
      this.updateFieldValidation(input, false, this.messages.required)
      return false
    }

    const date = new Date(value)
    let isValid = !isNaN(date.getTime())
    let message = ""

    if (!isValid) {
      message = "Please enter a valid date"
    } else {
      if (minDate && date < new Date(minDate)) {
        isValid = false
        message = `Date must be after ${minDate}`
      } else if (maxDate && date > new Date(maxDate)) {
        isValid = false
        message = `Date must be before ${maxDate}`
      }
    }

    this.updateFieldValidation(input, isValid, message)
    return isValid
  }

  // File validation
  validateFile(input, allowedTypes = [], maxSize = null) {
    const file = input.files[0]
    if (!file) {
      this.updateFieldValidation(input, false, "Please select a file")
      return false
    }

    let isValid = true
    let message = ""

    // Check file type
    if (allowedTypes.length > 0) {
      const fileType = file.type
      const fileName = file.name.toLowerCase()
      const isTypeAllowed = allowedTypes.some((type) => {
        return fileType.includes(type) || fileName.endsWith(`.${type}`)
      })

      if (!isTypeAllowed) {
        isValid = false
        message = `Allowed file types: ${allowedTypes.join(", ")}`
      }
    }

    // Check file size
    if (maxSize && file.size > maxSize) {
      isValid = false
      message = `File size must be less than ${this.formatFileSize(maxSize)}`
    }

    this.updateFieldValidation(input, isValid, message)
    return isValid
  }

  // CSV validation
  validateCSVStructure(data, requiredColumns) {
    if (!Array.isArray(data) || data.length === 0) {
      return { isValid: false, message: "CSV file is empty or invalid" }
    }

    const headers = Object.keys(data[0])
    const missingColumns = requiredColumns.filter((col) => !headers.includes(col))

    if (missingColumns.length > 0) {
      return {
        isValid: false,
        message: `Missing required columns: ${missingColumns.join(", ")}`,
      }
    }

    // Validate data rows
    for (let i = 0; i < data.length; i++) {
      const row = data[i]
      for (const col of requiredColumns) {
        if (!row[col] || row[col].toString().trim() === "") {
          return {
            isValid: false,
            message: `Row ${i + 1}: Missing value for ${col}`,
          }
        }
      }
    }

    return { isValid: true, message: "" }
  }

  // Grading system validation
  validateGradingSystem(gradingSystem) {
    if (!Array.isArray(gradingSystem) || gradingSystem.length === 0) {
      return { isValid: false, message: "Grading system must have at least one grade" }
    }

    // Check for required fields
    for (let i = 0; i < gradingSystem.length; i++) {
      const grade = gradingSystem[i]
      if (!grade.grade || typeof grade.min !== "number" || typeof grade.max !== "number") {
        return {
          isValid: false,
          message: `Grade ${i + 1}: Missing grade, min, or max value`,
        }
      }

      if (grade.min >= grade.max) {
        return {
          isValid: false,
          message: `Grade ${i + 1}: Min value must be less than max value`,
        }
      }
    }

    // Check for overlapping ranges
    for (let i = 0; i < gradingSystem.length; i++) {
      for (let j = i + 1; j < gradingSystem.length; j++) {
        const grade1 = gradingSystem[i]
        const grade2 = gradingSystem[j]

        if (
          (grade1.min <= grade2.max && grade1.max >= grade2.min) ||
          (grade2.min <= grade1.max && grade2.max >= grade1.min)
        ) {
          return {
            isValid: false,
            message: `Overlapping grade ranges: ${grade1.grade} and ${grade2.grade}`,
          }
        }
      }
    }

    return { isValid: true, message: "" }
  }

  // Form validation
  validateForm(form) {
    const inputs = form.querySelectorAll("input, select, textarea")
    let isValid = true
    const errors = []

    inputs.forEach((input) => {
      const fieldValid = this.validateField(input)
      if (!fieldValid) {
        isValid = false
        errors.push({
          field: input.name || input.id,
          message: this.getFieldError(input),
        })
      }
    })

    return { isValid, errors }
  }

  validateField(input) {
    const type = input.type
    const value = input.value.trim()

    // Skip validation for disabled or hidden fields
    if (input.disabled || input.type === "hidden") {
      return true
    }

    // Required validation
    if (input.required && !value) {
      this.updateFieldValidation(input, false, this.messages.required)
      return false
    }

    // Skip other validations if field is empty and not required
    if (!value && !input.required) {
      this.updateFieldValidation(input, true, "")
      return true
    }

    // Type-specific validation
    switch (type) {
      case "email":
        return this.validateEmail(input)
      case "password":
        return this.validatePassword(input)
      case "number":
        const min = input.min ? Number.parseFloat(input.min) : null
        const max = input.max ? Number.parseFloat(input.max) : null
        return this.validateNumber(input, min, max)
      case "date":
        return this.validateDate(input, input.min, input.max)
      case "file":
        const accept = input.accept ? input.accept.split(",").map((t) => t.trim()) : []
        return this.validateFile(input, accept)
      default:
        // Pattern validation
        if (input.pattern) {
          const regex = new RegExp(input.pattern)
          const isValid = regex.test(value)
          this.updateFieldValidation(input, isValid, isValid ? "" : this.messages.pattern)
          return isValid
        }

        // Length validation
        const minLength = input.minLength || 0
        const maxLength = input.maxLength || Number.POSITIVE_INFINITY

        if (value.length < minLength) {
          this.updateFieldValidation(input, false, this.messages.minLength.replace("{min}", minLength))
          return false
        }

        if (value.length > maxLength) {
          this.updateFieldValidation(input, false, this.messages.maxLength.replace("{max}", maxLength))
          return false
        }

        this.updateFieldValidation(input, true, "")
        return true
    }
  }

  updateFieldValidation(input, isValid, message) {
    // Remove existing error message
    const existingError = input.parentNode.querySelector(".error-message")
    if (existingError) {
      existingError.remove()
    }

    // Update field classes
    input.classList.remove("valid", "invalid")
    input.classList.add(isValid ? "valid" : "invalid")

    // Add error message if invalid
    if (!isValid && message) {
      const errorElement = document.createElement("div")
      errorElement.className = "error-message"
      errorElement.textContent = message
      errorElement.setAttribute("role", "alert")
      input.parentNode.appendChild(errorElement)
    }

    // Update ARIA attributes
    input.setAttribute("aria-invalid", !isValid)
    if (!isValid && message) {
      input.setAttribute("aria-describedby", `${input.id || input.name}-error`)
    } else {
      input.removeAttribute("aria-describedby")
    }
  }

  getFieldError(input) {
    const errorElement = input.parentNode.querySelector(".error-message")
    return errorElement ? errorElement.textContent : ""
  }

  // Utility methods
  formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  // Real-time validation setup
  setupRealTimeValidation(form) {
    const inputs = form.querySelectorAll("input, select, textarea")

    inputs.forEach((input) => {
      // Validate on blur
      input.addEventListener("blur", () => {
        this.validateField(input)
      })

      // Validate on input for certain types
      if (["email", "password", "text", "number"].includes(input.type)) {
        input.addEventListener(
          "input",
          this.debounce(() => {
            this.validateField(input)
          }, 300),
        )
      }
    })
  }

  debounce(func, wait) {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  }
}

export const validation = new Validation()
