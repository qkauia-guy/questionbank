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
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from urllib.parse import urlencode, urlparse, parse_qs
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt


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


def shuffle_choice_values(question):
    import random

    answer_letters = question.answer.strip().upper()
    if not answer_letters or not answer_letters[0].isalpha():
        raise ValueError(f"❌ 無效的答案格式：{question.answer}")

    first_letter = answer_letters[0]
    correct_content = getattr(question, f"choice_{first_letter.lower()}", None)

    if not correct_content:
        raise AttributeError(f"❌ 找不到欄位：choice_{first_letter.lower()}")

    # 建立選項對應表
    choices = {
        "A": question.choice_a,
        "B": question.choice_b,
        "C": question.choice_c,
        "D": question.choice_d,
    }

    # 過濾掉為空或為 "X" 的選項
    valid_choices = {k: v for k, v in choices.items() if v and v.strip() != "X"}

    items = list(valid_choices.items())
    random.shuffle(items)

    # 重新編號，回傳混洗後的新選項與新答案
    shuffled = {}
    new_answer = ""
    for idx, (old_letter, content) in enumerate(items):
        new_letter = chr(ord("A") + idx)
        shuffled[new_letter] = content
        if old_letter == first_letter:
            new_answer = new_letter

    return shuffled, new_answer


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
    question_text,
    user_ans,
    correct_ans,
    question=None,
    category=None,
    options="",
    model_name="qwen2.5-coder:3b",
):
    """
    回傳 AI 解釋說明文字，包含類別強化提示
    """

    # 防呆處理
    user_ans = user_ans or "（未提供）"
    correct_ans = correct_ans or "（未提供）"

    # 類別：優先使用 category，否則從 question 擷取
    category_text = category or (getattr(question, "category", "") or "").strip()
    if not category_text:
        print(
            f"DEBUG: category = {category}, question.category = {getattr(question, 'category', None)}"
        )

    # 自動擷取選項（若未手動傳入）
    if not options and question:
        for letter in "ABCDEFGH":
            choice_text = getattr(question, f"choice_{letter.lower()}", "").strip()
            if choice_text and choice_text.upper() != "X":
                options += f"{letter}. {choice_text}\n"

    # 強化版 prompt，讓模型一定讀到類別
    prompt = f"""請使用繁體中文回答。
這是一題選擇題，請幫我解釋為什麼答案不是「{user_ans}」，而是「{correct_ans}」。

請特別根據「題目範圍」思考解釋。
科目範圍：「{category_text or '未提供'}」

題目內容如下：
{question_text}

選項如下：
{options}
""".strip()

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
            },
            timeout=90,
        )
        data = response.json()
        return f"🤖 本次回答由「{model_name}」模型生成：\n\n{data.get('response', '⚠️ AI 沒有回應。')}"
    except Exception as e:
        return f"⚠️ AI 請求錯誤：{e}"


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

    ollama_enabled = request.session.get("ollama_enabled", True)
    result = None
    correct_answer = None
    explanation = None
    selected_answer = []
    ai_explanation = None
    fill_input = ""
    model_name = request.session.get("ollama_model", "qwen2.5-coder:7b")

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

        # ✅ 使用 session 中記錄的選項與正解
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
            # ❗ 圖片題：只顯示手動解釋，不呼叫 AI
            if question.image:
                ai_explanation = None  # 不呼叫 AI
            elif ollama_enabled:
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
                    question=question.category,
                    options=options_text,
                    model_name=model_name,
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
        if not question.is_fill_in:
            shuffled_choices, new_answer = shuffle_choice_values(question)
            request.session["shuffled_choices"] = shuffled_choices
            request.session["correct_answer"] = new_answer
            question.answer = new_answer
        else:
            shuffled_choices = None
            request.session["shuffled_choices"] = None
            request.session["correct_answer"] = question.fill_answer

    # 👇 下拉選單資料處理
    categories = Question.objects.values_list("category", flat=True).distinct()
    chapter_list = (
        Question.objects.filter(category=category)
        .values_list("chapter", flat=True)
        .distinct()
        if category
        else []
    )
    current_chapter = chapter or getattr(question, "chapter", None)
    number_list = []
    if category and current_chapter:
        raw_numbers = (
            Question.objects.filter(category=category, chapter=current_chapter)
            .values_list("number", flat=True)
            .distinct()
        )
        number_list = sorted(raw_numbers, key=sort_key)

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
            "shuffled_choices": request.session.get("shuffled_choices"),
            "ollama_model": model_name,
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

    # 題庫查詢
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

    # 若帶有 ?next=1，則進入下一題
    if request.method == "GET" and request.GET.get("next") == "1":
        request.session["current_index"] = request.session.get("current_index", 0) + 1
        return redirect(
            f"{reverse('chapter_practice')}?{urlencode({'category': category or '', 'chapter': chapter or '', 'number': number or ''})}"
        )

    # 目前第幾題
    current_index = request.session.get("current_index", 0)
    if current_index >= total:
        current_index = 0

    selected_answer = []
    fill_input = ""
    result = None
    correct_answer = None
    ai_explanation = None
    question = questions[current_index]

    # query 參數備用
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

        # ✅ AI 補充說明（僅答錯才顯示）
        if not result:
            ollama_enabled = request.session.get("ollama_enabled", True)
            model_name = request.session.get("ollama_model", "qwen2.5-coder:7b")

            if not question.image and ollama_enabled:
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
                    question=question.category,
                    options=options_text,
                    model_name=model_name,
                )

        # ✅ 建立答題紀錄
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
            "current_index": current_index,
            "chapter_list": chapter_list,
            "number_list": number_list,
            "categories": categories,
            "current_category": category,
            "category": category,
            "chapter": chapter,
            "number": number,
            "category_total": category_total,
            "ollama_model": request.session.get("ollama_model", "qwen2.5-coder:7b"),
            "options": generate_options_text(question),
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


@require_GET
def toggle_ollama(request):
    enable = request.GET.get("enable") == "true"
    request.session["ollama_enabled"] = enable
    return JsonResponse({"status": "ok", "enabled": enable})


def clear_ollama_notice(request):
    request.session.pop("show_ollama_notice", None)
    return JsonResponse({"cleared": True})


def set_ollama_model(request):
    model = request.GET.get("model")
    if model:
        request.session["ollama_model"] = model
    return JsonResponse({"status": "ok", "model": model})


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


def is_ollama_running():
    try:
        response = requests.get("http://localhost:11434")
        return response.status_code == 200
    except:
        return False


# def is_ollama_running():
#     try:
#         response = requests.get("http://192.168.0.101:11434/api/tags", timeout=3)
#         return response.status_code == 200
#     except Exception:
#         return False


@login_required
@require_POST
def save_ai_explanation(request, pk):
    question = get_object_or_404(Question, pk=pk)
    new_explanation = request.POST.get("explanation")

    if new_explanation:
        question.explanation = new_explanation
        question.save()
        messages.success(request, "✅ 解釋已成功寫入")
    else:
        messages.warning(request, "⚠️ 沒有收到解釋內容")

    # ⏩ 回到來源頁面並觸發下一題
    referer = request.META.get("HTTP_REFERER", "/")
    parsed = urlparse(referer)
    base_url = parsed.path
    query = parse_qs(parsed.query)
    query["next"] = ["1"]

    return redirect(f"{base_url}?{urlencode(query, doseq=True)}")


@csrf_exempt
@login_required
@require_POST
def ask_ai_followup(request):
    question_text = request.POST.get("question_text", "")
    category = request.POST.get("category", "")
    options = request.POST.get("options", "")
    followup = request.POST.get("followup", "")
    chat_history = request.POST.get("chat_history", "")

    prompt = f"""以下是使用者與 AI 的過往對話：

{chat_history.strip()}

---

原始題目：
{question_text}

範圍：「{category}」
選項：
{options}

使用者的新問題：
{followup}

請用繁體中文回答。
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen2.5-coder:3b", "prompt": prompt, "stream": False},
        timeout=90,
    )
    data = response.json()
    reply = data.get("response", "⚠️ AI 沒有回應。")

    return render(request, "quiz/_followup_result.html", {"reply": reply})


def generate_options_text(question):
    """
    根據題目自動產生選項文字（不含 "X" 的選項），給 AI 用的提示格式。
    """
    options_text = ""
    for letter in "ABCDEFGH":
        choice = getattr(question, f"choice_{letter.lower()}", "").strip()
        if choice and choice.upper() != "X":
            options_text += f"{letter}. {choice}\n"
    return options_text
