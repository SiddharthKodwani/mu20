from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('signup/', views.signup, name='signup'),
    path('userinfo/', views.userinfo, name='userinfo'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('medical_records/', views.medical_records, name='medical_records'),
    path('medical_records/delete/<int:report_id>/', views.delete_medical_record, name='delete_medical_record'),
    path("chatbot/", views.health_chatbot, name="health_chatbot"),
    
    path("ask_gemini/", views.ask_gemini, name="ask_gemini"),
    path('api/health/', views.health_chatbot_api, name='health_chatbot_api'),
    path('api/read_report/', views.read_report, name='read_report'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

