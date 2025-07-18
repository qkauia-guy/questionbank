from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from ..models import Question, QuestionRecord, ExamSession
from .base import shuffle_choice_values
from urllib.parse import urlencode


@login_required
def exam_start(request):
    categories = Question.objects.values_list("category", flat=True).distinct()
    category = request.GET.get("category") or request.session.get("exam_category")

    if not category:
        return render(
            request,
            "quiz/exam_start.html",
            {
                "categories": categories,
                "current_category": None,
                "total_available": 0,
                "question_options": [],
                "last_session": None,
            },
        )

    request.session["exam_category"] = category
    all_questions = Question.objects.filter(category=category).order_by("number_order")
    total_available = all_questions.count()

    question_options = [x for x in [5, 15, 30, 50] if total_available >= x]
    if total_available >= 1:
        question_options.append("all")

    if request.method == "POST":
        total = request.POST.get("total_questions")
        total = total_available if total == "all" else int(total)
        selected_questions = list(all_questions.order_by("?")[:total])

        session = ExamSession.objects.create(
            user=request.user,
            category=category,
            total_questions=total,
        )
        session.questions.set(selected_questions)

        return redirect("exam_question", session_id=session.id)

    last_session = (
        ExamSession.objects.filter(user=request.user, is_submitted=True)
        .order_by("-created_at")
        .first()
    )

    return render(
        request,
        "quiz/exam_start.html",
        {
            "categories": categories,
            "current_category": category,
            "total_available": total_available,
            "question_options": question_options,
            "last_session": last_session,
        },
    )


@login_required
def exam_question(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id, user=request.user)
    questions = session.questions.all().order_by("id")
    total = questions.count()
    used_time = int(request.POST.get("used_time", 0))

    answered_question_ids = QuestionRecord.objects.filter(
        exam_session=session
    ).values_list("question_id", flat=True)
    current_index = len(answered_question_ids)

    if current_index >= total:
        return redirect("exam_submit", session_id=session.id)

    current_question = questions[current_index]

    if request.method == "GET":
        if not current_question.is_fill_in:
            shuffled_choices, new_answer = shuffle_choice_values(current_question)
            request.session["exam_shuffled_choices"] = shuffled_choices
            request.session["exam_correct_answer"] = new_answer
            current_question.answer = new_answer
        else:
            request.session["exam_shuffled_choices"] = None
            request.session["exam_correct_answer"] = current_question.fill_answer

    if request.method == "POST":
        selected = request.POST.getlist("selected_answer")
        fill_answer = request.POST.get("fill_answer", "").strip()

        def clean_ans(ans):
            return ans.strip().upper().replace("`", "")

        correct_answer = sorted(
            [c for c in clean_ans(request.session.get("exam_correct_answer", ""))]
        )
        user_answer = sorted([clean_ans(s) for s in selected])

        if current_question.require_order:
            is_correct = user_answer == correct_answer
        else:
            is_correct = set(user_answer) == set(correct_answer)

        QuestionRecord.objects.create(
            user=request.user,
            question=current_question,
            selected_answer=",".join(user_answer),
            fill_answer=fill_answer,
            is_correct=is_correct,
            exam_session=session,
            source=f"模擬考（共 {session.total_questions} 題）",
            used_time=used_time,
            shuffled_choices=request.session.get("exam_shuffled_choices"),
            shuffled_correct_answer=request.session.get("exam_correct_answer"),
        )
        return redirect("exam_question", session_id=session.id)

    progress = round((current_index + 1) / total * 100)

    return render(
        request,
        "quiz/exam_question.html",
        {
            "question": current_question,
            "current_index": current_index,
            "total_question_count": total,
            "progress": progress,
            "session": session,
            "shuffled_choices": request.session.get("exam_shuffled_choices"),
            "correct_answer": request.session.get("exam_correct_answer"),
        },
    )


@login_required
def exam_submit(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id, user=request.user)
    total = session.total_questions
    records = session.records.all()
    correct = records.filter(is_correct=True).count()
    percentage = round(correct / total * 100, 2) if total else 0

    if not session.is_submitted:
        session.score = percentage
        session.finished_at = timezone.now()
        session.is_submitted = True
        session.save()

    return redirect("exam_result", session_id=session.id)


@login_required
def exam_result(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id, user=request.user)
    records = session.records.all()
    total = session.total_questions
    correct = records.filter(is_correct=True).count()
    percentage = round(correct / total * 100, 2) if total else 0

    past_sessions = ExamSession.objects.filter(
        user=request.user, is_submitted=True
    ).order_by("-created_at")

    for s in past_sessions:
        s.correct_count = s.records.filter(is_correct=True).count()
        s.wrong_count = s.total_questions - s.correct_count

    wrong_questions = records.filter(is_correct=False).select_related("question")

    return render(
        request,
        "quiz/exam_result.html",
        {
            "session": session,
            "records": records,
            "correct_count": correct,
            "total": total,
            "percentage": percentage,
            "past_sessions": past_sessions,
            "wrong_questions": wrong_questions,
        },
    )
