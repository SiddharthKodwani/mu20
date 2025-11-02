document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const submitBtn = form.querySelector("button[type='submit']");

  // Create message container dynamically if not in HTML
  let formMessage = document.createElement("p");
  formMessage.id = "formMessage";
  formMessage.style.marginTop = "10px";
  formMessage.style.fontSize = "14px";
  formMessage.style.textAlign = "center";
  form.appendChild(formMessage);

  // Show/Hide password toggle icon
  const toggleBtn = document.createElement("span");
  toggleBtn.innerHTML = "👁️";
  toggleBtn.style.position = "absolute";
  toggleBtn.style.right = "15px";
  toggleBtn.style.top = "36px";
  toggleBtn.style.cursor = "pointer";
  toggleBtn.style.userSelect = "none";
  toggleBtn.title = "Show/Hide Password";
  const passwordWrapper = passwordInput.parentElement;
  passwordWrapper.style.position = "relative";
  passwordWrapper.appendChild(toggleBtn);

  toggleBtn.addEventListener("click", () => {
    if (passwordInput.type === "password") {
      passwordInput.type = "text";
      toggleBtn.textContent = "🙈";
    } else {
      passwordInput.type = "password";
      toggleBtn.textContent = "👁️";
    }
  });

  // Client-side validation before Django submission
  form.addEventListener("submit", (e) => {
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();

    if (!email || !password) {
      e.preventDefault();
      formMessage.textContent = "⚠️ Please fill in all fields.";
      formMessage.style.color = "red";
      return;
    }

    // Basic email format check
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
      e.preventDefault();
      formMessage.textContent = "⚠️ Enter a valid email address.";
      formMessage.style.color = "red";
      return;
    }

    // Show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = "Logging in...";
    submitBtn.style.opacity = "0.7";
    formMessage.textContent = "Authenticating...";
    formMessage.style.color = "#333";
  });
});
