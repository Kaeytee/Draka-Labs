class ChartEngine {
  constructor() {
    this.charts = new Map()
    this.colors = {
      primary: "#00f0ff",
      secondary: "#ff00ff",
      accent: "#00ff88",
      success: "#00ff88",
      warning: "#ffaa00",
      error: "#ff4444",
      gradients: {
        primary: ["#00f0ff", "#0080ff"],
        secondary: ["#ff00ff", "#ff0080"],
        accent: ["#00ff88", "#00cc66"],
        rainbow: ["#ff0080", "#ff4444", "#ffaa00", "#00ff88", "#00f0ff", "#0080ff"],
      },
    }
  }

  createChart(canvasId, type, data, options = {}) {
    const canvas = document.getElementById(canvasId)
    if (!canvas) {
      console.error(`Canvas with id ${canvasId} not found`)
      return null
    }

    const ctx = canvas.getContext("2d")
    const chart = new Chart(ctx, type, data, options)
    this.charts.set(canvasId, chart)
    return chart
  }

  updateChart(canvasId, newData) {
    const chart = this.charts.get(canvasId)
    if (chart) {
      chart.updateData(newData)
    }
  }

  destroyChart(canvasId) {
    const chart = this.charts.get(canvasId)
    if (chart) {
      chart.destroy()
      this.charts.delete(canvasId)
    }
  }

  // Custom Chart Implementation
  createLineChart(canvasId, data, options = {}) {
    return this.createChart(canvasId, "line", data, {
      responsive: true,
      animation: true,
      showGrid: true,
      showLegend: true,
      ...options,
    })
  }

  createBarChart(canvasId, data, options = {}) {
    return this.createChart(canvasId, "bar", data, {
      responsive: true,
      animation: true,
      showGrid: true,
      showLegend: true,
      ...options,
    })
  }

  createPieChart(canvasId, data, options = {}) {
    return this.createChart(canvasId, "pie", data, {
      responsive: true,
      animation: true,
      showLegend: true,
      ...options,
    })
  }

  createDoughnutChart(canvasId, data, options = {}) {
    return this.createChart(canvasId, "doughnut", data, {
      responsive: true,
      animation: true,
      showLegend: true,
      cutout: "60%",
      ...options,
    })
  }

  createRadarChart(canvasId, data, options = {}) {
    return this.createChart(canvasId, "radar", data, {
      responsive: true,
      animation: true,
      showLegend: true,
      ...options,
    })
  }

  // Utility methods
  generateGradient(ctx, colors, direction = "vertical") {
    const gradient =
      direction === "vertical"
        ? ctx.createLinearGradient(0, 0, 0, ctx.canvas.height)
        : ctx.createLinearGradient(0, 0, ctx.canvas.width, 0)

    colors.forEach((color, index) => {
      gradient.addColorStop(index / (colors.length - 1), color)
    })

    return gradient
  }

  getColorPalette(count) {
    const colors = []
    const baseColors = this.colors.gradients.rainbow

    for (let i = 0; i < count; i++) {
      colors.push(baseColors[i % baseColors.length])
    }

    return colors
  }
}

// Custom Chart Class
class Chart {
  constructor(ctx, type, data, options = {}) {
    this.ctx = ctx
    this.canvas = ctx.canvas
    this.type = type
    this.data = data
    this.options = {
      responsive: true,
      animation: true,
      showGrid: true,
      showLegend: true,
      padding: 20,
      ...options,
    }

    this.setupCanvas()
    this.render()
  }

  setupCanvas() {
    const rect = this.canvas.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 1

    this.canvas.width = rect.width * dpr
    this.canvas.height = rect.height * dpr

    this.ctx.scale(dpr, dpr)
    this.canvas.style.width = rect.width + "px"
    this.canvas.style.height = rect.height + "px"
  }

  render() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)

    switch (this.type) {
      case "line":
        this.renderLineChart()
        break
      case "bar":
        this.renderBarChart()
        break
      case "pie":
        this.renderPieChart()
        break
      case "doughnut":
        this.renderDoughnutChart()
        break
      case "radar":
        this.renderRadarChart()
        break
      default:
        console.error(`Chart type ${this.type} not supported`)
    }

    if (this.options.showLegend) {
      this.renderLegend()
    }
  }

  renderLineChart() {
    const { labels, datasets } = this.data
    const padding = this.options.padding
    const chartArea = {
      x: padding,
      y: padding,
      width: this.canvas.width / window.devicePixelRatio - padding * 2,
      height: this.canvas.height / window.devicePixelRatio - padding * 2 - (this.options.showLegend ? 40 : 0),
    }

    // Find min/max values
    let minValue = Number.POSITIVE_INFINITY
    let maxValue = Number.NEGATIVE_INFINITY

    datasets.forEach((dataset) => {
      dataset.data.forEach((value) => {
        minValue = Math.min(minValue, value)
        maxValue = Math.max(maxValue, value)
      })
    })

    // Add some padding to the range
    const range = maxValue - minValue
    minValue -= range * 0.1
    maxValue += range * 0.1

    // Draw grid
    if (this.options.showGrid) {
      this.drawGrid(chartArea, labels.length, 5, minValue, maxValue)
    }

    // Draw lines
    datasets.forEach((dataset, datasetIndex) => {
      const color =
        dataset.borderColor ||
        chartEngine.colors.gradients.rainbow[datasetIndex % chartEngine.colors.gradients.rainbow.length]

      this.ctx.strokeStyle = color
      this.ctx.lineWidth = dataset.borderWidth || 2
      this.ctx.beginPath()

      dataset.data.forEach((value, index) => {
        const x = chartArea.x + (index / (labels.length - 1)) * chartArea.width
        const y = chartArea.y + chartArea.height - ((value - minValue) / (maxValue - minValue)) * chartArea.height

        if (index === 0) {
          this.ctx.moveTo(x, y)
        } else {
          this.ctx.lineTo(x, y)
        }
      })

      this.ctx.stroke()

      // Draw points
      if (dataset.showPoints !== false) {
        this.ctx.fillStyle = color
        dataset.data.forEach((value, index) => {
          const x = chartArea.x + (index / (labels.length - 1)) * chartArea.width
          const y = chartArea.y + chartArea.height - ((value - minValue) / (maxValue - minValue)) * chartArea.height

          this.ctx.beginPath()
          this.ctx.arc(x, y, dataset.pointRadius || 4, 0, Math.PI * 2)
          this.ctx.fill()
        })
      }

      // Fill area under line
      if (dataset.fill) {
        this.ctx.globalAlpha = 0.3
        this.ctx.fillStyle = color
        this.ctx.beginPath()

        dataset.data.forEach((value, index) => {
          const x = chartArea.x + (index / (labels.length - 1)) * chartArea.width
          const y = chartArea.y + chartArea.height - ((value - minValue) / (maxValue - minValue)) * chartArea.height

          if (index === 0) {
            this.ctx.moveTo(x, chartArea.y + chartArea.height)
            this.ctx.lineTo(x, y)
          } else {
            this.ctx.lineTo(x, y)
          }
        })

        this.ctx.lineTo(chartArea.x + chartArea.width, chartArea.y + chartArea.height)
        this.ctx.closePath()
        this.ctx.fill()
        this.ctx.globalAlpha = 1
      }
    })

    // Draw labels
    this.drawLabels(chartArea, labels, minValue, maxValue)
  }

  renderBarChart() {
    const { labels, datasets } = this.data
    const padding = this.options.padding
    const chartArea = {
      x: padding,
      y: padding,
      width: this.canvas.width / window.devicePixelRatio - padding * 2,
      height: this.canvas.height / window.devicePixelRatio - padding * 2 - (this.options.showLegend ? 40 : 0),
    }

    // Find max value
    let maxValue = 0
    datasets.forEach((dataset) => {
      dataset.data.forEach((value) => {
        maxValue = Math.max(maxValue, value)
      })
    })
    maxValue *= 1.1 // Add 10% padding

    // Draw grid
    if (this.options.showGrid) {
      this.drawGrid(chartArea, labels.length, 5, 0, maxValue)
    }

    // Calculate bar dimensions
    const barGroupWidth = chartArea.width / labels.length
    const barWidth = (barGroupWidth / datasets.length) * 0.8
    const barSpacing = barGroupWidth * 0.1

    // Draw bars
    datasets.forEach((dataset, datasetIndex) => {
      const color =
        dataset.backgroundColor ||
        chartEngine.colors.gradients.rainbow[datasetIndex % chartEngine.colors.gradients.rainbow.length]

      this.ctx.fillStyle = color

      dataset.data.forEach((value, index) => {
        const x = chartArea.x + index * barGroupWidth + datasetIndex * barWidth + barSpacing
        const barHeight = (value / maxValue) * chartArea.height
        const y = chartArea.y + chartArea.height - barHeight

        // Create gradient for bars
        const gradient = this.ctx.createLinearGradient(0, y, 0, y + barHeight)
        gradient.addColorStop(0, color)
        gradient.addColorStop(1, color + "80")

        this.ctx.fillStyle = gradient
        this.ctx.fillRect(x, y, barWidth, barHeight)

        // Add value labels on bars
        if (this.options.showValues) {
          this.ctx.fillStyle = "#ffffff"
          this.ctx.font = "12px Arial"
          this.ctx.textAlign = "center"
          this.ctx.fillText(value.toString(), x + barWidth / 2, y - 5)
        }
      })
    })

    // Draw labels
    this.drawLabels(chartArea, labels, 0, maxValue)
  }

  renderPieChart() {
    const { labels, datasets } = this.data
    const dataset = datasets[0]
    const centerX = this.canvas.width / window.devicePixelRatio / 2
    const centerY = this.canvas.height / window.devicePixelRatio / 2
    const radius = Math.min(centerX, centerY) - this.options.padding - (this.options.showLegend ? 20 : 0)

    // Calculate total
    const total = dataset.data.reduce((sum, value) => sum + value, 0)

    let currentAngle = -Math.PI / 2 // Start from top

    dataset.data.forEach((value, index) => {
      const sliceAngle = (value / total) * Math.PI * 2
      const color =
        dataset.backgroundColor?.[index] ||
        chartEngine.colors.gradients.rainbow[index % chartEngine.colors.gradients.rainbow.length]

      // Draw slice
      this.ctx.beginPath()
      this.ctx.moveTo(centerX, centerY)
      this.ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle)
      this.ctx.closePath()

      // Create gradient
      const gradient = this.ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius)
      gradient.addColorStop(0, color)
      gradient.addColorStop(1, color + "80")

      this.ctx.fillStyle = gradient
      this.ctx.fill()

      // Draw border
      this.ctx.strokeStyle = "#ffffff"
      this.ctx.lineWidth = 2
      this.ctx.stroke()

      // Draw percentage labels
      if (this.options.showPercentages) {
        const percentage = ((value / total) * 100).toFixed(1)
        const labelAngle = currentAngle + sliceAngle / 2
        const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7)
        const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7)

        this.ctx.fillStyle = "#ffffff"
        this.ctx.font = "bold 12px Arial"
        this.ctx.textAlign = "center"
        this.ctx.fillText(`${percentage}%`, labelX, labelY)
      }

      currentAngle += sliceAngle
    })
  }

  renderDoughnutChart() {
    const { labels, datasets } = this.data
    const dataset = datasets[0]
    const centerX = this.canvas.width / window.devicePixelRatio / 2
    const centerY = this.canvas.height / window.devicePixelRatio / 2
    const outerRadius = Math.min(centerX, centerY) - this.options.padding - (this.options.showLegend ? 20 : 0)
    const innerRadius = outerRadius * (this.options.cutout ? Number.parseFloat(this.options.cutout) / 100 : 0.6)

    // Calculate total
    const total = dataset.data.reduce((sum, value) => sum + value, 0)

    let currentAngle = -Math.PI / 2 // Start from top

    dataset.data.forEach((value, index) => {
      const sliceAngle = (value / total) * Math.PI * 2
      const color =
        dataset.backgroundColor?.[index] ||
        chartEngine.colors.gradients.rainbow[index % chartEngine.colors.gradients.rainbow.length]

      // Draw slice
      this.ctx.beginPath()
      this.ctx.arc(centerX, centerY, outerRadius, currentAngle, currentAngle + sliceAngle)
      this.ctx.arc(centerX, centerY, innerRadius, currentAngle + sliceAngle, currentAngle, true)
      this.ctx.closePath()

      // Create gradient
      const gradient = this.ctx.createRadialGradient(centerX, centerY, innerRadius, centerX, centerY, outerRadius)
      gradient.addColorStop(0, color)
      gradient.addColorStop(1, color + "80")

      this.ctx.fillStyle = gradient
      this.ctx.fill()

      // Draw border
      this.ctx.strokeStyle = "#ffffff"
      this.ctx.lineWidth = 2
      this.ctx.stroke()

      currentAngle += sliceAngle
    })

    // Draw center text if provided
    if (this.options.centerText) {
      this.ctx.fillStyle = "#ffffff"
      this.ctx.font = "bold 16px Arial"
      this.ctx.textAlign = "center"
      this.ctx.fillText(this.options.centerText, centerX, centerY)
    }
  }

  renderRadarChart() {
    const { labels, datasets } = this.data
    const centerX = this.canvas.width / window.devicePixelRatio / 2
    const centerY = this.canvas.height / window.devicePixelRatio / 2
    const radius = Math.min(centerX, centerY) - this.options.padding - (this.options.showLegend ? 20 : 0)

    // Find max value
    let maxValue = 0
    datasets.forEach((dataset) => {
      dataset.data.forEach((value) => {
        maxValue = Math.max(maxValue, value)
      })
    })

    // Draw grid circles
    const gridLevels = 5
    for (let i = 1; i <= gridLevels; i++) {
      const gridRadius = (radius / gridLevels) * i
      this.ctx.beginPath()
      this.ctx.arc(centerX, centerY, gridRadius, 0, Math.PI * 2)
      this.ctx.strokeStyle = "rgba(255, 255, 255, 0.2)"
      this.ctx.lineWidth = 1
      this.ctx.stroke()
    }

    // Draw grid lines
    const angleStep = (Math.PI * 2) / labels.length
    labels.forEach((label, index) => {
      const angle = index * angleStep - Math.PI / 2
      const x = centerX + Math.cos(angle) * radius
      const y = centerY + Math.sin(angle) * radius

      this.ctx.beginPath()
      this.ctx.moveTo(centerX, centerY)
      this.ctx.lineTo(x, y)
      this.ctx.strokeStyle = "rgba(255, 255, 255, 0.2)"
      this.ctx.lineWidth = 1
      this.ctx.stroke()

      // Draw labels
      const labelX = centerX + Math.cos(angle) * (radius + 15)
      const labelY = centerY + Math.sin(angle) * (radius + 15)

      this.ctx.fillStyle = "#ffffff"
      this.ctx.font = "12px Arial"
      this.ctx.textAlign = "center"
      this.ctx.fillText(label, labelX, labelY)
    })

    // Draw data
    datasets.forEach((dataset, datasetIndex) => {
      const color =
        dataset.borderColor ||
        chartEngine.colors.gradients.rainbow[datasetIndex % chartEngine.colors.gradients.rainbow.length]

      this.ctx.beginPath()
      dataset.data.forEach((value, index) => {
        const angle = index * angleStep - Math.PI / 2
        const dataRadius = (value / maxValue) * radius
        const x = centerX + Math.cos(angle) * dataRadius
        const y = centerY + Math.sin(angle) * dataRadius

        if (index === 0) {
          this.ctx.moveTo(x, y)
        } else {
          this.ctx.lineTo(x, y)
        }
      })
      this.ctx.closePath()

      // Fill area
      if (dataset.fill) {
        this.ctx.fillStyle = color + "40"
        this.ctx.fill()
      }

      // Draw border
      this.ctx.strokeStyle = color
      this.ctx.lineWidth = dataset.borderWidth || 2
      this.ctx.stroke()

      // Draw points
      dataset.data.forEach((value, index) => {
        const angle = index * angleStep - Math.PI / 2
        const dataRadius = (value / maxValue) * radius
        const x = centerX + Math.cos(angle) * dataRadius
        const y = centerY + Math.sin(angle) * dataRadius

        this.ctx.beginPath()
        this.ctx.arc(x, y, dataset.pointRadius || 4, 0, Math.PI * 2)
        this.ctx.fillStyle = color
        this.ctx.fill()
      })
    })
  }

  drawGrid(chartArea, xSteps, ySteps, minValue, maxValue) {
    this.ctx.strokeStyle = "rgba(255, 255, 255, 0.1)"
    this.ctx.lineWidth = 1

    // Vertical grid lines
    for (let i = 0; i <= xSteps; i++) {
      const x = chartArea.x + (i / xSteps) * chartArea.width
      this.ctx.beginPath()
      this.ctx.moveTo(x, chartArea.y)
      this.ctx.lineTo(x, chartArea.y + chartArea.height)
      this.ctx.stroke()
    }

    // Horizontal grid lines
    for (let i = 0; i <= ySteps; i++) {
      const y = chartArea.y + (i / ySteps) * chartArea.height
      this.ctx.beginPath()
      this.ctx.moveTo(chartArea.x, y)
      this.ctx.lineTo(chartArea.x + chartArea.width, y)
      this.ctx.stroke()

      // Y-axis labels
      const value = maxValue - (i / ySteps) * (maxValue - minValue)
      this.ctx.fillStyle = "rgba(255, 255, 255, 0.7)"
      this.ctx.font = "10px Arial"
      this.ctx.textAlign = "right"
      this.ctx.fillText(value.toFixed(1), chartArea.x - 5, y + 3)
    }
  }

  drawLabels(chartArea, labels, minValue, maxValue) {
    this.ctx.fillStyle = "rgba(255, 255, 255, 0.7)"
    this.ctx.font = "10px Arial"
    this.ctx.textAlign = "center"

    // X-axis labels
    labels.forEach((label, index) => {
      const x = chartArea.x + (index / (labels.length - 1)) * chartArea.width
      const y = chartArea.y + chartArea.height + 15
      this.ctx.fillText(label, x, y)
    })
  }

  renderLegend() {
    const legendY = this.canvas.height / window.devicePixelRatio - 30
    const legendItemWidth = 100
    const startX = (this.canvas.width / window.devicePixelRatio - this.data.datasets.length * legendItemWidth) / 2

    this.data.datasets.forEach((dataset, index) => {
      const x = startX + index * legendItemWidth
      const color =
        dataset.borderColor ||
        dataset.backgroundColor ||
        chartEngine.colors.gradients.rainbow[index % chartEngine.colors.gradients.rainbow.length]

      // Draw color box
      this.ctx.fillStyle = color
      this.ctx.fillRect(x, legendY, 12, 12)

      // Draw label
      this.ctx.fillStyle = "#ffffff"
      this.ctx.font = "12px Arial"
      this.ctx.textAlign = "left"
      this.ctx.fillText(dataset.label || `Dataset ${index + 1}`, x + 16, legendY + 9)
    })
  }

  updateData(newData) {
    this.data = newData
    this.render()
  }

  destroy() {
    // Clean up event listeners and resources
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)
  }
}

export const chartEngine = new ChartEngine()
