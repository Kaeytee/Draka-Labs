import { api } from "./api.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"
import { auth } from "./auth.js"
import { chartEngine } from "./charts.js"

class AnalyticsDashboard {
  constructor() {
    this.analyticsData = {}
    this.currentSection = "overview"
    this.dateRange = 30
    this.charts = new Map()
    this.init()
  }

  async init() {
    // Check permissions
    if (!roleAccess.hasPermission("view_analytics")) {
      window.location.href = "error.html?code=403&message=Access denied"
      return
    }

    this.setupEventListeners()
    this.setupNavigation()
    await this.loadAnalyticsData()

    console.log("Analytics dashboard initialized")
  }

  setupEventListeners() {
    // Logout button
    const logoutBtn = document.getElementById("logoutBtn")
    logoutBtn?.addEventListener("click", () => {
      if (confirm("Are you sure you want to logout?")) {
        auth.logout()
      }
    })

    // Date range selector
    const dateRange = document.getElementById("dateRange")
    dateRange?.addEventListener("change", (e) => {
      this.dateRange = e.target.value
      this.loadAnalyticsData()
    })

    // Export button
    const exportBtn = document.getElementById("exportBtn")
    exportBtn?.addEventListener("click", () => {
      this.exportAnalytics()
    })

    // Refresh button
    const refreshBtn = document.getElementById("refreshBtn")
    refreshBtn?.addEventListener("click", () => {
      this.loadAnalyticsData()
    })

    // Chart type toggles
    document.addEventListener("click", (e) => {
      if (e.target.classList.contains("chart-btn")) {
        const chartType = e.target.dataset.chart
        const container = e.target.closest(".chart-container")
        const canvasId = container.querySelector("canvas").id

        // Update active state
        container.querySelectorAll(".chart-btn").forEach((btn) => btn.classList.remove("active"))
        e.target.classList.add("active")

        // Re-render chart with new type
        this.updateChartType(canvasId, chartType)
      }
    })

    // Performance filter
    const performanceFilter = document.getElementById("performanceFilter")
    performanceFilter?.addEventListener("change", () => {
      this.updatePerformanceChart()
    })

    // Trend controls
    document.addEventListener("click", (e) => {
      if (e.target.classList.contains("trend-btn")) {
        const trendType = e.target.dataset.trend

        // Update active state
        document.querySelectorAll(".trend-btn").forEach((btn) => btn.classList.remove("active"))
        e.target.classList.add("active")

        this.updateTrendsChart(trendType)
      }
    })

    // Comparison controls
    const compareBy = document.getElementById("compareBy")
    compareBy?.addEventListener("change", () => {
      this.updateComparisonOptions()
    })

    const generateComparison = document.getElementById("generateComparison")
    generateComparison?.addEventListener("click", () => {
      this.generateComparisonChart()
    })

    // Report generation
    const generateReport = document.getElementById("generateReport")
    generateReport?.addEventListener("click", () => {
      this.generateReport()
    })
  }

  setupNavigation() {
    const navLinks = document.querySelectorAll(".nav-link")
    navLinks.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault()
        const section = link.dataset.section
        this.showSection(section)

        // Update active state
        navLinks.forEach((l) => l.classList.remove("active"))
        link.classList.add("active")
      })
    })

    // Show initial section
    this.showSection("overview")
    document.querySelector('[data-section="overview"]')?.classList.add("active")
  }

  showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll(".content-section").forEach((section) => {
      section.classList.add("hidden")
    })

    // Show selected section
    const targetSection = document.getElementById(`${sectionName}-section`)
    if (targetSection) {
      targetSection.classList.remove("hidden")
      this.currentSection = sectionName

      // Update page title
      const pageTitle = document.getElementById("pageTitle")
      if (pageTitle) {
        pageTitle.textContent = `Analytics - ${this.capitalizeFirst(sectionName)}`
      }

      // Load section-specific data
      this.loadSectionData(sectionName)
    }
  }

  async loadAnalyticsData() {
    this.showLoading(true)

    try {
      const response = await api.get(`/analytics?range=${this.dateRange}`)
      this.analyticsData = response.data || {}

      this.updateUserInfo()
      this.loadSectionData(this.currentSection)

      console.log("Analytics data loaded:", this.analyticsData)
    } catch (err) {
      console.error("Failed to load analytics data:", err)
      error.handleApiError(err, "Loading analytics")
    } finally {
      this.showLoading(false)
    }
  }

  async loadSectionData(section) {
    switch (section) {
      case "overview":
        this.renderOverviewCharts()
        break
      case "performance":
        this.renderPerformanceCharts()
        break
      case "grades":
        this.renderGradeCharts()
        break
      case "trends":
        this.renderTrendCharts()
        break
      case "comparison":
        this.setupComparisonSection()
        break
      case "reports":
        this.loadRecentReports()
        break
    }
  }

  renderOverviewCharts() {
    // Performance Overview Chart
    const overviewData = {
      labels: this.analyticsData.months || ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      datasets: [
        {
          label: "Average Score",
          data: this.analyticsData.monthlyScores || [75, 78, 82, 79, 85, 88],
          borderColor: chartEngine.colors.primary,
          backgroundColor: chartEngine.colors.primary + "40",
          fill: true,
          tension: 0.4,
        },
      ],
    }

    chartEngine.createLineChart("overviewChart", overviewData, {
      showPoints: true,
      showGrid: true,
    })

    // Grade Distribution Chart
    const gradeData = {
      labels: ["A", "B", "C", "D", "F"],
      datasets: [
        {
          data: this.analyticsData.gradeDistribution || [25, 35, 20, 15, 5],
          backgroundColor: [
            chartEngine.colors.accent,
            chartEngine.colors.primary,
            "#ffaa00",
            "#ff6600",
            chartEngine.colors.error,
          ],
        },
      ],
    }

    chartEngine.createDoughnutChart("gradeDistributionChart", gradeData, {
      centerText: "Grades",
      showPercentages: true,
    })

    // Course Performance Chart
    const courseData = {
      labels: this.analyticsData.courses?.map((c) => c.name) || ["Math", "Science", "English", "History"],
      datasets: [
        {
          label: "Average Score",
          data: this.analyticsData.courses?.map((c) => c.avgScore) || [85, 78, 92, 76],
          backgroundColor: chartEngine.getColorPalette(4),
        },
      ],
    }

    chartEngine.createBarChart("coursePerformanceChart", courseData, {
      showValues: true,
    })

    // Update key metrics
    this.updateKeyMetrics()
  }

  renderPerformanceCharts() {
    // Performance Trend Chart
    const trendData = {
      labels: this.analyticsData.weeks || ["Week 1", "Week 2", "Week 3", "Week 4"],
      datasets: [
        {
          label: "Top Performers",
          data: [95, 94, 96, 97],
          borderColor: chartEngine.colors.accent,
          backgroundColor: chartEngine.colors.accent + "20",
          fill: true,
        },
        {
          label: "Average Performers",
          data: [75, 77, 76, 78],
          borderColor: chartEngine.colors.primary,
          backgroundColor: chartEngine.colors.primary + "20",
          fill: true,
        },
        {
          label: "Struggling Students",
          data: [45, 48, 52, 55],
          borderColor: chartEngine.colors.error,
          backgroundColor: chartEngine.colors.error + "20",
          fill: true,
        },
      ],
    }

    chartEngine.createLineChart("performanceTrendChart", trendData, {
      showPoints: true,
      showGrid: true,
    })

    // Subject Performance Radar
    const subjectData = {
      labels: ["Math", "Science", "English", "History", "Art", "PE"],
      datasets: [
        {
          label: "Class Average",
          data: [85, 78, 92, 76, 88, 82],
          borderColor: chartEngine.colors.primary,
          backgroundColor: chartEngine.colors.primary + "40",
          fill: true,
        },
      ],
    }

    chartEngine.createRadarChart("subjectPerformanceChart", subjectData)

    // Class Performance Comparison
    const classData = {
      labels: this.analyticsData.classes?.map((c) => c.name) || ["Class A", "Class B", "Class C"],
      datasets: [
        {
          label: "Average GPA",
          data: this.analyticsData.classes?.map((c) => c.avgGPA) || [3.2, 3.5, 2.8],
          backgroundColor: chartEngine.getColorPalette(3),
        },
      ],
    }

    chartEngine.createBarChart("classPerformanceChart", classData, {
      showValues: true,
    })
  }

  renderGradeCharts() {
    // Grade Trends Over Time
    const gradeTrendData = {
      labels: this.analyticsData.semesters || ["Fall 2023", "Spring 2024", "Fall 2024"],
      datasets: [
        {
          label: "A Grades",
          data: [25, 28, 30],
          borderColor: chartEngine.colors.accent,
          backgroundColor: chartEngine.colors.accent + "40",
          fill: true,
        },
        {
          label: "B Grades",
          data: [35, 33, 38],
          borderColor: chartEngine.colors.primary,
          backgroundColor: chartEngine.colors.primary + "40",
          fill: true,
        },
        {
          label: "C Grades",
          data: [25, 27, 22],
          borderColor: "#ffaa00",
          backgroundColor: "#ffaa0040",
          fill: true,
        },
      ],
    }

    chartEngine.createLineChart("gradeTrendsChart", gradeTrendData, {
      showPoints: true,
      showGrid: true,
    })

    // Subject Grade Distribution
    const subjectGradeData = {
      labels: ["Math", "Science", "English", "History"],
      datasets: [
        {
          label: "A",
          data: [20, 25, 35, 15],
          backgroundColor: chartEngine.colors.accent,
        },
        {
          label: "B",
          data: [30, 35, 40, 25],
          backgroundColor: chartEngine.colors.primary,
        },
        {
          label: "C",
          data: [35, 25, 20, 40],
          backgroundColor: "#ffaa00",
        },
        {
          label: "D",
          data: [10, 10, 4, 15],
          backgroundColor: "#ff6600",
        },
        {
          label: "F",
          data: [5, 5, 1, 5],
          backgroundColor: chartEngine.colors.error,
        },
      ],
    }

    chartEngine.createBarChart("subjectGradesChart", subjectGradeData, {
      showValues: false,
    })

    // Pass/Fail Rates
    const passFailData = {
      labels: ["Pass", "Fail"],
      datasets: [
        {
          data: [85, 15],
          backgroundColor: [chartEngine.colors.accent, chartEngine.colors.error],
        },
      ],
    }

    chartEngine.createPieChart("passFailChart", passFailData, {
      showPercentages: true,
    })

    // Update grade analysis
    this.updateGradeAnalysis()
  }

  renderTrendCharts() {
    // Academic Trends Chart
    const trendsData = {
      labels: this.analyticsData.trendLabels || ["Q1", "Q2", "Q3", "Q4"],
      datasets: [
        {
          label: "GPA Trend",
          data: [3.2, 3.3, 3.4, 3.5],
          borderColor: chartEngine.colors.primary,
          backgroundColor: chartEngine.colors.primary + "40",
          fill: true,
          tension: 0.4,
        },
        {
          label: "Attendance Rate",
          data: [85, 87, 89, 91],
          borderColor: chartEngine.colors.accent,
          backgroundColor: chartEngine.colors.accent + "40",
          fill: true,
          tension: 0.4,
        },
      ],
    }

    chartEngine.createLineChart("academicTrendsChart", trendsData, {
      showPoints: true,
      showGrid: true,
    })

    // Update trend insights
    this.updateTrendInsights()
  }

  setupComparisonSection() {
    this.updateComparisonOptions()
  }

  updateComparisonOptions() {
    const compareBy = document.getElementById("compareBy")?.value
    const itemsContainer = document.getElementById("comparisonItems")

    if (!itemsContainer) return

    let options = []
    switch (compareBy) {
      case "class":
        options = this.analyticsData.classes || [
          { id: 1, name: "Class A" },
          { id: 2, name: "Class B" },
          { id: 3, name: "Class C" },
        ]
        break
      case "subject":
        options = this.analyticsData.subjects || [
          { id: 1, name: "Mathematics" },
          { id: 2, name: "Science" },
          { id: 3, name: "English" },
          { id: 4, name: "History" },
        ]
        break
      case "semester":
        options = this.analyticsData.semesters || [
          { id: 1, name: "Fall 2023" },
          { id: 2, name: "Spring 2024" },
          { id: 3, name: "Fall 2024" },
        ]
        break
      case "teacher":
        options = this.analyticsData.teachers || [
          { id: 1, name: "Dr. Smith" },
          { id: 2, name: "Prof. Johnson" },
          { id: 3, name: "Ms. Davis" },
        ]
        break
    }

    const template = `
      {{#each options}}
      <label class="comparison-option">
        <input type="checkbox" value="{{id}}" data-name="{{name}}">
        <span>{{name}}</span>
      </label>
      {{/each}}
    `

    itemsContainer.innerHTML = utils.template(template, { options })
  }

  generateComparisonChart() {
    const selectedItems = Array.from(document.querySelectorAll("#comparisonItems input:checked"))

    if (selectedItems.length < 2) {
      utils.showNotification("Please select at least 2 items to compare", "warning")
      return
    }

    const compareBy = document.getElementById("compareBy")?.value
    const labels = selectedItems.map((item) => item.dataset.name)

    // Generate sample comparison data
    const comparisonData = {
      labels: ["Average Score", "Pass Rate", "Improvement", "Attendance"],
      datasets: selectedItems.map((item, index) => ({
        label: item.dataset.name,
        data: [
          Math.floor(Math.random() * 30) + 70, // Average Score
          Math.floor(Math.random() * 20) + 80, // Pass Rate
          Math.floor(Math.random() * 10) + 5, // Improvement
          Math.floor(Math.random() * 15) + 85, // Attendance
        ],
        borderColor: chartEngine.getColorPalette(selectedItems.length)[index],
        backgroundColor: chartEngine.getColorPalette(selectedItems.length)[index] + "40",
        fill: true,
      })),
    }

    chartEngine.createRadarChart("comparisonChart", comparisonData)
  }

  async loadRecentReports() {
    const reportsList = document.getElementById("recentReportsList")
    if (!reportsList) return

    try {
      const response = await api.get("/reports/recent")
      const reports = response.data || []

      if (reports.length === 0) {
        reportsList.innerHTML = `
          <div class="no-reports">
            <div class="no-data-icon">📋</div>
            <p>No recent reports found</p>
          </div>
        `
        return
      }

      const template = `
        {{#each reports}}
        <div class="report-item glass-panel">
          <div class="report-info">
            <h4>{{name}}</h4>
            <p>{{description}}</p>
            <span class="report-date">{{formattedDate}}</span>
          </div>
          <div class="report-actions">
            <button class="action-btn small" data-action="download" data-id="{{id}}">
              📥 Download
            </button>
            <button class="action-btn small" data-action="view" data-id="{{id}}">
              👁️ View
            </button>
          </div>
        </div>
        {{/each}}
      `

      const reportsWithFormatting = reports.map((report) => ({
        ...report,
        formattedDate: utils.formatDate(report.createdAt, "DD/MM/YYYY"),
      }))

      reportsList.innerHTML = utils.template(template, { reports: reportsWithFormatting })

      // Add event listeners for report actions
      reportsList.addEventListener("click", (e) => {
        if (e.target.dataset.action) {
          const action = e.target.dataset.action
          const reportId = e.target.dataset.id
          this.handleReportAction(action, reportId)
        }
      })
    } catch (err) {
      console.error("Failed to load recent reports:", err)
      reportsList.innerHTML = `
        <div class="error-message">
          <p>Failed to load recent reports</p>
        </div>
      `
    }
  }

  updateKeyMetrics() {
    const metrics = {
      avgGPA: this.analyticsData.avgGPA || 3.2,
      totalStudents: this.analyticsData.totalStudents || 1250,
      passRate: this.analyticsData.passRate || 85,
      improvementRate: this.analyticsData.improvementRate || 12,
    }

    Object.entries(metrics).forEach(([key, value]) => {
      const element = document.getElementById(key)
      if (element) {
        if (key === "avgGPA") {
          this.animateValue(element, 0, value, 1000, 1)
        } else if (key === "passRate" || key === "improvementRate") {
          this.animateValue(element, 0, value, 1000, 0, "%")
        } else {
          this.animateValue(element, 0, value, 1000, 0)
        }
      }
    })
  }

  updateGradeAnalysis() {
    const analysisContainer = document.getElementById("gradeAnalysisContent")
    if (!analysisContainer) return

    const analysis = this.generateGradeAnalysis()

    const template = `
      <div class="analysis-insights">
        {{#each insights}}
        <div class="insight-item">
          <div class="insight-icon {{type}}">{{icon}}</div>
          <div class="insight-content">
            <h4>{{title}}</h4>
            <p>{{description}}</p>
          </div>
        </div>
        {{/each}}
      </div>
    `

    analysisContainer.innerHTML = utils.template(template, { insights: analysis })
  }

  updateTrendInsights() {
    const insightsContainer = document.getElementById("trendInsights")
    if (!insightsContainer) return

    const insights = this.generateTrendInsights()

    const template = `
      {{#each insights}}
      <div class="insight-item">
        <div class="insight-indicator {{trend}}"></div>
        <div class="insight-content">
          <h4>{{title}}</h4>
          <p>{{description}}</p>
          <span class="insight-value">{{value}}</span>
        </div>
      </div>
      {{/each}}
    `

    insightsContainer.innerHTML = utils.template(template, { insights })
  }

  generateGradeAnalysis() {
    return [
      {
        type: "positive",
        icon: "📈",
        title: "Improving Performance",
        description: "Overall grade distribution shows 15% improvement in A and B grades compared to last semester.",
      },
      {
        type: "warning",
        icon: "⚠️",
        title: "Math Concerns",
        description:
          "Mathematics shows higher failure rates (12%) compared to other subjects. Consider additional support.",
      },
      {
        type: "info",
        icon: "ℹ️",
        title: "Consistent Performance",
        description: "English and Science maintain stable grade distributions with minimal variation.",
      },
    ]
  }

  generateTrendInsights() {
    return [
      {
        trend: "up",
        title: "GPA Improvement",
        description: "Average GPA has increased by 0.3 points over the last quarter",
        value: "+0.3",
      },
      {
        trend: "up",
        title: "Attendance Rate",
        description: "Student attendance has improved consistently",
        value: "+6%",
      },
      {
        trend: "down",
        title: "Dropout Risk",
        description: "Students at risk of dropping out has decreased",
        value: "-8%",
      },
    ]
  }

  updateChartType(canvasId, chartType) {
    const chart = chartEngine.charts.get(canvasId)
    if (chart) {
      // Get current data
      const currentData = chart.data

      // Destroy current chart
      chartEngine.destroyChart(canvasId)

      // Create new chart with different type
      if (chartType === "line") {
        chartEngine.createLineChart(canvasId, currentData)
      } else if (chartType === "bar") {
        chartEngine.createBarChart(canvasId, currentData)
      }
    }
  }

  updatePerformanceChart() {
    const filter = document.getElementById("performanceFilter")?.value
    // Update the performance trend chart based on filter
    // This would typically fetch new data from the API
    console.log("Updating performance chart with filter:", filter)
  }

  updateTrendsChart(trendType) {
    // Update trends chart based on selected time period
    console.log("Updating trends chart for:", trendType)
  }

  async generateReport() {
    const reportType = document.getElementById("reportType")?.value
    const startDate = document.getElementById("reportStartDate")?.value
    const endDate = document.getElementById("reportEndDate")?.value
    const format = document.getElementById("reportFormat")?.value

    if (!startDate || !endDate) {
      utils.showNotification("Please select start and end dates", "warning")
      return
    }

    this.showLoading(true)

    try {
      const response = await api.post("/reports/generate", {
        type: reportType,
        startDate,
        endDate,
        format,
      })

      if (response.data.success) {
        utils.showNotification("Report generated successfully!", "success")

        // Download the report
        if (response.data.downloadUrl) {
          const link = document.createElement("a")
          link.href = response.data.downloadUrl
          link.download = response.data.filename
          link.click()
        }

        // Refresh recent reports list
        this.loadRecentReports()
      }
    } catch (err) {
      console.error("Failed to generate report:", err)
      error.handleApiError(err, "Generating report")
    } finally {
      this.showLoading(false)
    }
  }

  handleReportAction(action, reportId) {
    switch (action) {
      case "download":
        this.downloadReport(reportId)
        break
      case "view":
        this.viewReport(reportId)
        break
      default:
        console.log(`Report action not implemented: ${action}`)
    }
  }

  async downloadReport(reportId) {
    try {
      const response = await api.get(`/reports/${reportId}/download`)

      if (response.data.downloadUrl) {
        const link = document.createElement("a")
        link.href = response.data.downloadUrl
        link.download = response.data.filename
        link.click()

        utils.showNotification("Report download started", "success")
      }
    } catch (err) {
      console.error("Failed to download report:", err)
      utils.showNotification("Failed to download report", "error")
    }
  }

  viewReport(reportId) {
    // Open report in new window/tab
    window.open(`/reports/${reportId}/view`, "_blank")
  }

  async exportAnalytics() {
    try {
      const response = await api.post("/analytics/export", {
        section: this.currentSection,
        dateRange: this.dateRange,
        format: "excel",
      })

      if (response.data.downloadUrl) {
        const link = document.createElement("a")
        link.href = response.data.downloadUrl
        link.download = `analytics_${this.currentSection}_${new Date().toISOString().split("T")[0]}.xlsx`
        link.click()

        utils.showNotification("Analytics exported successfully!", "success")
      }
    } catch (err) {
      console.error("Failed to export analytics:", err)
      utils.showNotification("Failed to export analytics", "error")
    }
  }

  updateUserInfo() {
    const user = auth.getUser()
    if (!user) return

    const userName = document.getElementById("userName")
    const avatarImg = document.getElementById("avatarImg")

    if (userName) {
      userName.textContent = user.fullName || user.name || "User"
    }

    if (avatarImg && user.profileImage) {
      avatarImg.src = user.profileImage
    }
  }

  animateValue(element, start, end, duration, decimals = 0, suffix = "") {
    const startTime = performance.now()

    const updateValue = (currentTime) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)

      // Easing function
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      const currentValue = start + (end - start) * easeOutQuart

      element.textContent = currentValue.toFixed(decimals) + suffix

      if (progress < 1) {
        requestAnimationFrame(updateValue)
      }
    }

    requestAnimationFrame(updateValue)
  }

  capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1)
  }

  showLoading(show) {
    const loadingOverlay = document.getElementById("loadingOverlay")
    if (loadingOverlay) {
      loadingOverlay.classList.toggle("active", show)
    }
  }
}

// Initialize when DOM is loaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => new AnalyticsDashboard())
} else {
  new AnalyticsDashboard()
}

export const analyticsDashboard = new AnalyticsDashboard()
