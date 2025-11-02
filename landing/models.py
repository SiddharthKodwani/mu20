from django.db import models
from django.contrib.auth.models import User
from datetime import date


class Profile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    ACTIVITY_CHOICES = [
        ('light', 'Not Active'),
        ('lightly active', 'Lightly Active'),
        ('moderately active', 'Moderately Active'),
        ('active', 'Active'),
        ('very active', 'Very Active'),
    ]

    DIET_CHOICES = [
        ('Vegetarian', 'Vegetarian'),
        ('Non-Vegetarian', 'Non-Vegetarian'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    # User info fields
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    height = models.FloatField(help_text="Height in feet", null=True, blank=True)
    weight = models.FloatField(help_text="Weight in kg", null=True, blank=True)
    activity = models.CharField(max_length=30, choices=ACTIVITY_CHOICES, null=True, blank=True)
    diet = models.CharField(max_length=20, choices=DIET_CHOICES, null=True, blank=True)

    # Calculated fields
    bmi = models.FloatField(null=True, blank=True)
    bmi_category = models.CharField(max_length=50, null=True, blank=True)
    bmr = models.FloatField(null=True, blank=True)
    daily_calories = models.FloatField(null=True, blank=True)
    protein_g = models.FloatField(null=True, blank=True)
    fat_g = models.FloatField(null=True, blank=True)
    carbs_g = models.FloatField(null=True, blank=True)

    consumed_calories = models.FloatField(default=0)
    consumed_protein = models.FloatField(default=0)
    consumed_fat = models.FloatField(default=0)
    consumed_carbs = models.FloatField(default=0)
    last_reset = models.DateField(default=date.today)

    # --- Health questionnaire fields ---
    medications = models.CharField(max_length=255, null=True, blank=True)
    habits = models.CharField(max_length=255, null=True, blank=True)
    sleep_hours = models.PositiveIntegerField(null=True, blank=True)
    diet_type = models.CharField(max_length=255, null=True, blank=True)
    meal_count = models.PositiveIntegerField(null=True, blank=True)
    food_avoid = models.CharField(max_length=255, null=True, blank=True)
    family_history = models.CharField(max_length=255, null=True, blank=True)
    surgeries = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.full_name or self.user.username


class MedicalReport(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="medical_reports", null=True, blank=True)
    file = models.FileField(upload_to="medical_reports/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.profile.full_name} - {self.file.name.split('/')[-1]}"
