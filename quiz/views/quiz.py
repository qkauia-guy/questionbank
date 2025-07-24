from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from urllib.parse import urlencode
from ..models import Question, QuestionRecord, QuestionBookmark
from .base import (
    check_answer,
    shuffle_choice_values,
    convert_to_traditional,
    sort_key,
    generate_options_text,
)
from .ai import get_ai_feedback_ollama
import random
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import Question


@login_required
def chapter_practice(request):
    category = request.GET.get("category")
    chapter = request.GET.get("chapter")
    number = request.GET.get("number")
    category = None if category == "None" else category
    chapter = None if chapter == "None" else chapter
    number = None if number == "None" else number

    questions = Question.objects.order_by("chapter", "number_order")
    if category:
        questions = questions.filter(category=category)
    if chapter:
        questions = questions.filter(chapter=chapter)
    if number:
        questions = questions.filter(number=number)

    total = questions.count()
    category_total = (
        Question.objects.filter(category=category).count() if category else 0
    )

    if total == 0:
        return render(
            request,
            "quiz/chapter_practice.html",
            {
                "no_question": True,
                "category": category,
                "chapter": chapter,
                "number": number,
                "category_total": category_total,
            },
        )

    current_index = request.session.get("current_index", 0)
    if request.GET.get("next") == "1":
        request.session["current_index"] = current_index + 1
        return redirect(
            f"{reverse('chapter_practice')}?{urlencode({'category': category or '', 'chapter': chapter or '', 'number': number or ''})}"
        )

    if current_index >= total:
        current_index = 0

    selected_answer, fill_input, result, correct_answer, ai_explanation = (
        [],
        "",
        None,
        None,
        None,
    )
    question = questions[current_index]
    query_params = urlencode(
        {"category": category or "", "chapter": chapter or "", "number": number or ""}
    )
    redirect_url = f"{reverse('chapter_practice')}?{query_params}"

    if request.method == "POST":
        if "restart" in request.POST:
            request.session["current_index"] = 0
            return redirect(redirect_url)
        elif "skip" in request.POST or "next" in request.POST:
            request.session["current_index"] = current_index + 1
            return redirect(redirect_url)
        elif "prev" in request.POST:
            request.session["current_index"] = max(current_index - 1, 0)
            return redirect(redirect_url)

        selected_answer = [a.upper() for a in request.POST.getlist("selected_answer")]
        fill_input = request.POST.get("fill_answer", "").strip()
        used_time = request.POST.get("used_time", 0)
        result = check_answer(question, selected_answer, fill_input)
        correct_answer = question.answer

        if not result:
            ollama_enabled = request.session.get("ollama_enabled", True)
            model_name = request.session.get("ollama_model", "qwen2.5-coder:7b")
            if ollama_enabled and not question.image:
                options_text = generate_options_text(question)
                ai_explanation = get_ai_feedback_ollama(
                    question_text=question.question_text,
                    user_ans=(
                        fill_input if question.is_fill_in else "".join(selected_answer)
                    ),
                    correct_ans=correct_answer,
                    question=question,
                    options=options_text,
                    model_name=model_name,
                )
                ai_explanation = convert_to_traditional(ai_explanation)
            else:
                ai_explanation = convert_to_traditional(question.explanation)

        QuestionRecord.objects.create(
            user=request.user,
            question=question,
            is_correct=result,
            selected_answer=(
                fill_input if question.is_fill_in else "".join(selected_answer)
            ),
            used_time=used_time,
            ai_explanation=ai_explanation if not result else None,
            source="mock",
        )

    chapter_list = (
        Question.objects.filter(category=category)
        .values_list("chapter", flat=True)
        .distinct()
    )
    number_list = (
        Question.objects.filter(category=category, chapter=chapter)
        .values_list("number", flat=True)
        .distinct()
        if chapter
        else []
    )
    categories = Question.objects.values_list("category", flat=True).distinct()

    correct_answer_list = list(correct_answer) if correct_answer else []
    correct_choices_list = [
        getattr(question, f"choice_{l.lower()}")
        for l in correct_answer_list
        if getattr(question, f"choice_{l.lower()}", "").strip().upper() != "X"
    ]
    is_favorited = QuestionBookmark.objects.filter(
        user=request.user, question=question, bookmark_type="favorite"
    ).exists()
    is_flagged = QuestionBookmark.objects.filter(
        user=request.user, question=question, bookmark_type="flag"
    ).exists()

    return render(
        request,
        "quiz/chapter_practice.html",
        {
            "question": question,
            "selected_answer": selected_answer,
            "fill_input": fill_input,
            "result": result,
            "correct_answer": correct_answer,
            "ai_explanation": ai_explanation,
            "total_question_count": total,
            "current_index": current_index,
            "chapter_list": chapter_list,
            "number_list": sorted(number_list, key=sort_key),
            "categories": categories,
            "current_category": category,
            "category": category,
            "chapter": chapter,
            "number": number,
            "category_total": category_total,
            "ollama_model": request.session.get("ollama_model", "qwen2.5-coder:7b"),
            "options": generate_options_text(question),
            "correct_answer_list": correct_answer_list,
            "correct_choices_list": correct_choices_list,
            "is_favorited": is_favorited,
            "is_flagged": is_flagged,
            "show_category_filter": True,
            "keyword_filter": True,
        },
    )


@login_required
def mock_exam(request):
    category = request.GET.get("category")
    chapter = request.GET.get("chapter")
    number = request.GET.get("number")

    if category == "None":
        category = None
    if chapter == "None":
        chapter = None
    if number == "None":
        number = None

    model_name = request.session.get("ollama_model", "qwen2.5-coder:7b")
    ollama_enabled = request.session.get("ollama_enabled", True)

    result = None
    correct_answer = None
    explanation = None
    selected_answer = []
    fill_input = ""
    ai_explanation = None
    used_time = int(request.POST.get("used_time", 0))

    questions = Question.objects.order_by("chapter", "number_order")
    if category:
        questions = questions.filter(category=category)
    if chapter:
        questions = questions.filter(chapter=chapter)
    if number:
        questions = questions.filter(number=number)

    total = questions.count()
    category_total = (
        Question.objects.filter(category=category).count() if category else 0
    )

    if total == 0:
        return render(
            request,
            "quiz/chapter_practice.html",
            {
                "no_question": True,
                "category": category,
                "chapter": chapter,
                "number": number,
                "category_total": category_total,
            },
        )

    query_params = urlencode(
        {
            "category": category or "",
            "chapter": chapter or "",
            "number": number or "",
        }
    )
    redirect_url = f"{reverse('mock_exam')}?{query_params}"

    if request.method == "POST" and ("next" in request.POST or "skip" in request.POST):
        return redirect(redirect_url)

    if request.method == "POST":
        question_id = request.POST.get("question_id")
        question = get_object_or_404(Question, id=question_id)

        shuffled_choices = request.session.get("shuffled_choices")
        correct_answer = request.session.get("correct_answer")

        if not question.is_fill_in and correct_answer:
            question.answer = correct_answer

        selected_answer = request.POST.getlist("selected_answer")
        fill_input = request.POST.get("fill_answer", "").strip()
        used_time = int(request.POST.get("used_time", 0))

        explanation = question.explanation
        result = check_answer(question, selected_answer, fill_input)

        if not result:
            if ollama_enabled and not question.image:
                options_text = ""
                for letter in "ABCDEFGH":
                    choice = getattr(question, f"choice_{letter.lower()}", None)
                    if choice and choice.strip().upper() != "X":
                        options_text += f"{letter}. {choice}\n"

                ai_explanation = get_ai_feedback_ollama(
                    question_text=question.question_text,
                    user_ans=(
                        fill_input if question.is_fill_in else "".join(selected_answer)
                    ),
                    correct_ans=correct_answer,
                    question=question,
                    options=options_text,
                    model_name=model_name,
                )
                ai_explanation = convert_to_traditional(ai_explanation)
            else:
                ai_explanation = convert_to_traditional(question.explanation)
        else:
            ai_explanation = None

        if request.user.is_authenticated:
            QuestionRecord.objects.create(
                user=request.user,
                question=question,
                is_correct=result,
                selected_answer=(
                    fill_input if question.is_fill_in else "".join(selected_answer)
                ),
                used_time=used_time,
                ai_explanation=ai_explanation if not result else None,
                source="mock",
            )

    else:
        question = random.choice(questions)
        if not question.is_fill_in:
            shuffled_choices, new_answer = shuffle_choice_values(question)
            request.session["shuffled_choices"] = shuffled_choices
            request.session["correct_answer"] = new_answer
            question.answer = new_answer
        else:
            shuffled_choices = None
            request.session["shuffled_choices"] = None
            request.session["correct_answer"] = question.fill_answer

    # 下拉資料
    categories = Question.objects.values_list("category", flat=True).distinct()
    chapter_list = (
        Question.objects.filter(category=category)
        .values_list("chapter", flat=True)
        .distinct()
        if category
        else []
    )
    number_list = []
    current_chapter = chapter or getattr(question, "chapter", None)
    if category and current_chapter:
        raw_numbers = (
            Question.objects.filter(category=category, chapter=current_chapter)
            .values_list("number", flat=True)
            .distinct()
        )
        number_list = sorted(raw_numbers, key=sort_key)

    correct_answer = request.session.get("correct_answer")
    correct_answer_list = list(correct_answer) if correct_answer else []
    correct_choices_list = [
        getattr(question, f"choice_{letter.lower()}", "")
        for letter in correct_answer_list
        if getattr(question, f"choice_{letter.lower()}", "").strip().upper() != "X"
    ]

    is_favorited = QuestionBookmark.objects.filter(
        user=request.user, question=question, bookmark_type="favorite"
    ).exists()

    is_flagged = QuestionBookmark.objects.filter(
        user=request.user, question=question, bookmark_type="flag"
    ).exists()

    return render(
        request,
        "quiz/mock_exam.html",
        {
            "question": question,
            "selected_answer": selected_answer,
            "fill_input": fill_input,
            "result": result,
            "correct_answer": correct_answer,
            "correct_answer_list": correct_answer_list,
            "correct_choices_list": correct_choices_list,
            "explanation": explanation,
            "ai_explanation": ai_explanation,
            "category": category,
            "chapter": chapter,
            "number": number,
            "chapter_list": chapter_list,
            "number_list": number_list,
            "categories": categories,
            "current_category": category,
            "category_total": category_total,
            "shuffled_choices": request.session.get("shuffled_choices"),
            "ollama_model": model_name,
            "is_favorited": is_favorited,
            "is_flagged": is_flagged,
            "used_time": used_time,
            "show_category_filter": True,
            "keyword_filter": True,
        },
    )


@login_required
def reset_chapter_practice(request):
    request.session.pop("current_index", None)
    return redirect("chapter_practice")


def get_chapters_by_category(request):
    category = request.GET.get("category")
    chapters = list(
        Question.objects.filter(category=category)
        .values_list("chapter", flat=True)
        .distinct()
    )
    return JsonResponse({"chapters": chapters})


def get_numbers_by_chapter(request):
    category = request.GET.get("category")
    chapter = request.GET.get("chapter")
    numbers = list(
        Question.objects.filter(category=category, chapter=chapter)
        .values_list("number", flat=True)
        .distinct()
    )
    return JsonResponse({"numbers": numbers})


@login_required
def question_detail(request, pk):
    question = get_object_or_404(Question, pk=pk)
    return render(request, "quiz/question_detail.html", {"question": question})


from django.db.models import Q
from django.core.paginator import Paginator
from ..models import Question


@login_required
def question_list(request):
    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()

    questions = Question.objects.all()

    if category:
        questions = questions.filter(category=category)

    if search:
        questions = questions.filter(
            Q(question_text__icontains=search)
            | Q(choice_a__icontains=search)
            | Q(choice_b__icontains=search)
            | Q(choice_c__icontains=search)
            | Q(choice_d__icontains=search)
            | Q(explanation__icontains=search)
            | Q(category__icontains=search)
        )

    questions = questions.order_by("chapter", "number_order")

    paginator = Paginator(questions, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 所有可選科目（用於下拉選單）
    categories = Question.objects.values_list("category", flat=True).distinct()

    return render(
        request,
        "quiz/question_list.html",
        {
            "questions": page_obj,
            "search": search,
            "current_category": category,
            "categories": categories,
            "show_category_filter": True,
            "keyword_filter": True,
        },
    )
