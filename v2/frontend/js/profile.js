import { api } from "./api.js"
import { validation } from "./validation.js"
import { utils } from "./utils.js"
import { error } from "./error.js"
import { roleAccess } from "./role_access.js"
import { auth } from "./auth.js"

class ProfileManagement {
  constructor() {
    this.userProfile = null
    this.isEditing = false
  }

  async init() {
    // Check permissions
    if (!roleAccess.hasPermission("manage_profile")) {
      return
    }

    this.setupEventListeners()
    await this.loadProfile()

    console.log("Profile management initialized")
  }

  setupEventListeners() {
    // Edit profile button
    const editProfileBtn = document.getElementById("editProfileBtn")
    editProfileBtn?.addEventListener("click", () => {
      this.toggleEditMode()
    })

    // Save profile button
    const saveProfileBtn = document.getElementById("saveProfileBtn")
    saveProfileBtn?.addEventListener("click", () => {
      this.saveProfile()
    })

    // Cancel edit button
    const cancelEditBtn = document.getElementById("cancelEditBtn")
    cancelEditBtn?.addEventListener("click", () => {
      this.cancelEdit()
    })

    // Profile form
    const profileForm = document.getElementById("profileForm")
    profileForm?.addEventListener("submit", (e) => {
      e.preventDefault()
      this.saveProfile()
    })

    // Change password button
    const changePasswordBtn = document.getElementById("changePasswordBtn")
    changePasswordBtn?.addEventListener("click", () => {
      this.showChangePasswordModal()
    })
  }

  async loadProfile() {
    try {
      const user = auth.getUser()
      const response = await api.get(`/users/${user.id}/profile`)
      this.userProfile = response.data || user
      this.renderProfile()

      console.log("Profile loaded:", this.userProfile)
    } catch (err) {
      console.error("Failed to load profile:", err)
      error.handleApiError(err, "Loading profile")
    }
  }

  renderProfile() {
    const profileContainer = document.getElementById("profileContainer")
    if (!profileContainer) return

    const template = `
      <div class="profile-content">
        <div class="profile-header glass-panel">
          <div class="profile-image-container">
            <img src="{{profileImage}}" alt="Profile Picture" class="profile-image" id="profileImage">
            <button class="change-image-btn" id="changeImageBtn" {{#unless isEditing}}style="display: none;"{{/unless}}>
              <span class="change-icon">📷</span>
            </button>
          </div>
          <div class="profile-basic-info">
            <h2 id="profileName">{{fullName}}</h2>
            <p id="profileRole">{{role}}</p>
            <p id="profileId">{{userIdLabel}}: {{userId}}</p>
          </div>
          <div class="profile-actions">
            <button class="edit-btn" id="editProfileBtn" {{#if isEditing}}style="display: none;"{{/if}}>
              <span>✏️ Edit Profile</span>
            </button>
            <button class="save-btn" id="saveProfileBtn" {{#unless isEditing}}style="display: none;"{{/unless}}>
              <span>💾 Save Changes</span>
            </button>
            <button class="cancel-btn" id="cancelEditBtn" {{#unless isEditing}}style="display: none;"{{/unless}}>
              <span>❌ Cancel</span>
            </button>
          </div>
        </div>

        <div class="profile-details glass-panel">
          <h3>Personal Information</h3>
          <form class="profile-form" id="profileForm">
            <div class="form-grid">
              <div class="form-group">
                <label for="fullName">Full Name</label>
                <input type="text" id="fullName" name="fullName" value="{{fullName}}" 
                       {{#unless isEditing}}readonly{{/unless}} required>
                <div class="input-glow"></div>
              </div>

              <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" value="{{email}}" 
                       {{#unless isEditing}}readonly{{/unless}} required>
                <div class="input-glow"></div>
              </div>

              <div class="form-group">
                <label for="phone">Phone Number</label>
                <input type="tel" id="phone" name="phone" value="{{phone}}" 
                       {{#unless isEditing}}readonly{{/unless}}>
                <div class="input-glow"></div>
              </div>

              <div class="form-group">
                <label for="dateOfBirth">Date of Birth</label>
                <input type="date" id="dateOfBirth" name="dateOfBirth" value="{{dateOfBirth}}" 
                       {{#unless isEditing}}readonly{{/unless}}>
                <div class="input-glow"></div>
              </div>

              <div class="form-group">
                <label for="gender">Gender</label>
                <select id="gender" name="gender" {{#unless isEditing}}disabled{{/unless}}>
                  <option value="">Select Gender</option>
                  <option value="Male" {{#if isMale}}selected{{/if}}>Male</option>
                  <option value="Female" {{#if isFemale}}selected{{/if}}>Female</option>
                  <option value="Other" {{#if isOther}}selected{{/if}}>Other</option>
                </select>
                <div class="input-glow"></div>
              </div>

              <div class="form-group full-width">
                <label for="address">Address</label>
                <textarea id="address" name="address" rows="3" 
                          {{#unless isEditing}}readonly{{/unless}}>{{address}}</textarea>
                <div class="input-glow"></div>
              </div>
            </div>
          </form>
        </div>

        {{#if showAcademicInfo}}
        <div class="academic-info glass-panel">
          <h3>Academic Information</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Student ID:</span>
              <span class="info-value">{{studentId}}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Class:</span>
              <span class="info-value">{{className}}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Academic Year:</span>
              <span class="info-value">{{academicYear}}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Enrollment Date:</span>
              <span class="info-value">{{enrollmentDate}}</span>
            </div>
          </div>
        </div>
        {{/if}}

        <div class="security-section glass-panel">
          <h3>Security Settings</h3>
          <div class="security-actions">
            <button class="security-btn" id="changePasswordBtn">
              <span class="security-icon">🔒</span>
              <div class="security-content">
                <h4>Change Password</h4>
                <p>Update your account password</p>
              </div>
            </button>
            <button class="security-btn" id="enable2FABtn">
              <span class="security-icon">🛡️</span>
              <div class="security-content">
                <h4>Two-Factor Authentication</h4>
                <p>Add an extra layer of security</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    `

    const templateData = {
      ...this.userProfile,
      isEditing: this.isEditing,
      profileImage: this.userProfile.profileImage || "/placeholder.svg?height=120&width=120",
      userIdLabel: this.getUserIdLabel(),
      userId: this.getUserId(),
      dateOfBirth: this.userProfile.dateOfBirth ? utils.formatDate(this.userProfile.dateOfBirth, "YYYY-MM-DD") : "",
      isMale: this.userProfile.gender === "Male",
      isFemale: this.userProfile.gender === "Female",
      isOther: this.userProfile.gender === "Other",
      showAcademicInfo: this.userProfile.role === "student",
      enrollmentDate: this.userProfile.enrollmentDate
        ? utils.formatDate(this.userProfile.enrollmentDate, "DD/MM/YYYY")
        : "N/A",
    }

    profileContainer.innerHTML = utils.template(template, templateData)

    // Re-setup event listeners after rendering
    this.setupEventListeners()

    // Setup form validation if in edit mode
    if (this.isEditing) {
      const profileForm = document.getElementById("profileForm")
      validation.setupRealTimeValidation(profileForm)
    }
  }

  getUserIdLabel() {
    switch (this.userProfile.role) {
      case "student":
        return "Student ID"
      case "teacher":
        return "Teacher ID"
      case "admin":
        return "Admin ID"
      default:
        return "User ID"
    }
  }

  getUserId() {
    return (
      this.userProfile.studentId ||
      this.userProfile.teacherId ||
      this.userProfile.adminId ||
      this.userProfile.id ||
      "N/A"
    )
  }

  toggleEditMode() {
    this.isEditing = !this.isEditing
    this.renderProfile()

    if (this.isEditing) {
      utils.showNotification("Edit mode enabled", "info")
    }
  }

  async saveProfile() {
    const profileForm = document.getElementById("profileForm")
    if (!profileForm) return

    // Validate form
    const formValidation = validation.validateForm(profileForm)
    if (!formValidation.isValid) {
      error.handleFormErrors(formValidation.errors, profileForm)
      return
    }

    const formData = utils.getFormData(profileForm)

    // Prepare update data
    const updateData = {
      fullName: formData.fullName.trim(),
      email: formData.email.trim(),
      phone: formData.phone?.trim() || "",
      dateOfBirth: formData.dateOfBirth || null,
      gender: formData.gender || null,
      address: formData.address?.trim() || "",
    }

    try {
      const user = auth.getUser()
      const response = await api.updateProfile(user.id, updateData)

      if (response.success) {
        this.userProfile = { ...this.userProfile, ...updateData }
        this.isEditing = false
        this.renderProfile()

        // Update auth user data
        auth.updateUser(this.userProfile)

        utils.showNotification("Profile updated successfully!", "success")
      } else {
        throw new Error(response.message || "Failed to update profile")
      }
    } catch (err) {
      console.error("Failed to update profile:", err)
      error.handleApiError(err, "Updating profile")
    }
  }

  cancelEdit() {
    this.isEditing = false
    this.renderProfile()
    utils.showNotification("Edit cancelled", "info")
  }

  showChangePasswordModal() {
    // Create modal HTML
    const modalHTML = `
      <div class="modal-overlay" id="changePasswordModal">
        <div class="modal glass-panel">
          <div class="modal-header">
            <h3>Change Password</h3>
            <button class="modal-close" id="closePasswordModal">×</button>
          </div>
          <div class="modal-content">
            <form class="password-form" id="passwordForm">
              <div class="form-group">
                <label for="currentPassword">Current Password</label>
                <input type="password" id="currentPassword" name="currentPassword" required>
                <div class="input-glow"></div>
              </div>
              
              <div class="form-group">
                <label for="newPassword">New Password</label>
                <input type="password" id="newPassword" name="newPassword" required 
                       minlength="8" pattern="^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{8,}$">
                <div class="input-glow"></div>
                <small class="form-help">
                  Password must be at least 8 characters with uppercase, lowercase, number, and special character
                </small>
              </div>
              
              <div class="form-group">
                <label for="confirmPassword">Confirm New Password</label>
                <input type="password" id="confirmPassword" name="confirmPassword" required>
                <div class="input-glow"></div>
              </div>
              
              <div class="form-actions">
                <button type="submit" class="submit-btn">
                  <span>Change Password</span>
                  <div class="btn-glow"></div>
                </button>
                <button type="button" class="cancel-btn" id="cancelPasswordChange">
                  <span>Cancel</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    `

    // Add modal to page
    document.body.insertAdjacentHTML("beforeend", modalHTML)

    // Setup modal event listeners
    const modal = document.getElementById("changePasswordModal")
    const closeBtn = document.getElementById("closePasswordModal")
    const cancelBtn = document.getElementById("cancelPasswordChange")
    const passwordForm = document.getElementById("passwordForm")

    const closeModal = () => {
      modal.remove()
    }

    closeBtn.addEventListener("click", closeModal)
    cancelBtn.addEventListener("click", closeModal)
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal()
    })

    passwordForm.addEventListener("submit", async (e) => {
      e.preventDefault()
      await this.handlePasswordChange(passwordForm, closeModal)
    })

    // Setup form validation
    validation.setupRealTimeValidation(passwordForm)

    // Show modal
    modal.classList.add("active")
  }

  async handlePasswordChange(form, closeModal) {
    const formData = utils.getFormData(form)

    // Validate passwords match
    if (formData.newPassword !== formData.confirmPassword) {
      error.showInline(document.getElementById("confirmPassword"), "Passwords do not match")
      return
    }

    try {
      const user = auth.getUser()
      const response = await api.changePassword(user.id, {
        currentPassword: formData.currentPassword,
        newPassword: formData.newPassword,
      })

      if (response.success) {
        utils.showNotification("Password changed successfully!", "success")
        closeModal()
      } else {
        throw new Error(response.message || "Failed to change password")
      }
    } catch (err) {
      console.error("Failed to change password:", err)
      error.handleApiError(err, "Changing password")
    }
  }
}

export const profileManagement = new ProfileManagement()
