// profile_image_upload.js
// Handles profile image upload and back button

document.addEventListener("DOMContentLoaded", () => {
  const backBtn = document.getElementById("backBtn");
  backBtn?.addEventListener("click", () => {
    window.history.back();
  });

  const form = document.getElementById("imageUploadForm");
  form?.addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("profileImageInput");
    if (input && input.files.length > 0) {
      // TODO: Implement upload logic
      alert("Profile image uploaded (demo only)");
    }
  });
});
