document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("medicalForm");
  const status = document.getElementById("uploadStatus");
  const recordList = document.querySelector(".report-thumbnails");
  const fileInput = form.querySelector("input[name='report']");
  const addFileBtn = document.getElementById("addFileBtn");

  const cachedFiles = [];

  // 🔹 Add PDF file to the list
  addFileBtn.addEventListener("click", () => {
    const file = fileInput.files[0];
    if (!file) {
      alert("Please choose a file first.");
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Only PDF files are allowed.");
      return;
    }

    const exists = cachedFiles.some(f => f.name === file.name);
    if (exists) {
      alert("This file is already added.");
      return;
    }

    cachedFiles.push(file);
    addReport(file.name);
    fileInput.value = "";
  });

  // 🔹 Handle form submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.textContent = "Saving...";

    const formData = new FormData(form);
    cachedFiles.forEach(file => formData.append("report", file));

    try {
      const response = await fetch("/medical_records/", {
        method: "POST",
        body: formData,
        headers: { "X-CSRFToken": form.csrfmiddlewaretoken.value },
      });

      // ✅ If Django redirects (status 302), handle it manually
      if (response.redirected) {
        window.location.href = response.url;
        return;
      }

      const result = await response.json();

      if (result.success) {
        status.textContent = "Saved successfully!";
        cachedFiles.length = 0;
        recordList.innerHTML = "";

        // ✅ Tell parent (chatbot page) to close the modal
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({ action: "closeRecordsModal" }, "*");
        }
      } else {
        status.textContent = "Failed to save. Try again.";
      }

    } catch (error) {
      console.error("Error:", error);
      status.textContent = "Error connecting to server.";
    }
  });

  // 🔹 Add report preview
  function addReport(filename) {
    const div = document.createElement("div");
    div.classList.add("report-item");
    div.innerHTML = `
      <p class="report-name">${filename}</p>
      <button class="delete-btn" data-filename="${filename}">×</button>
    `;
    recordList.prepend(div);
  }

  // 🔹 Handle deleting a file before upload
  recordList.addEventListener("click", (e) => {
    if (!e.target.classList.contains("delete-btn")) return;
    const filename = e.target.dataset.filename;
    if (!confirm(`Remove ${filename}?`)) return;

    const index = cachedFiles.findIndex(f => f.name === filename);
    if (index !== -1) cachedFiles.splice(index, 1);
    e.target.closest(".report-item").remove();
  });
});
