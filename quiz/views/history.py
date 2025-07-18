from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime
from collections import defaultdict
from ..models import Question, QuestionRecord, QuestionBookmark


@login_required
def exam_history(request):
    category = request.GET.get("category")

    records = (
        QuestionRecord.objects.filter(user=request.user)
        .select_related("question")
        .order_by("-answered_at")
    )
    if category:
        records = records.filter(question__category=category)

    grouped = defaultdict(list)
    for r in records:
        date = localtime(r.answered_at).date()
        grouped[date].append(r)

    grouped_records = sorted(grouped.items(), reverse=True)
    categories = Question.objects.values_list("category", flat=True).distinct()

    return render(
        request,
        "quiz/exam_history.html",
        {
            "grouped_records": grouped_records,
            "current_category": category,
            "categories": categories,
        },
    )


@login_required
def review_wrong_questions(request):
    category = request.GET.get("category")

    wrong_records = (
        QuestionRecord.objects.filter(user=request.user, is_correct=False)
        .select_related("question")
        .order_by("-answered_at")
    )
    if category:
        wrong_records = wrong_records.filter(question__category=category)

    questions = [r.question for r in wrong_records if r.question]

    categories = Question.objects.values_list("category", flat=True).distinct()

    bookmark_status = {}
    for q in questions:
        bookmark_status[q.id] = {
            "is_favorited": QuestionBookmark.objects.filter(
                user=request.user, question=q, bookmark_type="favorite"
            ).exists(),
            "is_flagged": QuestionBookmark.objects.filter(
                user=request.user, question=q, bookmark_type="flag"
            ).exists(),
        }

    return render(
        request,
        "quiz/review_wrong_questions.html",
        {
            "questions": questions,
            "records": wrong_records,
            "categories": categories,
            "current_category": category,
            "bookmark_status": bookmark_status,
        },
    )
