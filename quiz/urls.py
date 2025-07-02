from django.urls import path
from . import views

urlpatterns = [
    path("", views.question_list, name="question_list"),
    path("mock/", views.mock_exam, name="mock_exam"),
    path("get_numbers/", views.get_numbers_by_chapter, name="get_numbers_by_chapter"),
]
