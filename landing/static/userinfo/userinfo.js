document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('userinfoForm');
  const message = document.getElementById('formMessage');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const requiredFields = ['age', 'gender', 'height', 'weight', 'activity', 'diet'];
    let valid = true;

    // Validate all required fields
    requiredFields.forEach(id => {
      const field = document.getElementById(id);
      if (!field.value.trim()) {
        field.style.borderColor = 'red';
        valid = false;
      } else {
        field.style.borderColor = '#ccc';
      }
    });

    if (!valid) {
      message.textContent = "Please fill all fields.";
      message.style.color = "red";
      return;
    }

    // Prepare form data
    const formData = new FormData(form);

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        message.textContent = "Information saved successfully! Redirecting...";
        message.style.color = "green";

        setTimeout(() => {
          window.location.href = '/dashboard/';
        }, 1200);
      } else {
        message.textContent = data.error || "Something went wrong.";
        message.style.color = "red";
      }
    } catch (error) {
      message.textContent = "Error submitting form. Please try again.";
      message.style.color = "red";
      console.error(error);
    }
  });
});

// Helper: get CSRF token from cookies
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}
