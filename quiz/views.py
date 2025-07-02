import random
import requests
import json
from django.shortcuts import render, redirect
from .models import Question
from django.http import JsonResponse


def get_numbers_by_chapter(request):
    chapter = request.GET.get("chapter")
    numbers = list(
        Question.objects.filter(chapter=chapter)
        .values_list("number", flat=True)
        .distinct()
    )

    def sort_key(val):
        try:
            cleaned = val.replace(" ", "")
            if "-" in cleaned:
                parts = cleaned.split("-")
                return (int(parts[0]), int(parts[1]))
            else:
                return (int(cleaned), 0)
        except Exception:
            return (float("inf"), float("inf"))

    sorted_numbers = sorted(numbers, key=sort_key)
    return JsonResponse({"numbers": sorted_numbers})


# 顯示全部題目列表
def question_list(request):
    questions = Question.objects.all()
    return render(request, "quiz/question_list.html", {"questions": questions})


# 題庫分類選擇頁
def select_category(request):
    categories = Question.objects.values_list("category", flat=True).distinct()
    return render(request, "quiz/select_category.html", {"categories": categories})


# 呼叫本地 Ollama 模型獲得補充說明
def get_ai_feedback_ollama(question_text, user_ans, correct_ans):
    prompt = f"""
這是一題選擇題，請幫我解釋這題的答案為什麼不是「{user_ans}」，而是「{correct_ans}」，內容如下：

{question_text}
"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5-coder:3b", "prompt": prompt, "stream": False},
            timeout=90,  # 設定超時時間為 90 秒
        )
        data = response.json()
        return data.get("response", "⚠️ AI 沒有回應。")
    except Exception as e:
        return f"⚠️ AI 請求錯誤：{e}"


# 模擬測驗（支援分類 + 複選 + 順序 + AI 說明）
def mock_exam(request):
    category = request.GET.get("chapter")
    number = request.GET.get("number")
    result = None
    correct_answer = None
    explanation = None
    selected_answer = []
    ai_explanation = None
    fill_input = ""

    questions = Question.objects.all()
    if category:
        questions = questions.filter(chapter=category)
    if number:
        questions = questions.filter(number=number)

    if not questions.exists():
        chapter_list = Question.objects.values_list("chapter", flat=True).distinct()
        number_list = (
            Question.objects.filter(chapter=category)
            .values_list("number", flat=True)
            .distinct()
            if category
            else []
        )
        return render(
            request,
            "quiz/mock_exam.html",
            {
                "no_question": True,
                "chapter_list": chapter_list,
                "number_list": number_list,
                "category": category,
                "number": number,
            },
        )

    if request.method == "POST" and ("next" in request.POST or "skip" in request.POST):
        return redirect("mock_exam")

    if request.method == "POST":
        question_id = request.POST.get("question_id")
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return render(request, "quiz/mock_exam.html", {"no_question": True})

        selected_answer = request.POST.getlist("selected_answer")
        fill_input = request.POST.get("fill_answer", "").strip()

        correct_answer = question.answer.upper()
        explanation = question.explanation
        require_order = question.require_order

        if question.is_fill_in:
            result = fill_input == question.fill_answer.strip()
        else:
            user_ans = "".join(selected_answer).upper()
            if require_order:
                result = user_ans == correct_answer
            else:
                result = sorted(user_ans) == sorted(correct_answer)

        if not result:
            try:
                ai_explanation = get_ai_feedback_ollama(
                    question.question_text, "".join(selected_answer), correct_answer
                )
            except Exception as e:
                ai_explanation = f"⚠️ AI 補充失敗：{e}"
    else:
        question = random.choice(questions)

    # ⏬ 準備選單項目
    chapter_list = Question.objects.values_list("chapter", flat=True).distinct()
    current_chapter = category or getattr(question, "chapter", None)

    if current_chapter:
        raw_numbers = (
            Question.objects.filter(chapter=current_chapter)
            .values_list("number", flat=True)
            .distinct()
        )

        def sort_key(val):
            try:
                cleaned = val.replace(" ", "")  # 去除空格：'10 - 2' → '10-2'
                if "-" in cleaned:
                    parts = cleaned.split("-")
                    return (int(parts[0]), int(parts[1]))
                else:
                    return (int(cleaned), 0)
            except Exception:
                return (float("inf"), float("inf"))

        number_list = sorted(raw_numbers, key=sort_key)
    else:
        number_list = []

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
            "number": number,
            "ai_explanation": ai_explanation,
            "chapter_list": chapter_list,
            "number_list": number_list,
            "fill_input": fill_input,
        },
    )
