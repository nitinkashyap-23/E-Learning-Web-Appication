from django.urls import path
from . import views

urlpatterns = [

    path('', views.index, name='index'),

    # AUTH
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # DASHBOARD
    path('dashboard/', views.dashboard, name='dashboard'),

    # COURSES
    path('courses/', views.courses, name='courses'),

    path(
        'course/<slug:slug>/',
        views.course_detail,
        name='course_detail'
    ),

    path(
        'enroll/<slug:slug>/',
        views.enroll_course,
        name='enroll_course'
    ),

    # LEARNING
    path(
        'learn/<slug:slug>/',
        views.learn_course,
        name='learn_course'
    ),

    path(
        'save-progress/<slug:slug>/',
        views.save_progress,
        name='save_progress'
    ),

    # ASSESSMENT
    path(
        'assessment/<int:id>/',
        views.assessment_page,
        name='assessment_page'
    ),

    path(
        'submit-assessment/<int:id>/',
        views.submit_assessment,
        name='submit_assessment'
    ),

    # CERTIFICATE
    path(
        'download-certificate/<int:course_id>/',
        views.download_certificate,
        name='download_certificate'
    ),

    # PUBLIC
    path('about/', views.about, name='about'),

    path('contact/', views.contact, name='contact'),

    # SEARCH
    path(
        'search-courses/',
        views.search_courses,
        name='search_courses'
    ),
    

]