"""
URL configuration for project24 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL configuration for project24 project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from Watch.views import *

urlpatterns = [

    path('admin/', admin.site.urls),

    # HOME PAGE
    path('', home),

    # AUTHENTICATION
    path('login/', login_view),
    path('register/', register),

    # DASHBOARD
    path('dashboard/', dashboard),

    # PERFORMANCE PAGE
    path('performance/', performance),

    # REPORTS PAGE
    path('reports/', reports),

    # PERFORMANCE RESTART
    path('performance/restart/', restart_performance),

    # MAIN INTERVIEW PAGE
    path('interview/', interview),

    # LEARN MORE PAGE
    path('learnmore/', learnmore),

    # FEATURES PAGE
    path('features/', features),

    # ABOUT PAGE
    path('about/', about),

    # CONTACT PAGE
    path('contact/', contact),

    # HR INTERVIEW
    path(
        'interview/hr/',
        hr_interview
    ),

    path(
        'interview/hr/<int:index>/',
        hr_interview
    ),

    # TECHNICAL INTERVIEW
    path(
        'interview/technical/',
        technical_interview
    ),

    path(
        'interview/technical/<int:index>/',
        technical_interview
    ),

    # APTITUDE INTERVIEW
    path(
        'interview/aptitude/',
        aptitude_interview
    ),

    path(
        'interview/aptitude/<int:index>/',
        aptitude_interview
    ),

    # RESUME UPLOAD
    path('upload-resume/', upload_resume),
    path('delete-resume/', delete_own_resume),

    # AJAX SAVE ATTEMPT (from SPA interview)
    path('interview/save_attempt/', save_attempt),

    # CUSTOM ADMIN PORTAL
    path('admin-dashboard/login/', admin_login),
    path('admin-dashboard/', admin_dashboard),
    path('admin-dashboard/hire/<int:resume_id>/', admin_hire_candidate),
    path('admin-dashboard/delete-resume/<int:resume_id>/', admin_delete_resume),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)