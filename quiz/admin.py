from django.contrib import admin
from .models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("chapter", "number", "question_text", "answer")
    search_fields = ("chapter", "number", "question_text")
