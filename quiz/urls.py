from django.urls import path
from . import views
from .views import register
from . import views as quiz_views

urlpatterns = [
    # 題目功能
    path("questions/", views.question_list, name="question_list"),
    path("question/<int:pk>/", views.question_detail, name="question_detail"),
    path(
        "question/<int:pk>/save_ai_explanation/",
        views.save_ai_explanation,
        name="save_ai_explanation",
    ),
    path("ask-ai-followup/", views.ask_ai_followup, name="ask_ai_followup"),
    # 練習與考試
    path("", views.chapter_practice, name="chapter_practice"),
    path("practice/", views.chapter_practice, name="chapter_practice"),
    path("mock/", views.mock_exam, name="mock_exam"),
    path("exam/", views.exam_start, name="exam_start"),
    path("exam/<int:session_id>/", views.exam_question, name="exam_question"),
    path("exam/<int:session_id>/submit/", views.exam_submit, name="exam_submit"),
    path("exam/result/<int:session_id>/", views.exam_result, name="exam_result"),
    # 記錄功能
    path("review/", views.review_wrong_questions, name="review_wrong_questions"),
    path("history/", views.exam_history, name="exam_history"),
    # 書籤功能
    path("bookmarks/", views.bookmark_list, name="bookmark_list"),
    path("toggle_bookmark/", views.toggle_bookmark, name="toggle_bookmark"),
    path(
        "bookmark/note/<int:question_id>/<str:bookmark_type>/",
        views.update_bookmark_note,
        name="update_bookmark_note",
    ),
    # 動態選單
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
    # Ollama AI 控制
    path("toggle-ollama", views.toggle_ollama, name="toggle_ollama"),
    path("clear-ollama-notice", views.clear_ollama_notice, name="clear_ollama_notice"),
    path("set-ollama-model", views.set_ollama_model, name="set_ollama_model"),
    # 帳號註冊
    path("accounts/register/", views.register, name="register"),
]
