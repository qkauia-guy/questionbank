from django.contrib import admin
from django.utils.html import format_html
from .models import Question


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
