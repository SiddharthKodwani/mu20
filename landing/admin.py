from django.contrib import admin
from django.utils.html import format_html
from .models import Profile, MedicalReport


# Inline section for medical reports
class MedicalReportInline(admin.TabularInline):
    model = MedicalReport
    extra = 0
    readonly_fields = ('file_link', 'uploaded_at')
    fields = ('file', 'file_link', 'uploaded_at')

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.file.url)
        return "No file"
    file_link.short_description = "Report File"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'user', 'age', 'gender', 'activity', 'diet',
        'bmi', 'bmi_category', 'daily_calories',
        'consumed_calories', 'last_reset', 'created_at'
    )
    search_fields = ('full_name', 'user__username', 'user__email')
    list_filter = ('gender', 'diet', 'activity', 'bmi_category')

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'full_name', 'created_at')
        }),
        ('User Information', {
            'fields': ('age', 'gender', 'height', 'weight', 'activity', 'diet')
        }),
        ('Calculated Data', {
            'fields': (
                'bmi', 'bmi_category', 'bmr', 'daily_calories',
                'protein_g', 'fat_g', 'carbs_g'
            )
        }),
        ('Progress Tracker', {
            'fields': (
                'consumed_calories', 'consumed_protein',
                'consumed_fat', 'consumed_carbs', 'last_reset'
            )
        }),
        ('Health Questionnaire', {
            'fields': (
                'medications', 'habits', 'sleep_hours', 'diet_type',
                'meal_count', 'food_avoid', 'family_history', 'surgeries'
            )
        }),
    )

    readonly_fields = (
        'created_at', 'bmi', 'bmi_category', 'bmr',
        'daily_calories', 'protein_g', 'fat_g', 'carbs_g'
    )

    inlines = [MedicalReportInline]


@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('profile', 'filename', 'file_link', 'uploaded_at')
    readonly_fields = ('file_link', 'filename', 'uploaded_at')
    fields = ('profile', 'file', 'file_link', 'uploaded_at')

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.file.url)
        return "No file"
    file_link.short_description = "Report File"

    def filename(self, obj):
        return obj.file.name.split('/')[-1]
    filename.short_description = "Filename"
