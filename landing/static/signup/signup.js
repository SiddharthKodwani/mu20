// Simple client-side password validation
document.addEventListener('DOMContentLoaded', () => {
  const password = document.getElementById('password');
  const confirmPassword = document.getElementById('confirmPassword');
  const passwordError = document.getElementById('passwordError');
  const form = document.getElementById('signupForm');

  confirmPassword.addEventListener('input', () => {
    if (confirmPassword.value !== password.value) {
      passwordError.textContent = "Passwords do not match.";
    } else {
      passwordError.textContent = "";
    }
  });

  form.addEventListener('submit', (e) => {
    if (password.value !== confirmPassword.value) {
      e.preventDefault();
      passwordError.textContent = "Passwords do not match.";
    }
  });
});
