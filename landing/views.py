from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings
import google.generativeai as genai
import json, os
import pdfplumber
from datetime import date
from .models import Profile, MedicalReport
from django.views.decorators.clickjacking import xframe_options_exempt

# ----------------------------
# Gemini Configuration
# ----------------------------
# Consider loading the key from environment variables for safety
genai.configure(api_key="AIzaSyCX6Y3PslsPUKKcq8pyLpz9fOyp0akHfjw")


# ----------------------------
# Authentication Views
# ----------------------------


def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Since you use email as username, we must find the user by email
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials. Please try again.")

    return render(request, 'login.html')



def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

def landing(request):
    return render(request, "landing.html")


def signup(request):
    if request.method == "POST":
        full_name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmPassword")

        if password != confirm_password:
            return render(request, "signup.html", {"error": "Passwords do not match"})

        if User.objects.filter(username=email).exists():
            return render(request, "signup.html", {"error": "User already exists"})

        user = User.objects.create_user(username=email, email=email, password=password)
        Profile.objects.create(user=user, full_name=full_name)
        login(request, user)
        return redirect("userinfo")

    return render(request, "signup.html")


# ----------------------------
# User Info + Dashboard
# ----------------------------

@login_required
def userinfo(request):
    if request.method == "POST":
        user = request.user
        try:
            profile = Profile.objects.get(user=user)

            input_age = int(request.POST.get("age"))
            input_gender = request.POST.get("gender")
            input_height_ft = float(request.POST.get("height"))
            input_weight_kg = float(request.POST.get("weight"))
            input_activity = request.POST.get("activity")
            input_diet = request.POST.get("diet")

            height_m = input_height_ft * 0.3048
            bmi = input_weight_kg / (height_m ** 2)

            if bmi < 18.5:
                bmi_category = "Underweight"
            elif bmi < 25:
                bmi_category = "Normal weight"
            elif bmi < 30:
                bmi_category = "Overweight"
            else:
                bmi_category = "Obese"

            if input_gender.lower() == "male":
                bmr = 10 * input_weight_kg + 6.25 * (height_m * 100) - 5 * input_age + 5
            else:
                bmr = 10 * input_weight_kg + 6.25 * (height_m * 100) - 5 * input_age - 161

            activity_map = {
                "light": 1.375,
                "lightly active": 1.375,
                "moderate": 1.55,
                "moderately active": 1.55,
                "active": 1.725,
                "very active": 1.9,
            }
            multiplier = activity_map.get(input_activity.lower(), 1.2)
            daily_calories = bmr * multiplier

            protein_g = (daily_calories * 0.3) / 4
            fat_g = (daily_calories * 0.25) / 9
            carbs_g = (daily_calories * 0.45) / 4

            profile.age = input_age
            profile.gender = input_gender
            profile.height = input_height_ft
            profile.weight = input_weight_kg
            profile.activity = input_activity
            profile.diet = input_diet
            profile.bmi = round(bmi, 2)
            profile.bmi_category = bmi_category
            profile.bmr = round(bmr)
            profile.daily_calories = round(daily_calories)
            profile.protein_g = round(protein_g)
            profile.fat_g = round(fat_g)
            profile.carbs_g = round(carbs_g)
            profile.save()

            print("POST DATA:", request.POST)
            return JsonResponse({"success": True, "redirect_url": "/dashboard/"})

        except Profile.DoesNotExist:
            return JsonResponse({"success": False, "error": "Profile not found"}, status=404)
        except Exception as e:
            print("Error saving profile:", e)
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return render(request, "userinfo.html")


@login_required
def dashboard(request):
    user = request.user
    try:
        profile = Profile.objects.get(user=user)

        # Reset daily consumed values once per day
        if not hasattr(profile, "last_reset") or profile.last_reset != date.today():
            profile.consumed_calories = 0
            profile.consumed_protein = 0
            profile.consumed_fat = 0
            profile.consumed_carbs = 0
            profile.last_reset = date.today()
            profile.save()

        return render(request, "dashboard.html", {"profile": profile})

    except Profile.DoesNotExist:
        return redirect("userinfo")


# ----------------------------
# Nutrition Chatbot API
# ----------------------------

# This endpoint expects JSON POST with { "question": "..." } (CSRF via X-CSRFToken header)
@require_POST
@login_required
def nutrition_chatbot_api(request):
    try:
        data = json.loads(request.body)
        user_input = data.get("question", "").strip()

        if not user_input:
            return JsonResponse({"error": "No input provided."}, status=400)

        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
        You are a nutrition assistant. Based on the following meal description, 
        estimate the approximate nutritional values (in grams and kcal). 
        Respond ONLY in valid JSON (no explanation). Example format:
        {{
            "calories": 540,
            "protein": 22,
            "fat": 18,
            "carbs": 60
        }}

        Meal description: "{user_input}"
        """

        response = model.generate_content(prompt)
        text = response.text.strip()

        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
            text = text.strip()

        data = json.loads(text)
        return JsonResponse({"nutrients": data})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid AI response format."}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ----------------------------
# Medical Records + Upload + Delete
# ----------------------------

@login_required
@xframe_options_exempt  # allow this view to be embedded in your chatbot iframe
def medical_records(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    # --- Handle file upload ---
    if request.method == "POST" and request.FILES.get("report"):
        file = request.FILES["report"]
        report = MedicalReport.objects.create(profile=profile, file=file)

        # Extract text from the PDF right after upload
        pdf_path = report.file.path
        extracted_text = ""

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
        except Exception as e:
            return JsonResponse({"error": f"Failed to extract text: {str(e)}"}, status=500)

        # Cache extracted text for /read_report/
        request.session["last_pdf_text"] = extracted_text
        report.extracted_text = extracted_text.strip()
        report.save()

        return JsonResponse({
            "success": True,
            "filename": os.path.basename(report.file.name),
            "file_url": report.file.url,
            "uploaded_at": report.uploaded_at.strftime("%d %b %Y, %H:%M"),
        })

    # --- Handle health form submission (no files) ---
    elif request.method == "POST":
        def clean_int(value):
            return int(value) if str(value).isdigit() else None

        profile.medications = request.POST.get("medications") or None
        profile.habits = request.POST.get("habits") or None
        profile.sleep_hours = clean_int(request.POST.get("sleep_hours"))
        profile.diet_type = request.POST.get("diet_type") or None
        profile.meal_count = clean_int(request.POST.get("meal_count"))
        profile.food_avoid = request.POST.get("food_avoid") or None
        profile.family_history = request.POST.get("family_history") or None
        profile.surgeries = request.POST.get("surgeries") or None
        profile.save()

        return redirect("health_chatbot")

    # --- GET request: show uploaded records ---
    records = MedicalReport.objects.filter(profile=profile).order_by("-uploaded_at")
    return render(request, "dashboard_items/medical_records.html", {"records": records})


@login_required
def delete_medical_record(request, report_id):
    report = get_object_or_404(MedicalReport, id=report_id, profile__user=request.user)
    try:
        if os.path.exists(report.file.path):
            os.remove(report.file.path)
        report.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


# ----------------------------
# Health Chatbot
# ----------------------------

@login_required
def health_chatbot(request):
    return render(request, "dashboard_items/chatbot.html")


# Keep this POST-only and protected by login + CSRF (frontend must send X-CSRFToken)
@require_POST
@login_required
def health_chatbot_api(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message")
        if not user_message:
            return JsonResponse({"error": "Message is required"}, status=400)

        # --- Get profile and latest medical report ---
        profile = Profile.objects.get(user=request.user)
        latest_record = MedicalReport.objects.filter(profile=profile).last()

        # Fallback: try reading cached text if extraction hasn't saved yet
        if (not latest_record or not latest_record.extracted_text) and "last_pdf_text" in request.session:
            report_text = request.session["last_pdf_text"]
        else:
            report_text = latest_record.extracted_text.strip() if latest_record and latest_record.extracted_text else ""

        # Limit report text length
        if latest_record and latest_record.extracted_text:
            report_text = latest_record.extracted_text.strip()
            if len(report_text) > 2000:  # avoid flooding prompt
                report_text = report_text[:2000] + "\n\n[Report truncated for length]"

        # --- Build user health context ---
        user_context = f"""
        Gender: {profile.gender}
        BMI: {profile.bmi}
        BMI Category: {profile.bmi_category}
        BMR: {profile.bmr}
        Daily Calories: {profile.daily_calories}
        Protein (g): {profile.protein_g}
        Fat (g): {profile.fat_g}
        Carbs (g): {profile.carbs_g}
        Diet: {profile.diet}
        Activity: {profile.activity}
        Weight: {profile.weight}
        Medications: {profile.medications}
        Habits: {profile.habits}
        Sleep Hours: {profile.sleep_hours}
        Diet Type: {profile.diet_type}
        Meal Count: {profile.meal_count}
        Food Avoid: {profile.food_avoid}
        Family History: {profile.family_history}
        Surgeries: {profile.surgeries}
        """

        # --- Create prompt including both user profile and report ---
        prompt = f"""
        You are a trusted AI health assistant from India. 
        Your advice should always reflect Indian dietary habits, lifestyle, climate, and current seasonal conditions.

        Use both the user's medical profile and their uploaded medical report (if available)
        to give specific, practical, and friendly guidance.

        Patient Profile:
        {user_context}

        Medical Report Summary (if available):
        {report_text or 'No medical report uploaded yet.'}

        User Message:
        {user_message}

        Give advice that feels personal and clear.
        Avoid giving medical diagnoses or prescribing medications.
        Focus on suggestions that are realistic and relevant for someone living in India — 
        including local foods, weather patterns, and seasonal routines.
        """

        # --- Generate AI response ---
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        reply_text = response.text.strip()

        return JsonResponse({"reply": reply_text})

    except Profile.DoesNotExist:
        return JsonResponse({"error": "Profile not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request body."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ----------------------------
# Nutrition / Ask Gemini endpoint
# (keeps it POST-only and requires login)
# ----------------------------
@require_POST
@login_required
def ask_gemini(request):
    try:
        data = json.loads(request.body)
        # Accept either "question" or "message" keys for compatibility
        user_input = (data.get("question") or data.get("message") or "").strip()

        if not user_input:
            return JsonResponse({"error": "No input provided."}, status=400)

        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        You are a nutrition assistant. Based on the following meal description, 
        estimate the approximate nutritional values (in grams and kcal). 
        Respond ONLY in valid JSON (no explanation). Example format:
        {{
            "calories": 540,
            "protein": 22,
            "fat": 18,
            "carbs": 60
        }}

        Meal description: "{user_input}"
        """

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Remove Markdown code fences if Gemini adds them
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
            text = text.strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # Return both the raw text and an error code so frontend can show debug info
            return JsonResponse({"error": "Invalid AI response format.", "raw": text}, status=500)

        return JsonResponse({"nutrients": parsed})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request body."}, status=400)
    except Exception as e:
        print("Gemini error:", e)
        return JsonResponse({"error": str(e)}, status=500)


# ----------------------------
# Read Report (GET/POST)
# ----------------------------
@login_required
def read_report(request):
    """
    Handles both:
    - POST: Extracts text from the user's latest uploaded PDF and stores it in session.
    - GET: Displays the last extracted PDF text in a readable HTML format.
    """

    # ---------------------------
    # 1️⃣ GET — Show extracted text in browser
    # ---------------------------
    if request.method == 'GET':
        extracted_text = request.session.get('last_pdf_text')

        if extracted_text:
            return HttpResponse(f"""
                <html>
                <head>
                    <title>Extracted PDF Report</title>
                    <style>
                        body {{
                            font-family: 'Segoe UI', sans-serif;
                            background: #f5f6fa;
                            margin: 0;
                            padding: 2rem;
                        }}
                        h1 {{
                            color: #333;
                            text-align: center;
                        }}
                        pre {{
                            background: #fff;
                            padding: 1.5rem;
                            border-radius: 10px;
                            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                            white-space: pre-wrap;
                            word-wrap: break-word;
                            line-height: 1.6;
                        }}
                    </style>
                </head>
                <body>
                    <h1>Extracted PDF Report</h1>
                    <pre>{extracted_text}</pre>
                </body>
                </html>
            """)
        else:
            return JsonResponse({"error": "No PDF data available yet."})

    # ---------------------------
    # 2️⃣ POST — Extract text from latest uploaded PDF
    # ---------------------------
    elif request.method == 'POST':
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return JsonResponse({"error": "Profile not found."}, status=404)

        latest_record = MedicalReport.objects.filter(profile=profile).last()

        if not latest_record:
            return JsonResponse({"error": "No medical report found."}, status=404)

        if not latest_record.file or not os.path.exists(latest_record.file.path):
            return JsonResponse({"error": f"PDF file not found: {latest_record.file}"}, status=404)

        pdf_path = latest_record.file.path
        text = ""

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            return JsonResponse({"error": f"Failed to read PDF: {str(e)}"}, status=500)

        # Store in session for GET view
        request.session['last_pdf_text'] = text

        return JsonResponse({
            "success": True,
            "message": "PDF text extracted successfully.",
            "extracted_text_preview": text[:300] + "..." if len(text) > 300 else text
        })

    # ---------------------------
    # 3️⃣ Invalid Method
    # ---------------------------
    else:
        return JsonResponse({"error": "Invalid request method."}, status=405)
