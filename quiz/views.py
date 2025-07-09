import random
import requests
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import localtime
from .models import Question, QuestionRecord
from django.urls import reverse
from urllib.parse import urlencode
from django.http import JsonResponse

# ========== 工具函式 ==========


def check_answer(question, selected_answer, fill_input):
    correct_answer = question.answer.upper()
    if question.is_fill_in:
        return fill_input.strip() == question.fill_answer.strip()
    else:
        user_ans = "".join(selected_answer).strip().upper()
        return (
            user_ans == correct_answer
            if question.require_order
            else sorted(user_ans) == sorted(correct_answer)
        )


def sort_key(val):
    try:
        cleaned = val.replace(" ", "")
        if "-" in cleaned:
            parts = cleaned.split("-")
            return (int(parts[0]), int(parts[1]))
        return (int(cleaned), 0)
    except Exception:
        return (float("inf"), float("inf"))


def get_chapters_by_category(request):
    category = request.GET.get("category")
    chapters = list(
        Question.objects.filter(category=category)
        .values_list("chapter", flat=True)
        .distinct()
    )
    return JsonResponse({"chapters": chapters})


# def get_ai_feedback_ollama(question_text, user_ans, correct_ans, category=None):
#     category_line = f"這題的範圍是「{category}」\n" if category else ""

#     prompt = f"""
#     這是一題選擇題，請幫我解釋這題的答案為什麼不是「{user_ans}」，而是「{correct_ans}」。
#     {category_line}內容如下：

#     {question_text}
#     """
#     try:
#         response = requests.post(
#             "http://localhost:11434/api/generate",
#             json={"model": "qwen2.5-coder:3b", "prompt": prompt, "stream": False},
#             timeout=90,
#         )
#         data = response.json()
#         return data.get("response", "⚠️ AI 沒有回應。")
#     except Exception as e:
#         return f"⚠️ AI 請求錯誤：{e}"


def get_ai_feedback_ollama(
    question_text, user_ans, correct_ans, question=None, category=None, options=""
):
    """
    :param question_text: 題目內容（純題幹）
    :param user_ans: 使用者作答，例如 "B"、"AC"
    :param correct_ans: 正確答案，例如 "C"
    :param question: Question 物件（選填，用來提取選項）
    :param category: 題目類別（例如 "Python"、"AI"）
    """
    # 👉 類別描述行
    category_line = (
        f"這題的範圍是「{category or getattr(question, 'category', '')}」\n"
        if (category or question)
        else ""
    )

    # 👉 整理選項文字
    choices_text = ""
    if question:
        for letter in "ABCDEFGH":
            choice_text = getattr(question, f"choice_{letter.lower()}", "").strip()
            if choice_text and choice_text.upper() != "X":
                choices_text += f"{letter}. {choice_text}\n"

    # 👉 組合 prompt 給 AI
    prompt = f"""這是一題選擇題，請幫我解釋為什麼答案不是「{user_ans}」，而是「{correct_ans}」。
{category_line}
題目如下：
{question_text}

選項如下：
{options}
""".strip()

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5-coder:3b", "prompt": prompt, "stream": False},
            timeout=90,
        )
        data = response.json()
        return data.get("response", "⚠️ AI 沒有回應。")
    except Exception as e:
        return f"⚠️ AI 請求錯誤：{e}"


# ========== 註冊視圖 ==========


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})


# ========== 題目視圖 ==========


@login_required
def question_detail(request, pk):
    question = get_object_or_404(Question, pk=pk)
    return render(request, "quiz/question_detail.html", {"question": question})


def question_list(request):
    questions = Question.objects.all()
    return render(request, "quiz/question_list.html", {"questions": questions})


def select_category(request):
    categories = Question.objects.values_list("category", flat=True).distinct()
    return render(request, "quiz/select_category.html", {"categories": categories})


def get_numbers_by_chapter(request):
    category = request.GET.get("category")
    chapter = request.GET.get("chapter")
    numbers = list(
        Question.objects.filter(category=category, chapter=chapter)
        .values_list("number", flat=True)
        .distinct()
    )
    return JsonResponse({"numbers": numbers})


# ========== 練習與模擬測驗 ==========


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

    result = None
    correct_answer = None
    explanation = None
    selected_answer = []
    ai_explanation = None
    fill_input = ""

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
    # 保留 query string 參數
    query_params = urlencode(
        {
            "category": category or "",
            "chapter": chapter or "",
            "number": number or "",
        }
    )
    redirect_url = f"{reverse('mock_exam')}?{query_params}"

    # 題目過濾條件
    questions = Question.objects.all()
    if category:
        questions = questions.filter(category=category)
    if chapter:
        questions = questions.filter(chapter=chapter)
    if number:
        questions = questions.filter(number=number)

    # 沒有題目時返回錯誤畫面
    if not questions.exists():
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
        return render(
            request,
            "quiz/mock_exam.html",
            {
                "no_question": True,
                "chapter_list": chapter_list,
                "number_list": number_list,
                "category": category,
                "chapter": chapter,
                "number": number,
                "categories": categories,
                "current_category": category,
            },
        )

    # 點了「下一題或跳過」
    if request.method == "POST" and ("next" in request.POST or "skip" in request.POST):
        return redirect(redirect_url)

    # 有送出答案
    if request.method == "POST":
        question_id = request.POST.get("question_id")
        question = get_object_or_404(Question, id=question_id)

        selected_answer = request.POST.getlist("selected_answer")
        fill_input = request.POST.get("fill_answer", "").strip()
        used_time = int(request.POST.get("used_time", 0))

        correct_answer = question.answer.upper()
        explanation = question.explanation
        result = check_answer(question, selected_answer, fill_input)

        if not result:
            if question.image:
                ai_explanation = question.explanation
            else:
                # ✅ 組合 options_text，避免未定義錯誤
                options_text = ""
                for letter in "ABCDEFGH":
                    choice = getattr(question, f"choice_{letter.lower()}", "").strip()
                    if choice and choice.upper() != "X":
                        options_text += f"{letter}. {choice}\n"

                ai_explanation = get_ai_feedback_ollama(
                    question_text=question.question_text,
                    user_ans=(
                        fill_input if question.is_fill_in else "".join(selected_answer)
                    ),
                    correct_ans=correct_answer,
                    question=question.category,
                    options=options_text,  # ✅ 傳組合好的選項文字
                )

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

    # 準備下拉資料
    categories = Question.objects.values_list("category", flat=True).distinct()

    # 類別對應章節
    chapter_list = (
        Question.objects.filter(category=category)
        .values_list("chapter", flat=True)
        .distinct()
        if category
        else []
    )

    # ⬇️ 計算目前章節（優先用 GET 傳入，其次從題目抓）
    current_chapter = chapter or getattr(question, "chapter", None)

    # 題號下拉選單：需同時指定 category + chapter，才會有對應題號
    number_list = []
    if category and current_chapter:
        raw_numbers = (
            Question.objects.filter(category=category, chapter=current_chapter)
            .values_list("number", flat=True)
            .distinct()
        )
        number_list = sorted(raw_numbers, key=sort_key)

    # ⬇️ 取得該類別總題數
    category_total = (
        Question.objects.filter(category=category).count() if category else 0
    )

    return render(
        request,
        "quiz/mock_exam.html",
        {
            "question": question,
            "selected_answer": selected_answer,
            "result": result,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "category": category,
            "chapter": chapter,
            "number": number,
            "ai_explanation": ai_explanation,
            "chapter_list": chapter_list,
            "number_list": number_list,
            "fill_input": fill_input,
            "categories": categories,
            "current_category": category,
            "category_total": category_total,
        },
    )


@login_required
def reset_chapter_practice(request):
    request.session.pop("question_ids", None)
    request.session.pop("current_index", None)
    return redirect("chapter_practice")


@login_required
def chapter_practice(request):
    category = request.GET.get("category")
    chapter = request.GET.get("chapter")
    number = request.GET.get("number")
    if category == "None":
        category = None
    if chapter == "None":
        chapter = None
    if number == "None":
        number = None

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
                "question": None,
            },
        )

    current_index = request.session.get("current_index", 0)
    if current_index >= total:
        current_index = 0

    selected_answer = []
    fill_input = ""
    result = None
    correct_answer = None
    ai_explanation = None
    question = questions[current_index]

    # 準備 query string 參數
    query_params = urlencode(
        {
            "category": category or "",
            "chapter": chapter or "",
            "number": number or "",
        }
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

        # ✅ 作答處理
        selected_answer = [a.upper() for a in request.POST.getlist("selected_answer")]
        fill_input = request.POST.get("fill_answer", "").strip()
        used_time = request.POST.get("used_time", 0)

        result = check_answer(question, selected_answer, fill_input)
        correct_answer = question.answer

        if not result:
            if question.image:
                ai_explanation = question.explanation
            else:
                options_text = ""
                for letter in "ABCDEFGH":
                    choice = getattr(question, f"choice_{letter.lower()}", None)
                    if choice and choice != "X":
                        options_text += f"{letter}. {choice}\n"

                ai_explanation = get_ai_feedback_ollama(
                    question_text=question.question_text,
                    user_ans=(
                        fill_input if question.is_fill_in else "".join(selected_answer)
                    ),
                    correct_ans=correct_answer,
                    question=question.category,
                    options=options_text,  # ✅ 加這行
                )

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

    # 傳遞下拉選單資料
    chapter_list = (
        Question.objects.filter(category=category)
        .values_list("chapter", flat=True)
        .distinct()
    )
    if category and chapter:
        number_list = (
            Question.objects.filter(category=category, chapter=chapter)
            .values_list("number", flat=True)
            .distinct()
        )
    else:
        number_list = []

    categories = Question.objects.values_list("category", flat=True).distinct()

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
            "current_index": current_index + 1,
            "chapter_list": chapter_list,
            "number_list": number_list,
            "categories": categories,
            "current_category": category,
            "category": category,
            "chapter": chapter,
            "number": number,
            "category_total": category_total,
        },
    )


# ========== 歷史與複習 ==========


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

    questions = [record.question for record in wrong_records]
    categories = Question.objects.values_list("category", flat=True).distinct()

    return render(
        request,
        "quiz/review_wrong_questions.html",
        {
            "questions": questions,
            "records": wrong_records,
            "categories": categories,
            "current_category": category,
        },
    )
