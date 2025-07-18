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
    favorite_bookmarks = QuestionBookmark.objects.filter(
        user=request.user, bookmark_type="favorite"
    ).select_related("question")

    flagged_bookmarks = QuestionBookmark.objects.filter(
        user=request.user, bookmark_type="flag"
    ).select_related("question")

    return render(
        request,
        "quiz/bookmark_list.html",
        {
            "favorite_questions": [b.question for b in favorite_bookmarks],
            "flagged_questions": [b.question for b in flagged_bookmarks],
        },
    )
