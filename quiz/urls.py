from django.urls import path
from . import views
from .views import register
from . import views as quiz_views

urlpatterns = [
    path("", views.chapter_practice, name="chapter_practice"),
    path("mock/", views.mock_exam, name="mock_exam"),
    path("get_numbers/", views.get_numbers_by_chapter, name="get_numbers_by_chapter"),
    path("review/", views.review_wrong_questions, name="review_wrong_questions"),
    path("history/", views.exam_history, name="exam_history"),
    path("practice/", views.chapter_practice, name="chapter_practice"),
    path("question/<int:pk>/", views.question_detail, name="question_detail"),
    path(
        "get_chapters_by_category/",
        views.get_chapters_by_category,
        name="get_chapters_by_category",
    ),
    path(
        "get_numbers_by_chapter/",
        views.get_numbers_by_chapter,
        name="get_numbers_by_chapter",
    ),
    path("toggle-ollama", views.toggle_ollama, name="toggle_ollama"),
    path("clear-ollama-notice", views.clear_ollama_notice, name="clear_ollama_notice"),
    path("set-ollama-model", views.set_ollama_model, name="set_ollama_model"),
    path("accounts/register/", quiz_views.register, name="register"),
    path(
        "question/<int:pk>/save_ai_explanation/",
        views.save_ai_explanation,
        name="save_ai_explanation",
    ),
    path("ask-ai-followup/", views.ask_ai_followup, name="ask_ai_followup"),
    path("exam/", views.exam_start, name="exam_start"),
    path("exam/<int:session_id>/", views.exam_question, name="exam_question"),
    path("exam/<int:session_id>/submit/", views.exam_submit, name="exam_submit"),
    path("exam/result/<int:session_id>/", views.exam_result, name="exam_result"),
    path("bookmarks/", views.bookmark_list, name="bookmark_list"),
    path("toggle_bookmark/", views.toggle_bookmark, name="toggle_bookmark"),
]
