import { auth } from "./auth.js"

class API {
  constructor() {
    this.baseURL = process.env.NODE_ENV === "production" ? "https://api.siams.edu" : "http://localhost:3001"
    this.timeout = 10000 // 10 seconds
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const config = {
      timeout: this.timeout,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    }

    // Add authentication header if token exists
    const token = auth.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add CSRF token if available
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content")
    if (csrfToken) {
      config.headers["X-CSRF-Token"] = csrfToken
    }

    try {
      console.log(`API Request: ${options.method || "GET"} ${url}`)

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), config.timeout)

      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      // Handle different response types
      let data
      const contentType = response.headers.get("content-type")

      if (contentType && contentType.includes("application/json")) {
        data = await response.json()
      } else {
        data = await response.text()
      }

      if (!response.ok) {
        // Handle specific HTTP errors
        switch (response.status) {
          case 401:
            console.warn("Unauthorized access - redirecting to login")
            auth.logout()
            throw new Error("Session expired. Please login again.")
          case 403:
            throw new Error("Access denied. Insufficient permissions.")
          case 404:
            throw new Error("Resource not found.")
          case 429:
            throw new Error("Too many requests. Please try again later.")
          case 500:
            throw new Error("Server error. Please try again later.")
          default:
            throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`)
        }
      }

      console.log(`API Response: ${response.status}`, data)
      return data
    } catch (err) {
      if (err.name === "AbortError") {
        console.error("API request timeout:", url)
        throw new Error("Request timeout. Please check your connection.")
      }

      console.error("API request failed:", err)
      throw err
    }
  }

  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString()
    const url = queryString ? `${endpoint}?${queryString}` : endpoint

    return this.request(url, {
      method: "GET",
    })
  }

  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async patch(endpoint, data = {}) {
    return this.request(endpoint, {
      method: "PATCH",
      body: JSON.stringify(data),
    })
  }

  async delete(endpoint) {
    return this.request(endpoint, {
      method: "DELETE",
    })
  }

  async upload(endpoint, formData) {
    const token = auth.getToken()
    const headers = {}

    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    // Add CSRF token if available
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content")
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken
    }

    try {
      console.log(`API Upload: POST ${this.baseURL}${endpoint}`)

      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: "POST",
        headers,
        body: formData,
      })

      let data
      const contentType = response.headers.get("content-type")

      if (contentType && contentType.includes("application/json")) {
        data = await response.json()
      } else {
        data = await response.text()
      }

      if (!response.ok) {
        throw new Error(data.message || `Upload failed: ${response.statusText}`)
      }

      console.log("Upload successful:", data)
      return data
    } catch (err) {
      console.error("Upload failed:", err)
      throw err
    }
  }

  // Specific API endpoints
  async getSchools(schoolId = null) {
    const params = schoolId ? { school_id: schoolId } : {}
    const response = await this.get("/schools", params)
    return response.schools || []
  }

  async createSchool(schoolData) {
    return this.post("/schools", schoolData)
  }

  async updateSchool(schoolId, schoolData) {
    return this.put(`/schools/${schoolId}`, schoolData)
  }

  async deleteSchool(schoolId) {
    return this.delete(`/schools/${schoolId}`)
  }

  async getClasses(schoolId = null) {
    const params = schoolId ? { school_id: schoolId } : {}
    const response = await this.get("/classes", params)
    return response.classes || []
  }

  async createClass(classData) {
    return this.post("/classes", classData)
  }

  async updateClass(classId, classData) {
    return this.put(`/classes/${classId}`, classData)
  }

  async deleteClass(classId) {
    return this.delete(`/classes/${classId}`)
  }

  async getCourses(classId = null) {
    const params = classId ? { class_id: classId } : {}
    const response = await this.get("/courses", params)
    return response.courses || []
  }

  async createCourse(courseData) {
    return this.post("/courses", courseData)
  }

  async updateCourse(courseId, courseData) {
    return this.put(`/courses/${courseId}`, courseData)
  }

  async deleteCourse(courseId) {
    return this.delete(`/courses/${courseId}`)
  }

  async getStudents(classId = null) {
    const params = classId ? { class_id: classId } : {}
    const response = await this.get("/students", params)
    return response.students || []
  }

  async importStudents(importData) {
    return this.post("/students/import", importData)
  }

  async uploadStudentResults(courseId, resultsData) {
    return this.post(`/courses/${courseId}/results`, resultsData)
  }

  async getStudentGrades(studentId) {
    // Backend expects GET /grades?student_id=...
    const response = await this.get("/grades", { student_id: studentId })
    return response.grades || []
  }

  async updateStudentProfile(studentId, profileData) {
    return this.put(`/students/${studentId}/profile`, profileData)
  }

  async uploadProfileImage(studentId, imageFile) {
    const formData = new FormData()
    formData.append("image", imageFile)
    return this.upload(`/students/${studentId}/profile-image`, formData)
  }

  async getTeacherCourses(schoolId = null) {
    // Backend expects GET /teachers?school_id=...
    const params = schoolId ? { school_id: schoolId } : {}
    const response = await this.get("/teachers", params)
    return response.teachers || []
  }

  async getDashboardStats() {
    return this.get("/dashboard/stats")
  }
}

export const api = new API()
