from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Question,
    QuestionRecord,
    UserProfile,
    ExamSession,
    QuestionBookmark,
)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("chapter", "number", "question_text", "answer", "image_tag")
    search_fields = ("chapter", "number", "question_text")

    def image_tag(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px;" />', obj.image.url
            )
        return "—"

    image_tag.short_description = "附圖預覽"


@admin.register(QuestionRecord)
class QuestionRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "is_correct", "answered_at", "source")
    search_fields = ("user__username", "question__question_text")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    search_fields = ("user__username",)


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "created_at", "is_submitted", "score")
    search_fields = ("user__username", "category")


@admin.register(QuestionBookmark)
class QuestionBookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "bookmark_type", "created_at", "note")
    search_fields = ("user__username", "question__question_text")
