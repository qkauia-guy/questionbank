from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from ..models import Question, QuestionBookmark


@login_required
@require_POST
def toggle_bookmark(request):
    question_id = request.POST.get("question_id")
    bookmark_type = request.POST.get("bookmark_type")  # 'favorite' 或 'flag'

    if bookmark_type not in ["favorite", "flag"]:
        return JsonResponse({"error": "❌ 無效的類型"}, status=400)

    question = get_object_or_404(Question, id=question_id)

    bookmark, created = QuestionBookmark.objects.get_or_create(
        user=request.user, question=question, bookmark_type=bookmark_type
    )

    if not created:
        bookmark.delete()
        return JsonResponse({"status": "removed"})
    else:
        return JsonResponse({"status": "added"})


@login_required
def bookmark_list(request):
    category = request.GET.get("category")

    # 收藏書籤
    favorite_bookmarks = QuestionBookmark.objects.filter(
        user=request.user, bookmark_type="favorite"
    ).select_related("question")

    # 爭議書籤
    flagged_bookmarks = QuestionBookmark.objects.filter(
        user=request.user, bookmark_type="flag"
    ).select_related("question")

    # ✅ 如果有傳入科目，進一步篩選 question 的 category
    if category:
        favorite_bookmarks = favorite_bookmarks.filter(question__category=category)
        flagged_bookmarks = flagged_bookmarks.filter(question__category=category)

    # ✅ 取出所有可用科目供篩選器使用
    categories = Question.objects.values_list("category", flat=True).distinct()

    return render(
        request,
        "quiz/bookmark_list.html",
        {
            "favorite_questions": [b.question for b in favorite_bookmarks],
            "flagged_questions": [b.question for b in flagged_bookmarks],
            "categories": categories,
            "current_category": category,
            "show_category_filter": True,
        },
    )
