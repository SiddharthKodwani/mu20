document.addEventListener('DOMContentLoaded', () => {
  // --- Progress Tracking ---
  const progress = { calories: 0, protein: 0, fat: 0, carbs: 0 };

  // --- Helper to Save Progress ---
  function saveProgress() {
    localStorage.setItem('nutritionProgress', JSON.stringify(progress));
  }

  // --- Helper to Load Progress ---
  function loadProgress() {
    const saved = localStorage.getItem('nutritionProgress');
    if (saved) {
      const loaded = JSON.parse(saved);
      for (const key in loaded) {
        progress[key] = loaded[key];
        const total = parseInt(
          document.getElementById(`${key}-text`).textContent.split('/')[1]
        );
        const percent = Math.min((progress[key] / total) * 100, 100);
        document.getElementById(`${key}-progress`).style.width = `${percent}%`;
        document.getElementById(`${key}-text`).textContent = `${progress[key]} / ${total}`;
      }
    }
  }

  // --- Function to Update Progress ---
  const updateProgress = (type, value, total) => {
    const current = progress[type] + value;
    progress[type] = current;
    const percent = Math.min((current / total) * 100, 100);
    document.getElementById(`${type}-progress`).style.width = `${percent}%`;
    document.getElementById(`${type}-text`).textContent = `${current} / ${total}`;
    saveProgress(); // 💾 Save every time progress updates
  };

  // --- Initialize Progress Bars ---
  loadProgress(); // 🔄 Load any cached progress first
  updateProgress('calories', 0, parseInt(document.getElementById('calories-text').textContent.split('/')[1]));
  updateProgress('protein', 0, parseInt(document.getElementById('protein-text').textContent.split('/')[1]));
  updateProgress('fat', 0, parseInt(document.getElementById('fat-text').textContent.split('/')[1]));
  updateProgress('carbs', 0, parseInt(document.getElementById('carbs-text').textContent.split('/')[1]));

  // --- Nutrition AI Request ---
  document.getElementById('askBtn').addEventListener('click', async () => {
    const question = document.getElementById('aiQuestion').value.trim();
    const responseText = document.getElementById('aiResponse');

    if (!question) {
      responseText.textContent = "Please type something first.";
      responseText.style.color = "red";
      return;
    }

    // Start “Thinking…” animation
    let dotCount = 0;
    responseText.textContent = "Thinking";
    responseText.style.color = "#555";

    const loadingInterval = setInterval(() => {
      dotCount = (dotCount + 1) % 4;
      responseText.textContent = "Thinking" + ".".repeat(dotCount);
    }, 500);

    try {
      const response = await fetch('/ask_gemini/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();
      clearInterval(loadingInterval); // ✅ Stop animation immediately on success or error

      if (data.nutrients) {
        const { calories, protein, fat, carbs } = data.nutrients;
        responseText.textContent = `Meal logged! +${calories} kcal, ${protein}g protein, ${fat}g fat, ${carbs}g carbs`;
        responseText.style.color = "green";

        updateProgress("calories", calories, parseInt(document.getElementById("calories-text").textContent.split("/")[1]));
        updateProgress("protein", protein, parseInt(document.getElementById("protein-text").textContent.split("/")[1]));
        updateProgress("fat", fat, parseInt(document.getElementById("fat-text").textContent.split("/")[1]));
        updateProgress("carbs", carbs, parseInt(document.getElementById("carbs-text").textContent.split("/")[1]));
      } 
      else if (data.reply) {
        responseText.textContent = data.reply;
        responseText.style.color = "#333";
      } 
      else {
        responseText.textContent = "Unexpected response.";
        responseText.style.color = "red";
        console.log(data);
      }

    } catch (error) {
      clearInterval(loadingInterval); // ✅ Stop animation even on error
      responseText.textContent = "Error contacting Gemini.";
      responseText.style.color = "red";
      console.error(error);
    }
  });
});

// --- Helper for CSRF ---
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

// --- Voice Input Integration ---
const aiInput = document.getElementById('aiQuestion');
const voiceBtn = document.getElementById('voiceBtn');
const askBtn = document.getElementById('askBtn');
const aiResponse = document.getElementById('aiResponse');

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();

  recognition.lang = 'en-IN';
  recognition.interimResults = false;
  recognition.continuous = false;

  // Start recording
  voiceBtn.addEventListener('click', () => {
    recognition.start();
    voiceBtn.classList.add('listening');
  });

  // Capture voice result
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    aiInput.value = transcript;
  };

  // Error handling
  recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    aiResponse.textContent = 'Voice input failed. Please try again.';
    aiResponse.style.color = 'red';
    voiceBtn.classList.remove('listening');
  };

  // Stop animation when recognition ends
  recognition.onend = () => {
    voiceBtn.classList.remove('listening');
  };
} else {
  voiceBtn.style.display = 'none';
  console.warn('Speech recognition not supported in this browser.');
}
