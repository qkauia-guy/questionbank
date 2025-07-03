# quiz/context_processors.py
def total_question_count(request):
    from .models import Question  # ✅ 改為函式內部 import，延遲載入

    return {"total_question_count": Question.objects.count()}
