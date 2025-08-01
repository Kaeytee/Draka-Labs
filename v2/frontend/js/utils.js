class Utils {
  constructor() {
    this.templateCache = new Map()
  }

  // EJS-like templating system
  template(templateString, data = {}) {
    // Check cache first
    const cacheKey = this.hashString(templateString)
    if (this.templateCache.has(cacheKey)) {
      const compiledTemplate = this.templateCache.get(cacheKey)
      return compiledTemplate(data)
    }

    // Compile template
    const compiledTemplate = this.compileTemplate(templateString)
    this.templateCache.set(cacheKey, compiledTemplate)

    return compiledTemplate(data)
  }

  compileTemplate(templateString) {
    // Replace {{variable}} with data access
    let compiled = templateString.replace(/\{\{([^}]+)\}\}/g, (match, expression) => {
      // Handle simple variable access
      if (expression.includes(".")) {
        return `\${this.getNestedValue(data, '${expression.trim()}')}`
      }
      return `\${data.${expression.trim()} || ''}`
    })

    // Handle loops: {{#each items}}...{{/each}}
    compiled = compiled.replace(/\{\{#each\s+([^}]+)\}\}([\s\S]*?)\{\{\/each\}\}/g, (match, arrayName, content) => {
      return `\${this.renderLoop(data.${arrayName.trim()}, \`${content}\`, data)}`
    })

    // Handle conditionals: {{#if condition}}...{{/if}}
    compiled = compiled.replace(/\{\{#if\s+([^}]+)\}\}([\s\S]*?)\{\{\/if\}\}/g, (match, condition, content) => {
      return `\${this.getNestedValue(data, '${condition.trim()}') ? \`${content}\` : ''}`
    })

    // Handle conditionals with else: {{#if condition}}...{{else}}...{{/if}}
    compiled = compiled.replace(
      /\{\{#if\s+([^}]+)\}\}([\s\S]*?)\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g,
      (match, condition, ifContent, elseContent) => {
        return `\${this.getNestedValue(data, '${condition.trim()}') ? \`${ifContent}\` : \`${elseContent}\`}`
      },
    )

    // Return compiled function
    return new Function(
      "data",
      `
            return \`${compiled}\`;
        `,
    ).bind(this)
  }

  renderLoop(array, template, parentData) {
    if (!Array.isArray(array)) return ""

    return array
      .map((item, index) => {
        const itemData = { ...parentData, ...item, index, first: index === 0, last: index === array.length - 1 }
        return this.template(template, itemData)
      })
      .join("")
  }

  getNestedValue(obj, path) {
    return path.split(".").reduce((current, key) => {
      return current && current[key] !== undefined ? current[key] : ""
    }, obj)
  }

  hashString(str) {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = (hash << 5) - hash + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return hash.toString()
  }

  // DOM manipulation utilities
  createElement(tag, attributes = {}, children = []) {
    const element = document.createElement(tag)

    // Set attributes
    Object.entries(attributes).forEach(([key, value]) => {
      if (key === "className") {
        element.className = value
      } else if (key === "innerHTML") {
        element.innerHTML = value
      } else if (key === "textContent") {
        element.textContent = value
      } else if (key.startsWith("data-")) {
        element.setAttribute(key, value)
      } else {
        element[key] = value
      }
    })

    // Add children
    children.forEach((child) => {
      if (typeof child === "string") {
        element.appendChild(document.createTextNode(child))
      } else if (child instanceof Node) {
        element.appendChild(child)
      }
    })

    return element
  }

  updateElementContent(element, content) {
    if (!element) return

    // Use DocumentFragment for better performance
    const fragment = document.createDocumentFragment()

    if (typeof content === "string") {
      element.innerHTML = content
    } else if (content instanceof Node) {
      element.innerHTML = ""
      element.appendChild(content)
    } else if (Array.isArray(content)) {
      element.innerHTML = ""
      content.forEach((item) => {
        if (typeof item === "string") {
          fragment.appendChild(document.createTextNode(item))
        } else if (item instanceof Node) {
          fragment.appendChild(item)
        }
      })
      element.appendChild(fragment)
    }
  }

  // Form utilities
  getFormData(form) {
    const formData = new FormData(form)
    const data = {}

    for (const [key, value] of formData.entries()) {
      if (data[key]) {
        // Handle multiple values (checkboxes, etc.)
        if (Array.isArray(data[key])) {
          data[key].push(value)
        } else {
          data[key] = [data[key], value]
        }
      } else {
        data[key] = value
      }
    }

    return data
  }

  resetForm(form) {
    if (!form) return

    form.reset()

    // Clear custom validation states
    const inputs = form.querySelectorAll("input, select, textarea")
    inputs.forEach((input) => {
      input.classList.remove("valid", "invalid")
      const errorElement = input.parentNode.querySelector(".error-message")
      if (errorElement) {
        errorElement.remove()
      }
    })
  }

  // Data formatting utilities
  formatDate(date, format = "YYYY-MM-DD") {
    if (!date) return ""

    const d = new Date(date)
    if (isNaN(d.getTime())) return ""

    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, "0")
    const day = String(d.getDate()).padStart(2, "0")
    const hours = String(d.getHours()).padStart(2, "0")
    const minutes = String(d.getMinutes()).padStart(2, "0")

    switch (format) {
      case "YYYY-MM-DD":
        return `${year}-${month}-${day}`
      case "DD/MM/YYYY":
        return `${day}/${month}/${year}`
      case "MM/DD/YYYY":
        return `${month}/${day}/${year}`
      case "YYYY-MM-DD HH:mm":
        return `${year}-${month}-${day} ${hours}:${minutes}`
      default:
        return d.toLocaleDateString()
    }
  }

  formatNumber(number, decimals = 2) {
    if (typeof number !== "number") return ""
    return number.toFixed(decimals)
  }

  formatGrade(score, gradingSystem) {
    if (typeof score !== "number") return "N/A"

    if (!gradingSystem || !Array.isArray(gradingSystem)) {
      // Default letter grading
      if (score >= 90) return "A"
      if (score >= 80) return "B"
      if (score >= 70) return "C"
      if (score >= 60) return "D"
      return "F"
    }

    // Custom grading system
    for (const grade of gradingSystem) {
      if (score >= grade.min && score <= grade.max) {
        return grade.grade
      }
    }

    return "N/A"
  }

  // String utilities
  sanitizeHtml(str) {
    const div = document.createElement("div")
    div.textContent = str
    return div.innerHTML
  }

  truncateText(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text
    return text.substring(0, maxLength) + "..."
  }

  capitalizeFirst(str) {
    if (!str) return ""
    return str.charAt(0).toUpperCase() + str.slice(1)
  }

  // Storage utilities
  setLocalStorage(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (err) {
      console.error("Failed to save to localStorage:", err)
    }
  }

  getLocalStorage(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch (err) {
      console.error("Failed to read from localStorage:", err)
      return defaultValue
    }
  }

  removeLocalStorage(key) {
    try {
      localStorage.removeItem(key)
    } catch (err) {
      console.error("Failed to remove from localStorage:", err)
    }
  }

  // Notification utilities
  showNotification(message, type = "info", duration = 3000) {
    const notification = this.createElement("div", {
      className: `notification notification-${type}`,
      innerHTML: `
                <div class="notification-content">
                    <span class="notification-icon">${this.getNotificationIcon(type)}</span>
                    <span class="notification-message">${this.sanitizeHtml(message)}</span>
                    <button class="notification-close">×</button>
                </div>
            `,
    })

    // Add to page
    document.body.appendChild(notification)

    // Position notification
    const notifications = document.querySelectorAll(".notification")
    const offset = (notifications.length - 1) * 70
    notification.style.top = `${20 + offset}px`

    // Show notification
    setTimeout(() => notification.classList.add("show"), 100)

    // Auto-hide
    const hideTimeout = setTimeout(() => {
      this.hideNotification(notification)
    }, duration)

    // Close button handler
    const closeBtn = notification.querySelector(".notification-close")
    closeBtn.addEventListener("click", () => {
      clearTimeout(hideTimeout)
      this.hideNotification(notification)
    })
  }

  hideNotification(notification) {
    notification.classList.add("hide")
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification)
      }
    }, 300)
  }

  getNotificationIcon(type) {
    const icons = {
      success: "✅",
      error: "❌",
      warning: "⚠️",
      info: "ℹ️",
    }
    return icons[type] || icons.info
  }

  // Debounce utility
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

  // Throttle utility
  throttle(func, limit) {
    let inThrottle
    return function executedFunction(...args) {
      if (!inThrottle) {
        func.apply(this, args)
        inThrottle = true
        setTimeout(() => (inThrottle = false), limit)
      }
    }
  }

  // Generate unique ID
  generateId(prefix = "id") {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // Deep clone object
  deepClone(obj) {
    if (obj === null || typeof obj !== "object") return obj
    if (obj instanceof Date) return new Date(obj.getTime())
    if (obj instanceof Array) return obj.map((item) => this.deepClone(item))
    if (typeof obj === "object") {
      const cloned = {}
      Object.keys(obj).forEach((key) => {
        cloned[key] = this.deepClone(obj[key])
      })
      return cloned
    }
  }
}

export const utils = new Utils()
