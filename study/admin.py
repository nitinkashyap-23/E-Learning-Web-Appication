from django.contrib import admin
from django.contrib import messages
from .models import (
    Course, CourseDetail, Enrollment, Contact,
    Testimonial, CourseVideo, CourseProgress,
    QuizResult, Certificate, Assessment, AIQuestion, StudentAnswer
)


# ─────────────────────────────────────────────
# ASSESSMENT ADMIN — auto-generates questions
# ─────────────────────────────────────────────

class AssessmentAdmin(admin.ModelAdmin):
    """
    When admin saves an Assessment, Gemini AI automatically
    generates 50 MCQ questions for that course.
    """

    list_display = ['title', 'course', 'duration_minutes', 'created_at', 'question_count']
    readonly_fields = ['created_at']

    def question_count(self, obj):
        return AIQuestion.objects.filter(assessment=obj).count()
    question_count.short_description = "Questions Generated"

    def save_model(self, request, obj, form, change):
        # First save the Assessment object itself
        super().save_model(request, obj, form, change)

        # Now call Gemini to generate questions
        from .ai_generator import generate_questions_for_course

        self.message_user(
            request,
            f"⏳ Generating 25 AI questions for '{obj.course.title}'... please wait.",
            level=messages.INFO
        )

        success, message = generate_questions_for_course(
            course_title=obj.course.title,
            course_description=obj.course.description,
            assessment=obj,
            num_questions=25
        )

        if success:
            self.message_user(request, f"✅ {message}", level=messages.SUCCESS)
        else:
            self.message_user(request, f"❌ {message}", level=messages.ERROR)


class AIQuestionAdmin(admin.ModelAdmin):
    list_display = ['question', 'assessment', 'topic', 'difficulty', 'correct_answer']
    list_filter = ['assessment', 'difficulty', 'topic']
    search_fields = ['question', 'topic']

    # Add a custom action to regenerate questions for an assessment
    actions = ['regenerate_questions']

    def regenerate_questions(self, request, queryset):
        """Select questions and regenerate all for their assessment."""
        assessments_done = set()
        for question in queryset:
            assessment = question.assessment
            if assessment.id not in assessments_done:
                from .ai_generator import generate_questions_for_course
                success, message = generate_questions_for_course(
                    course_title=assessment.course.title,
                    course_description=assessment.course.description,
                    assessment=assessment,
                    num_questions=25
                )
                if success:
                    self.message_user(request, f"✅ {message}", level=messages.SUCCESS)
                else:
                    self.message_user(request, f"❌ {message}", level=messages.ERROR)
                assessments_done.add(assessment.id)

    regenerate_questions.short_description = "🔄 Regenerate AI questions for selected assessments"


# ─────────────────────────────────────────────
# REGISTER ALL MODELS
# ─────────────────────────────────────────────

admin.site.register(Course)
admin.site.register(CourseDetail)
admin.site.register(Enrollment)
admin.site.register(Contact)
admin.site.register(Testimonial)
admin.site.register(CourseVideo)
admin.site.register(CourseProgress)
admin.site.register(QuizResult)
admin.site.register(Certificate)
admin.site.register(Assessment, AssessmentAdmin)   # ← Custom admin with AI
admin.site.register(AIQuestion, AIQuestionAdmin)   # ← Custom admin with regenerate action
admin.site.register(StudentAnswer)