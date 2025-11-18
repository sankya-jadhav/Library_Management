from django.urls import path
from . import views

urlpatterns = [
    # Student dashboard, shows all books
    path('', views.book_list, name='book_list'),
    
    # Book detail page
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    
    # POST endpoint to request a book
    path('book/<int:pk>/request/', views.request_book, name='request_book'),
    
    # Student profile page
    path('profile/', views.student_profile, name='student_profile'),

    # Student Registration
    path('register/', views.register, name='register'),

    # Staff pages (avoid using the top-level 'admin/' prefix which is reserved for Django admin)
    path('staff/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/pending-requests/', views.pending_requests, name='admin_pending_requests'),
    path('staff/pending-requests/<int:pk>/approve/', views.approve_request, name='approve_request'),
    path('staff/pending-requests/<int:pk>/reject/', views.reject_request, name='reject_request'),
    
    # Admin Login and Registration
    path('staff/login/', views.admin_login, name='admin_login'),
    path('staff/register/', views.admin_register, name='admin_register'),
]