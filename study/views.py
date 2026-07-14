from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Course, CourseDetail, Enrollment, Contact, Testimonial, CourseVideo, CourseProgress, QuizResult, Certificate, Assessment, AIQuestion, StudentAnswer
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from datetime import date
from django.core.mail import send_mail
from django.conf import settings
import json



def index(request):
    testimonials = Testimonial.objects.order_by('-created_at')[:3]
    return render(request, 'index.html', {'testimonials': testimonials})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('courses')

    if request.method == "POST":
        if 'login' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('courses')
            else:
                messages.error(request, "Invalid username or password")

        elif 'register' in request.POST:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists")
                return redirect('login')
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            messages.success(request, "Account created successfully")
            return redirect('login')

    return render(request, "login.html")


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def courses(request):
    all_courses = Course.objects.all()
    return render(request, 'courses.html', {'courses': all_courses})


@login_required(login_url='login')
def course_detail(request, slug):

    course = get_object_or_404(
        Course,
        slug=slug
    )

    detail = get_object_or_404(
        CourseDetail,
        course=course
    )

    enrolled = Enrollment.objects.filter(
        user=request.user,
        course=course
    ).exists()
    
    video_exists = CourseVideo.objects.filter(
        course=course
    ).exists()

    return render(
        request,
        'course_detail.html',
        {
            'course': course,
            'detail': detail,
            'enrolled': enrolled,
            'video_exists':video_exists,
        }
    )


@login_required(login_url='login')
def learn_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    # Check whether the user has enrolled
    is_enrolled = Enrollment.objects.filter(
        user=request.user,
        course=course
        ).exists()
    
    if not is_enrolled:
        return redirect('course_detail', slug=course.slug)

# At this point, the UI has already checked that a video exists.
# This is just a safety check in case someone manually enters the URL.
    video = get_object_or_404(
        CourseVideo,
        course=course
        )

    progress, _ = CourseProgress.objects.get_or_create(
        user=request.user,
        course=course
    )

    assessment = Assessment.objects.filter(course=course).first()

    return render(request, 'learn_course.html', {
        'course': course,
        'video': video,
        'progress': progress,
        'assessment': assessment,
    })


@login_required(login_url='login')
def save_progress(request, slug):
    if request.method == "POST":
        course = get_object_or_404(Course, slug=slug)
        watched_seconds = request.POST.get('watched_seconds', 0)
        completed = request.POST.get('completed')

        progress, created = CourseProgress.objects.get_or_create(
            user=request.user,
            course=course
        )

        # Only update if new time is greater than saved time
        # This prevents accidental overwrite if two tabs open
        if int(watched_seconds) > progress.watched_seconds:
            progress.watched_seconds = int(watched_seconds)

        if completed == "true":
            progress.completed = True

        progress.save()
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'failed'})


@login_required(login_url='login')
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    already_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    if not already_enrolled:
        Enrollment.objects.create(user=request.user, course=course)
    return redirect('courses')


# =============================================
# DASHBOARD — with progress data synced
# =============================================
@login_required(login_url='login')
def dashboard(request):

    enrolled_courses = Enrollment.objects.filter(user=request.user)
    total_courses = enrolled_courses.count()
    testimonial = Testimonial.objects.filter(user=request.user).first()

    # Build course list with progress attached
    # For each enrolled course, fetch its CourseProgress
    courses_with_progress = []
    completed_count = 0
    certificates_count = Certificate.objects.filter(
        user=request.user
        ).count()

    for enrollment in enrolled_courses:

        # get_or_create so even new enrollments show 0% progress
        progress, _ = CourseProgress.objects.get_or_create(
            user=request.user,
            course=enrollment.course
        )

        # Calculate percentage — need video duration
        # We store watched_seconds, get total from CourseVideo if exists
        try:
            course_video = CourseVideo.objects.get(course=enrollment.course)
            # Use ffprobe or just a large estimate — for now use watched vs a fixed max
            # We'll calculate % as min(100, watched/total*100) if duration stored
            # Since duration not in model yet, show time-based badge instead
            total_seconds = course_video.duration_seconds if hasattr(course_video, 'duration_seconds') else None
        except CourseVideo.DoesNotExist:
            total_seconds = None

        if total_seconds and total_seconds > 0:
            percent = min(100, int((progress.watched_seconds / total_seconds) * 100))
        elif progress.completed:
            percent = 100
        elif progress.watched_seconds > 0:
            # No duration stored — estimate based on watched time
            # Show at least some progress so dashboard reflects activity
            percent = min(99, int(progress.watched_seconds / 60))
        else:
            percent = 0

        if progress.completed:
            completed_count += 1

        courses_with_progress.append({
            'enrollment': enrollment,
            'course': enrollment.course,
            'progress': progress,
            'percent': percent,
        })

    # Overall progress percentage across all courses
    overall_percent = int((completed_count / total_courses) * 100) if total_courses > 0 else 0

    if request.method == "POST":
        profession = request.POST.get("profession")
        message = request.POST.get("message")
        rating = request.POST.get("rating")

        if testimonial:
            testimonial.profession = profession
            testimonial.message = message
            testimonial.rating = rating
            testimonial.save()
        else:
            Testimonial.objects.create(
                user=request.user,
                profession=profession,
                message=message,
                rating=rating
            )
        return redirect('dashboard')

    return render(request, 'dashboard.html', {
        'courses_with_progress': courses_with_progress,
        'total_courses': total_courses,
        'completed_count': completed_count,
        'overall_percent': overall_percent,
        'testimonial': testimonial,
        'certificates_count': certificates_count,
    })


def about(request):
    return render(request, 'about.html')




def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        Contact.objects.create(name=name, email=email, subject=subject, message=message)

        full_message = f"""
New message from your website:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}
"""
        send_mail(
            subject=f"Website Contact: {subject}",
            message=full_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
        )
        return render(request, "contact.html", {"success": True})

    return render(request, "contact.html")


def search_courses(request):
    query = request.GET.get('query')
    courses = Course.objects.filter(title__icontains=query)
    data = [{'title': course.title, 'slug': course.slug} for course in courses]
    return JsonResponse(data, safe=False)



    
@login_required(login_url='login')
def download_certificate(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id
    )

    certificate_exists = Certificate.objects.filter(
        user=request.user,
        course=course
    ).exists()

    if not certificate_exists:

        return HttpResponse(
            "You are not eligible for certificate."
        )

    result = QuizResult.objects.filter(
        user=request.user,
        course=course,
        passed=True
    ).first()

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="{course.title}_certificate.pdf"'
    )

    pdf = canvas.Canvas(response)

    pdf.setPageSize((900, 600))

    # TITLE

    pdf.setFont("Helvetica-Bold", 30)

    pdf.drawCentredString(
        450,
        520,
        "CERTIFICATE OF COMPLETION"
    )

    pdf.line(180, 500, 720, 500)

    # USER

    pdf.setFont("Helvetica", 22)

    pdf.drawCentredString(
        450,
        430,
        "This certificate is proudly presented to"
    )

    pdf.setFont("Helvetica-Bold", 32)

    pdf.drawCentredString(
        450,
        370,
        request.user.username
    )

    # COURSE

    pdf.setFont("Helvetica", 22)

    pdf.drawCentredString(
        450,
        300,
        "For successfully completing the course"
    )

    pdf.setFont("Helvetica-Bold", 26)

    pdf.drawCentredString(
        450,
        250,
        course.title
    )

    # SCORE

    if result:

        pdf.setFont("Helvetica", 18)

        pdf.drawCentredString(
            450,
            200,
            f"Score: {result.score}%"
        )

    # DATE

    pdf.setFont("Helvetica", 18)

    pdf.drawString(
        80,
        120,
        f"Date: {date.today()}"
    )

    # SIGNATURE

    pdf.drawString(
        650,
        120,
        "E-Learning"
    )

    pdf.showPage()

    pdf.save()

    return response

@login_required(login_url='login')
def assessment_page(request, id):

    assessment = get_object_or_404(
        Assessment,
        id=id
    )

    questions = AIQuestion.objects.filter(
        assessment=assessment
    )

    return render(
        request,
        'assessment.html',
        {
            'assessment': assessment,
            'questions': questions
        }
    )

@login_required(login_url='login')
def submit_assessment(request, id):

    assessment = get_object_or_404(
        Assessment,
        id=id
    )

    questions = AIQuestion.objects.filter(
        assessment=assessment
    ).order_by('?')[:50]

    correct = 0

    weak_topics = []

    strong_topics = []

    total = questions.count()

    for question in questions:

        selected = request.POST.get(
            f"question{question.id}"
        )

        if selected == question.correct_answer:

            correct += 1

            strong_topics.append(
                question.topic
            )

        else:

            weak_topics.append(
                question.topic
            )

    score = int((correct / total) * 100)

    passed = score >= 40

    # REMOVE DUPLICATES

    strong_topics = list(
        set(strong_topics)
    )

    weak_topics = list(
        set(weak_topics)
    )

    QuizResult.objects.create(
        user=request.user,
        course=assessment.course,
        score=score,
        passed=passed
    )

    # CREATE CERTIFICATE IF PASSED

    if passed:

        Certificate.objects.get_or_create(
            user=request.user,
            course=assessment.course
        )

    return render(
        request,
        'assessment_result.html',
        {
            'score': score,
            'passed': passed,
            'assessment': assessment,
            'strong_topics': strong_topics,
            'weak_topics': weak_topics,
        }
    )
