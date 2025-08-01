class FileUpload {
  constructor() {
    this.maxFileSize = 10 * 1024 * 1024 // 10MB default
    this.allowedTypes = {
      image: ["image/jpeg", "image/png", "image/gif", "image/webp"],
      csv: ["text/csv", "application/vnd.ms-excel"],
      excel: ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"],
    }
  }

  // Parse CSV file
  async parseCSV(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()

      reader.onload = (e) => {
        try {
          const csv = e.target.result
          const data = this.csvToArray(csv)
          resolve(data)
        } catch (err) {
          reject(new Error("Failed to parse CSV file: " + err.message))
        }
      }

      reader.onerror = () => {
        reject(new Error("Failed to read file"))
      }

      reader.readAsText(file)
    })
  }

  // Convert CSV string to array of objects
  csvToArray(csv) {
    const lines = csv.split("\n").filter((line) => line.trim())
    if (lines.length < 2) {
      throw new Error("CSV must have at least a header row and one data row")
    }

    const headers = lines[0].split(",").map((header) => header.trim().replace(/"/g, ""))
    const data = []

    for (let i = 1; i < lines.length; i++) {
      const values = this.parseCSVLine(lines[i])
      if (values.length !== headers.length) {
        console.warn(`Row ${i + 1} has ${values.length} columns, expected ${headers.length}`)
        continue
      }

      const row = {}
      headers.forEach((header, index) => {
        row[header] = values[index]?.trim() || ""
      })
      data.push(row)
    }

    return data
  }

  // Parse a single CSV line handling quoted values
  parseCSVLine(line) {
    const values = []
    let current = ""
    let inQuotes = false

    for (let i = 0; i < line.length; i++) {
      const char = line[i]

      if (char === '"') {
        inQuotes = !inQuotes
      } else if (char === "," && !inQuotes) {
        values.push(current.replace(/"/g, ""))
        current = ""
      } else {
        current += char
      }
    }

    values.push(current.replace(/"/g, ""))
    return values
  }

  // Validate file
  validateFile(file, type = "any", maxSize = null) {
    const errors = []

    // Check if file exists
    if (!file) {
      errors.push("No file selected")
      return { isValid: false, errors }
    }

    // Check file size
    const sizeLimit = maxSize || this.maxFileSize
    if (file.size > sizeLimit) {
      errors.push(`File size (${this.formatFileSize(file.size)}) exceeds limit (${this.formatFileSize(sizeLimit)})`)
    }

    // Check file type
    if (type !== "any") {
      const allowedTypes = this.allowedTypes[type]
      if (allowedTypes && !allowedTypes.includes(file.type)) {
        const allowedExtensions = allowedTypes.map((t) => t.split("/")[1]).join(", ")
        errors.push(`Invalid file type. Allowed types: ${allowedExtensions}`)
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
    }
  }

  // Upload file with progress
  async uploadFile(file, endpoint, onProgress = null) {
    const formData = new FormData()
    formData.append("file", file)

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      // Progress handler
      if (onProgress) {
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100
            onProgress(percentComplete)
          }
        })
      }

      // Success handler
      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText)
            resolve(response)
          } catch (err) {
            resolve(xhr.responseText)
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`))
        }
      })

      // Error handler
      xhr.addEventListener("error", () => {
        reject(new Error("Upload failed: Network error"))
      })

      // Timeout handler
      xhr.addEventListener("timeout", () => {
        reject(new Error("Upload failed: Timeout"))
      })

      // Configure request
      xhr.open("POST", endpoint)
      xhr.timeout = 30000 // 30 seconds

      // Add authentication header if available
      const token = localStorage.getItem("siams_token")
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`)
      }

      // Send request
      xhr.send(formData)
    })
  }

  // Create file input with drag and drop
  createFileInput(options = {}) {
    const {
      accept = "*/*",
      multiple = false,
      dragDrop = true,
      preview = false,
      onFileSelect = null,
      onError = null,
    } = options

    const container = document.createElement("div")
    container.className = "file-input-container"

    const input = document.createElement("input")
    input.type = "file"
    input.accept = accept
    input.multiple = multiple
    input.className = "file-input-hidden"
    input.style.display = "none"

    const dropZone = document.createElement("div")
    dropZone.className = "file-drop-zone glass-panel"
    dropZone.innerHTML = `
            <div class="drop-zone-content">
                <div class="drop-zone-icon">📁</div>
                <p class="drop-zone-text">Click to select files or drag and drop</p>
                <p class="drop-zone-hint">Supported formats: ${accept}</p>
            </div>
        `

    const previewContainer = document.createElement("div")
    previewContainer.className = "file-preview-container"

    container.appendChild(input)
    container.appendChild(dropZone)
    if (preview) {
      container.appendChild(previewContainer)
    }

    // Click to select files
    dropZone.addEventListener("click", () => {
      input.click()
    })

    // File selection handler
    input.addEventListener("change", (e) => {
      const files = Array.from(e.target.files)
      this.handleFileSelection(files, onFileSelect, onError, preview ? previewContainer : null)
    })

    if (dragDrop) {
      // Drag and drop handlers
      dropZone.addEventListener("dragover", (e) => {
        e.preventDefault()
        dropZone.classList.add("drag-over")
      })

      dropZone.addEventListener("dragleave", (e) => {
        e.preventDefault()
        dropZone.classList.remove("drag-over")
      })

      dropZone.addEventListener("drop", (e) => {
        e.preventDefault()
        dropZone.classList.remove("drag-over")

        const files = Array.from(e.dataTransfer.files)
        this.handleFileSelection(files, onFileSelect, onError, preview ? previewContainer : null)
      })
    }

    return container
  }

  // Handle file selection
  handleFileSelection(files, onFileSelect, onError, previewContainer) {
    if (files.length === 0) return

    // Validate files
    const validFiles = []
    const errors = []

    files.forEach((file) => {
      const validation = this.validateFile(file)
      if (validation.isValid) {
        validFiles.push(file)
      } else {
        errors.push(`${file.name}: ${validation.errors.join(", ")}`)
      }
    })

    // Show errors
    if (errors.length > 0 && onError) {
      onError(errors)
    }

    // Process valid files
    if (validFiles.length > 0) {
      if (previewContainer) {
        this.showFilePreview(validFiles, previewContainer)
      }

      if (onFileSelect) {
        onFileSelect(validFiles)
      }
    }
  }

  // Show file preview
  showFilePreview(files, container) {
    container.innerHTML = ""

    files.forEach((file) => {
      const preview = document.createElement("div")
      preview.className = "file-preview-item glass-panel"

      if (file.type.startsWith("image/")) {
        // Image preview
        const img = document.createElement("img")
        img.className = "file-preview-image"
        img.alt = file.name

        const reader = new FileReader()
        reader.onload = (e) => {
          img.src = e.target.result
        }
        reader.readAsDataURL(file)

        preview.appendChild(img)
      } else {
        // File icon
        const icon = document.createElement("div")
        icon.className = "file-preview-icon"
        icon.textContent = this.getFileIcon(file.type)
        preview.appendChild(icon)
      }

      const info = document.createElement("div")
      info.className = "file-preview-info"
      info.innerHTML = `
                <div class="file-name">${file.name}</div>
                <div class="file-size">${this.formatFileSize(file.size)}</div>
            `

      const removeBtn = document.createElement("button")
      removeBtn.className = "file-remove-btn"
      removeBtn.innerHTML = "×"
      removeBtn.setAttribute("aria-label", `Remove ${file.name}`)
      removeBtn.addEventListener("click", () => {
        preview.remove()
      })

      preview.appendChild(info)
      preview.appendChild(removeBtn)
      container.appendChild(preview)
    })
  }

  // Get file icon based on type
  getFileIcon(type) {
    if (type.startsWith("image/")) return "🖼️"
    if (type.includes("csv")) return "📊"
    if (type.includes("excel") || type.includes("spreadsheet")) return "📈"
    if (type.includes("pdf")) return "📄"
    if (type.includes("word")) return "📝"
    return "📁"
  }

  // Format file size
  formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  // Create progress bar
  createProgressBar() {
    const container = document.createElement("div")
    container.className = "upload-progress-container"

    const progressBar = document.createElement("div")
    progressBar.className = "upload-progress-bar"

    const progressFill = document.createElement("div")
    progressFill.className = "upload-progress-fill"

    const progressText = document.createElement("div")
    progressText.className = "upload-progress-text"
    progressText.textContent = "0%"

    progressBar.appendChild(progressFill)
    container.appendChild(progressBar)
    container.appendChild(progressText)

    return {
      container,
      update: (percent) => {
        progressFill.style.width = `${percent}%`
        progressText.textContent = `${Math.round(percent)}%`
      },
    }
  }

  // Compress image before upload
  async compressImage(file, maxWidth = 800, maxHeight = 600, quality = 0.8) {
    return new Promise((resolve) => {
      const canvas = document.createElement("canvas")
      const ctx = canvas.getContext("2d")
      const img = new Image()

      img.onload = () => {
        // Calculate new dimensions
        let { width, height } = img
        if (width > height) {
          if (width > maxWidth) {
            height = (height * maxWidth) / width
            width = maxWidth
          }
        } else {
          if (height > maxHeight) {
            width = (width * maxHeight) / height
            height = maxHeight
          }
        }

        // Set canvas size
        canvas.width = width
        canvas.height = height

        // Draw and compress
        ctx.drawImage(img, 0, 0, width, height)
        canvas.toBlob(resolve, "image/jpeg", quality)
      }

      img.src = URL.createObjectURL(file)
    })
  }
}

export const fileUpload = new FileUpload()
