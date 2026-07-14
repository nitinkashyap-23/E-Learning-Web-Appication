from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):

    title = models.CharField(max_length=200)

    description = models.TextField()

    image = models.ImageField(upload_to='courses/')

    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title

class CourseDetail(models.Model):

    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE
    )

    duration = models.CharField(max_length=100)

    level = models.CharField(max_length=100)

    students = models.CharField(max_length=100)

    learn_1 = models.CharField(max_length=300)

    learn_2 = models.CharField(max_length=300)

    learn_3 = models.CharField(max_length=300)

    learn_4 = models.CharField(max_length=300)

    learn_5 = models.CharField(max_length=300)

    learn_6 = models.CharField(max_length=300)

    def __str__(self):
        return self.course.title
    
#Enrollment model

class Enrollment(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    enrolled_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.user.username} - {self.course.title}"

# contact model

class Contact(models.Model):

    name = models.CharField(max_length=100)

    email = models.EmailField()

    subject = models.CharField(max_length=200)

    message = models.TextField()

    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return self.name

# testimonial model
class Testimonial(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    profession = models.CharField(
        max_length=100
    )

    message = models.TextField()

    rating = models.IntegerField(default=5)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username
    
# video model 

class CourseVideo(models.Model):

    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE
    )

    video_file = models.FileField(
        upload_to='course_videos/'
    )

    def __str__(self):
        return self.course.title


class CourseProgress(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    watched_seconds = models.IntegerField(
        default=0
    )

    completed = models.BooleanField(
        default=False
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return f"{self.user.username} - {self.course.title}"
    

class QuizResult(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    score = models.IntegerField(default=0)

    passed = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.user.username} - {self.course.title}"


class Certificate(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    issued_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.user.username} - {self.course.title}"

class Assessment(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    title = models.CharField(
        max_length=200
    )

    duration_minutes = models.IntegerField(
        default=90
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.title


class AIQuestion(models.Model):

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE
    )

    question = models.TextField()

    option1 = models.CharField(
        max_length=300
    )

    option2 = models.CharField(
        max_length=300
    )

    option3 = models.CharField(
        max_length=300
    )

    option4 = models.CharField(
        max_length=300
    )

    correct_answer = models.CharField(
        max_length=300
    )
    topic = models.CharField(
    max_length=200,
    default="General"
    )

    difficulty = models.CharField(
    max_length=50,
    default="Easy"
    )

    def __str__(self):

        return self.question


class StudentAnswer(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    question = models.ForeignKey(
        AIQuestion,
        on_delete=models.CASCADE
    )

    selected_answer = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    def __str__(self):

        return self.user.username

