from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime
from collections import defaultdict
from ..models import Question, QuestionRecord, QuestionBookmark
from django.core.paginator import Paginator


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
            "show_category_filter": True,
        },
    )


@login_required
def review_wrong_questions(request):
    category = request.GET.get("category")

    # ✅ 預載 question，避免 record.question 造成 N+1
    wrong_records = (
        QuestionRecord.objects.filter(user=request.user, is_correct=False)
        .select_related("question")
        .order_by("-answered_at")
    )
    if category:
        wrong_records = wrong_records.filter(question__category=category)

    # ✅ 把所有 question id 抓出來
    question_ids = [r.question_id for r in wrong_records]

    # ✅ 一次查出所有 bookmark 資料
    bookmarks = QuestionBookmark.objects.filter(
        user=request.user, question_id__in=question_ids
    )

    # ✅ 建立一個 dict { question_id: { is_favorited: ..., is_flagged: ... } }
    bookmark_status = {}
    for qid in question_ids:
        bookmark_status[qid] = {"is_favorited": False, "is_flagged": False}
    for b in bookmarks:
        if b.bookmark_type == "favorite":
            bookmark_status[b.question_id]["is_favorited"] = True
        elif b.bookmark_type == "flag":
            bookmark_status[b.question_id]["is_flagged"] = True

    categories = Question.objects.values_list("category", flat=True).distinct()

    paginator = Paginator(wrong_records, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "quiz/review_wrong_questions.html",
        {
            "records": page_obj,
            "categories": categories,
            "current_category": category,
            "bookmark_status": bookmark_status,
            "show_category_filter": True,
        },
    )
