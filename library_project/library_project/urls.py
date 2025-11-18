"""
This is the content for library_project/urls.py
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Login/Logout views
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='library/login.html'
    ), name='login'),
    
    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='login'
    ), name='logout'),
    
    # Include the library app's URLs
    path('', include('library.urls')),
]